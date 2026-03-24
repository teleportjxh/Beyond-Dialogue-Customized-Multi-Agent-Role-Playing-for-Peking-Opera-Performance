"""
Hybrid 混合检索模块
- Dense Embedding (FAISS) + Sparse BM25 (lexical)
- 解决词义不匹配、OOV、数字专有名词
- 提升：全量召回、冷启动
"""

import math
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter


class BM25Retriever:
    """
    BM25 稀疏检索器
    用于处理精确匹配、专有名词、OOV 等 dense embedding 难以处理的场景
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_freqs: Dict[str, int] = {}  # 词 -> 包含该词的文档数
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_term_freqs: List[Dict[str, int]] = []  # 每个文档的词频
        self.total_docs: int = 0
        self._built = False

    def _tokenize(self, text: str) -> List[str]:
        """
        简单的中文分词（基于字符和常见词汇）
        对于京剧领域，保留专有名词完整性
        """
        # 保留的专有名词列表
        proper_nouns = [
            "孙悟空", "猪八戒", "沙僧", "唐三藏", "唐僧",
            "诸葛亮", "关羽", "张飞", "刘备", "曹操", "周瑜",
            "赵匡胤", "赵云", "黄忠", "马谡", "王朗", "司马懿",
            "铁扇公主", "牛魔王", "金钱豹", "蜘蛛精",
            "齐天大圣", "美猴王", "弼马温",
            "空城计", "定军山", "芭蕉扇", "安天会", "三顾茅庐",
            "失街亭", "斩马谡", "群英会", "骂王朗", "七星灯",
            "流沙河", "盘丝洞", "高老庄", "莲花塘", "无底洞",
            "大闹天宫", "西天取经", "三借芭蕉扇",
            "西皮", "二黄", "花脸", "老生", "武生", "青衣", "花旦",
            "靠旗", "帅盔", "八卦衣", "鹅毛扇", "金箍棒",
            "脸谱", "唱腔", "念白", "武打", "身段",
        ]

        tokens = []
        text_lower = text.lower()

        # 先提取专有名词
        remaining = text
        positions = []  # (start, end, token)

        for noun in sorted(proper_nouns, key=len, reverse=True):
            start = 0
            while True:
                idx = remaining.find(noun, start)
                if idx == -1:
                    break
                positions.append((idx, idx + len(noun), noun))
                start = idx + len(noun)

        # 按位置排序，去重叠
        positions.sort(key=lambda x: x[0])
        merged = []
        for pos in positions:
            if not merged or pos[0] >= merged[-1][1]:
                merged.append(pos)

        # 提取专有名词和剩余文本的字符
        last_end = 0
        for start, end, token in merged:
            # 处理专有名词之前的文本（按字切分）
            if start > last_end:
                segment = remaining[last_end:start]
                tokens.extend(self._char_tokenize(segment))
            tokens.append(token)
            last_end = end

        # 处理最后一段
        if last_end < len(remaining):
            tokens.extend(self._char_tokenize(remaining[last_end:]))

        return [t for t in tokens if t.strip()]

    def _char_tokenize(self, text: str) -> List[str]:
        """字符级分词 + bigram"""
        tokens = []
        # 提取中文字符
        chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(chars)

        # 添加 bigram
        for i in range(len(chars) - 1):
            tokens.append(chars[i] + chars[i + 1])

        # 提取英文单词和数字
        words = re.findall(r'[a-zA-Z]+|[0-9]+', text)
        tokens.extend(words)

        return tokens

    def build_index(self, documents: List[Dict[str, Any]]):
        """构建 BM25 索引"""
        self.documents = documents
        self.total_docs = len(documents)
        self.doc_term_freqs = []
        self.doc_lengths = []
        self.doc_freqs = {}

        for doc in documents:
            text = doc.get("text", "") + " " + doc.get("metadata", {}).get("title", "")
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))

            # 计算词频
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            # 更新文档频率
            for term in set(tokens):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avg_doc_length = sum(self.doc_lengths) / max(self.total_docs, 1)
        self._built = True

    def _compute_bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """计算单个文档的 BM25 分数"""
        score = 0.0
        doc_tf = self.doc_term_freqs[doc_idx]
        doc_len = self.doc_lengths[doc_idx]

        for term in query_tokens:
            if term not in doc_tf:
                continue

            tf = doc_tf[term]
            df = self.doc_freqs.get(term, 0)

            # IDF
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)

            # TF normalization
            tf_norm = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
            )

            score += idf * tf_norm

        return score

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """BM25 检索"""
        if not self._built:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for i in range(self.total_docs):
            score = self._compute_bm25_score(query_tokens, i)
            if score > 0:
                scores.append((i, score))

        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            doc = self.documents[idx].copy()
            doc["bm25_score"] = score
            results.append(doc)

        return results


class HybridRetriever:
    """
    混合检索器：融合 Dense (FAISS) + Sparse (BM25) 结果
    使用 Reciprocal Rank Fusion (RRF) 或加权融合
    """

    def __init__(
        self,
        dense_retriever,  # 原始的 FAISS 检索器
        alpha: float = 0.5,  # dense 权重
        rrf_k: int = 60,  # RRF 参数
        fusion_method: str = "rrf"  # "rrf" 或 "weighted"
    ):
        self.dense_retriever = dense_retriever
        self.bm25 = BM25Retriever()
        self.alpha = alpha
        self.rrf_k = rrf_k
        self.fusion_method = fusion_method
        self._bm25_built = False

    def build_bm25_index(self, documents: List[Dict[str, Any]]):
        """构建 BM25 索引"""
        self.bm25.build_index(documents)
        self._bm25_built = True

    def _rrf_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Reciprocal Rank Fusion"""
        scores = {}  # doc_id -> rrf_score
        doc_map = {}  # doc_id -> doc

        # Dense 结果的 RRF 分数
        for rank, doc in enumerate(dense_results):
            doc_id = doc.get("id", "")
            rrf_score = self.alpha / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            doc_map[doc_id] = doc

        # Sparse 结果的 RRF 分数
        for rank, doc in enumerate(sparse_results):
            doc_id = doc.get("id", "")
            rrf_score = (1 - self.alpha) / (self.rrf_k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        # 按 RRF 分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids[:top_k]:
            doc = doc_map[doc_id].copy()
            doc["hybrid_score"] = scores[doc_id]
            doc["fusion_method"] = "rrf"
            results.append(doc)

        return results

    def _weighted_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """加权分数融合"""
        scores = {}
        doc_map = {}

        # 归一化 dense 分数
        if dense_results:
            dense_scores = [doc.get("score", 0) for doc in dense_results]
            max_dense = max(dense_scores) if dense_scores else 1
            min_dense = min(dense_scores) if dense_scores else 0
            range_dense = max_dense - min_dense if max_dense != min_dense else 1

            for doc in dense_results:
                doc_id = doc.get("id", "")
                norm_score = (doc.get("score", 0) - min_dense) / range_dense
                scores[doc_id] = self.alpha * norm_score
                doc_map[doc_id] = doc

        # 归一化 BM25 分数
        if sparse_results:
            bm25_scores = [doc.get("bm25_score", 0) for doc in sparse_results]
            max_bm25 = max(bm25_scores) if bm25_scores else 1
            min_bm25 = min(bm25_scores) if bm25_scores else 0
            range_bm25 = max_bm25 - min_bm25 if max_bm25 != min_bm25 else 1

            for doc in sparse_results:
                doc_id = doc.get("id", "")
                norm_score = (doc.get("bm25_score", 0) - min_bm25) / range_bm25
                scores[doc_id] = scores.get(doc_id, 0) + (1 - self.alpha) * norm_score
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc

        # 排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids[:top_k]:
            doc = doc_map[doc_id].copy()
            doc["hybrid_score"] = scores[doc_id]
            doc["fusion_method"] = "weighted"
            results.append(doc)

        return results

    def search(
        self,
        query: str,
        top_k: int = 10,
        dense_top_k: Optional[int] = None,
        sparse_top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 最终返回的文档数
            dense_top_k: dense 检索的候选数（默认 top_k * 3）
            sparse_top_k: sparse 检索的候选数（默认 top_k * 3）
        """
        if dense_top_k is None:
            dense_top_k = top_k * 3
        if sparse_top_k is None:
            sparse_top_k = top_k * 3

        # Dense 检索
        dense_results = self.dense_retriever(query, top_k=dense_top_k)

        # Sparse 检索
        sparse_results = []
        if self._bm25_built:
            sparse_results = self.bm25.search(query, top_k=sparse_top_k)

        # 融合
        if self.fusion_method == "rrf":
            return self._rrf_fusion(dense_results, sparse_results, top_k)
        else:
            return self._weighted_fusion(dense_results, sparse_results, top_k)
