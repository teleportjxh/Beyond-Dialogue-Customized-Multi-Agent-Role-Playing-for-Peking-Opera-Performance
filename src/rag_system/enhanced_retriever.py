"""
增强版语义检索器
集成 Query 改写 + Hybrid 混合检索 + CrossEncoder Rerank
"""

import time
from typing import List, Dict, Any, Optional

from .semantic_retriever import SemanticRetriever
from .vector_store import VectorStoreManager
from .query_rewriter import rewrite_query
from .hybrid_retriever import HybridRetriever, BM25Retriever
from .reranker import CrossEncoderReranker, RetrieveAndRerank


class EnhancedRetriever:
    """
    增强版检索器
    Pipeline: Query改写 → Hybrid检索(Dense+BM25) → CrossEncoder Rerank
    """

    def __init__(
        self,
        vector_store: VectorStoreManager,
        base_retriever: SemanticRetriever,
        enable_query_rewrite: bool = True,
        enable_hybrid: bool = True,
        enable_rerank: bool = True,
        dense_weight: float = 0.5,
        retrieve_top_n: int = 50,
        rerank_top_k: int = 5,
    ):
        self.vector_store = vector_store
        self.base_retriever = base_retriever
        self.enable_query_rewrite = enable_query_rewrite
        self.enable_hybrid = enable_hybrid
        self.enable_rerank = enable_rerank

        # 初始化 BM25
        self.bm25 = BM25Retriever()
        self._bm25_built = False

        # 初始化 Hybrid Retriever
        self.hybrid = HybridRetriever(
            dense_retriever=self._dense_search,
            alpha=dense_weight,
            fusion_method="rrf"
        )

        # 初始化 Reranker
        self.reranker = CrossEncoderReranker(use_lightweight=True)
        self.retrieve_top_n = retrieve_top_n
        self.rerank_top_k = rerank_top_k

    def build_bm25_index(self):
        """从 vector_store 的文档构建 BM25 索引"""
        if self.vector_store.documents:
            docs_for_bm25 = []
            for i, doc in enumerate(self.vector_store.documents):
                doc_copy = doc.copy()
                if "id" not in doc_copy:
                    doc_copy["id"] = f"doc_{i}"
                docs_for_bm25.append(doc_copy)

            self.bm25.build_index(docs_for_bm25)
            self.hybrid.build_bm25_index(docs_for_bm25)
            self._bm25_built = True
            print(f"✅ BM25 索引构建完成，共 {len(docs_for_bm25)} 个文档")

    def _dense_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Dense 检索封装"""
        results = self.base_retriever.retrieve(query=query, top_k=top_k)
        # 确保每个结果有 id 和 score
        for i, r in enumerate(results):
            if "id" not in r:
                r["id"] = f"doc_{i}"
            if "score" not in r:
                r["score"] = r.get("similarity_score", 0)
        return results

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        增强检索 Pipeline

        Args:
            query: 查询文本
            top_k: 最终返回数量

        Returns:
            检索结果列表
        """
        # Step 1: Query 改写
        queries = [query]
        if self.enable_query_rewrite:
            queries = rewrite_query(query)

        # Step 2: 多查询检索
        all_candidates = {}  # doc_id -> doc (去重)
        retrieve_k = self.retrieve_top_n if self.enable_rerank else top_k

        for q in queries:
            if self.enable_hybrid and self._bm25_built:
                # Hybrid 检索
                results = self.hybrid.search(q, top_k=retrieve_k)
            else:
                # 仅 Dense 检索
                results = self._dense_search(q, top_k=retrieve_k)

            for r in results:
                doc_id = r.get("id", "")
                if doc_id not in all_candidates:
                    all_candidates[doc_id] = r
                else:
                    # 合并分数（取最高）
                    existing = all_candidates[doc_id]
                    for key in ["score", "similarity_score", "hybrid_score", "bm25_score"]:
                        if key in r:
                            existing[key] = max(existing.get(key, 0), r.get(key, 0))

        candidates = list(all_candidates.values())

        # Step 3: Rerank
        if self.enable_rerank and len(candidates) > top_k:
            results = self.reranker.rerank(query, candidates, top_k=top_k)
        else:
            # 按现有分数排序
            candidates.sort(
                key=lambda x: x.get("hybrid_score", x.get("similarity_score", x.get("score", 0))),
                reverse=True
            )
            results = candidates[:top_k]

        return results

    def search_with_details(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        带详细信息的增强检索

        Returns:
            包含检索结果和过程信息的字典
        """
        start_time = time.time()

        # Query 改写
        rewritten_queries = rewrite_query(query) if self.enable_query_rewrite else [query]

        # 检索
        results = self.search(query, top_k=top_k)

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            "query": query,
            "rewritten_queries": rewritten_queries,
            "results": results,
            "total_results": len(results),
            "retrieval_time_ms": elapsed_ms,
            "pipeline": {
                "query_rewrite": self.enable_query_rewrite,
                "hybrid_retrieval": self.enable_hybrid,
                "rerank": self.enable_rerank,
            }
        }


def create_baseline_retriever_fn(base_retriever: SemanticRetriever):
    """创建基线检索函数（用于评估）"""
    def retriever_fn(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        results = base_retriever.retrieve(query=query, top_k=top_k)
        for i, r in enumerate(results):
            if "id" not in r:
                r["id"] = f"doc_{i}"
        return results
    return retriever_fn


def create_enhanced_retriever_fn(enhanced: EnhancedRetriever):
    """创建增强检索函数（用于评估）"""
    def retriever_fn(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        return enhanced.search(query, top_k=top_k)
    return retriever_fn
