"""
CrossEncoder 重排 (Rerank) 模块
- 检索 top-50 → rerank → top-3~8
- 强提升：Precision@k、NDCG、Context Precision、最终答案相关性
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional


class CrossEncoderReranker:
    """
    CrossEncoder 重排器
    支持三种模式：
    1. Embedding 相似度重排（使用已有的 embedding 模型）
    2. 基于 sentence-transformers CrossEncoder（需要安装）
    3. 基于多维度特征的轻量级 fallback 方案
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        use_lightweight: bool = True,
        device: str = "cpu",
        embeddings=None,
    ):
        self.model_name = model_name
        self.use_lightweight = use_lightweight
        self.device = device
        self.model = None
        self.embeddings = embeddings  # 可注入 embedding 模型

        if not use_lightweight:
            self._load_model()

    def _load_model(self):
        """加载 CrossEncoder 模型"""
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name, device=self.device)
            self.use_lightweight = False
            print(f"✅ CrossEncoder 模型加载成功: {self.model_name}")
        except ImportError:
            print("⚠️ sentence-transformers 未安装，使用轻量级重排方案")
            self.use_lightweight = True
        except Exception as e:
            print(f"⚠️ CrossEncoder 模型加载失败: {e}，使用轻量级重排方案")
            self.use_lightweight = True

    def _lightweight_score(self, query: str, document: str) -> float:
        """
        多维度特征加权评分（改进版）
        """
        score = 0.0
        if not document:
            return 0.0

        # 提取查询关键词（2-4字中文词）
        query_keywords = re.findall(r'[\u4e00-\u9fff]{2,4}', query)

        # 1. 关键词精确匹配 (权重 0.40) - 最重要的信号
        if query_keywords:
            matched = sum(1 for kw in query_keywords if kw in document)
            keyword_ratio = matched / len(query_keywords)
            score += 0.40 * keyword_ratio

        # 2. 关键词频率加权 (权重 0.20) - 出现次数越多越相关
        if query_keywords:
            freq_score = 0
            for kw in query_keywords:
                count = document.count(kw)
                if count > 0:
                    freq_score += min(count / 5.0, 1.0)  # cap at 5 occurrences
            freq_score /= len(query_keywords)
            score += 0.20 * freq_score

        # 3. 连续子串匹配 (权重 0.15) - 长匹配更有价值
        max_substr_len = 0
        for i in range(len(query)):
            for j in range(i + 2, min(i + 15, len(query) + 1)):
                substr = query[i:j]
                if substr in document:
                    max_substr_len = max(max_substr_len, len(substr))
        if len(query) > 0:
            substr_ratio = min(max_substr_len / len(query), 1.0)
            score += 0.15 * substr_ratio

        # 4. 位置权重 (权重 0.15) - 关键词出现在文档开头更重要
        if query_keywords:
            early_match = 0
            for kw in query_keywords:
                pos = document.find(kw)
                if pos != -1:
                    # 越靠前分数越高
                    position_score = max(0, 1.0 - pos / max(len(document), 1))
                    early_match += position_score
            early_ratio = early_match / len(query_keywords)
            score += 0.15 * early_ratio

        # 5. 文档长度适中奖励 (权重 0.05)
        doc_len = len(document)
        if doc_len < 100:
            len_score = doc_len / 100
        elif doc_len > 1500:
            len_score = 1500 / doc_len
        else:
            len_score = 1.0
        score += 0.05 * len_score

        # 6. 字符覆盖率 (权重 0.05)
        query_chars = set(c for c in query if '\u4e00' <= c <= '\u9fff')
        if query_chars:
            overlap = sum(1 for c in query_chars if c in document)
            score += 0.05 * (overlap / len(query_chars))

        return score

    def _embedding_score(self, query: str, documents: List[str]) -> List[float]:
        """使用 Embedding 模型计算 query-doc 相似度"""
        if self.embeddings is None:
            return [self._lightweight_score(query, doc) for doc in documents]

        try:
            q_vec = np.array(self.embeddings.embed_query(query))
            d_vecs = np.array(self.embeddings.embed_documents(documents))
            # Cosine similarity
            q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-10)
            d_norms = d_vecs / (np.linalg.norm(d_vecs, axis=1, keepdims=True) + 1e-10)
            scores = d_norms @ q_norm
            return scores.tolist()
        except Exception:
            return [self._lightweight_score(query, doc) for doc in documents]

    def _model_score(self, query: str, documents: List[str]) -> List[float]:
        """使用 CrossEncoder 模型打分"""
        if self.model is None:
            return [self._lightweight_score(query, doc) for doc in documents]
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        return scores.tolist()

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        score_key: str = "rerank_score"
    ) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排

        Args:
            query: 查询文本
            documents: 检索结果列表，每个元素需包含 "text" 字段
            top_k: 重排后返回的文档数
            score_key: 重排分数的键名

        Returns:
            重排后的文档列表
        """
        if not documents:
            return []

        doc_texts = [doc.get("text", "") for doc in documents]

        if not self.use_lightweight and self.model is not None:
            scores = self._model_score(query, doc_texts)
        else:
            # 混合打分：轻量级特征 + embedding（如果可用）
            lw_scores = [self._lightweight_score(query, text) for text in doc_texts]

            if self.embeddings is not None:
                emb_scores = self._embedding_score(query, doc_texts)
                # 加权融合：embedding 0.4 + lightweight 0.6
                scores = [0.6 * lw + 0.4 * emb for lw, emb in zip(lw_scores, emb_scores)]
            else:
                scores = lw_scores

        # 将分数附加到文档
        scored_docs = []
        for doc, score in zip(documents, scores):
            doc_copy = doc.copy()
            doc_copy[score_key] = float(score)
            scored_docs.append(doc_copy)

        # 按重排分数排序
        scored_docs.sort(key=lambda x: x[score_key], reverse=True)

        return scored_docs[:top_k]


class RetrieveAndRerank:
    """检索 + 重排 Pipeline"""

    def __init__(self, retriever_fn, reranker=None, retrieve_top_n=50, rerank_top_k=5):
        self.retriever_fn = retriever_fn
        self.reranker = reranker or CrossEncoderReranker(use_lightweight=True)
        self.retrieve_top_n = retrieve_top_n
        self.rerank_top_k = rerank_top_k

    def search(self, query: str, top_k=None) -> List[Dict[str, Any]]:
        if top_k is None:
            top_k = self.rerank_top_k
        candidates = self.retriever_fn(query, top_k=self.retrieve_top_n)
        reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        return reranked
