"""
RAG检索系统模块
用于构建基于向量数据库的语义检索系统，为多agent剧本生成提供场景增强

增强功能：
- Query 改写/扩展（同义词还原、意图补全、子问题拆解）
- Hybrid 混合检索（Dense Embedding + BM25）
- CrossEncoder 重排（Rerank）
- 评估框架（Recall@k, Precision@k, NDCG@k）
"""

from .vector_processor import VectorProcessor
from .vector_store import VectorStoreManager
from .semantic_retriever import SemanticRetriever
from .scene_enhancer import SceneEnhancer
from .main import RAGSystem

# 增强模块
from .query_rewriter import rewrite_query, expand_synonyms, generate_sub_queries
from .hybrid_retriever import BM25Retriever, HybridRetriever
from .reranker import CrossEncoderReranker, RetrieveAndRerank
from .enhanced_retriever import EnhancedRetriever
from .evaluation import (
    create_ground_truth,
    evaluate_retriever,
    print_benchmark_result,
    compare_benchmarks,
    compute_recall_at_k,
    compute_precision_at_k,
    compute_ndcg_at_k,
)

__all__ = [
    # 原有模块
    'VectorProcessor',
    'VectorStoreManager',
    'SemanticRetriever',
    'SceneEnhancer',
    'RAGSystem',
    # 增强模块
    'EnhancedRetriever',
    'rewrite_query',
    'expand_synonyms',
    'generate_sub_queries',
    'BM25Retriever',
    'HybridRetriever',
    'CrossEncoderReranker',
    'RetrieveAndRerank',
    # 评估
    'create_ground_truth',
    'evaluate_retriever',
    'print_benchmark_result',
    'compare_benchmarks',
    'compute_recall_at_k',
    'compute_precision_at_k',
    'compute_ndcg_at_k',
]
