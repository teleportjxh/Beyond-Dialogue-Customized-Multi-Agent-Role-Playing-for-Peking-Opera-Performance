"""
RAG 系统评估模块
提供 Recall@k, Precision@k, NDCG@k, Answer Relevance 等指标计算
"""

import json
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class EvalQuery:
    """评估查询"""
    query: str
    relevant_doc_ids: List[str]  # ground truth 相关文档ID
    character: Optional[str] = None
    category: str = "general"


@dataclass
class EvalResult:
    """单个查询的评估结果"""
    query: str
    retrieved_ids: List[str]
    relevant_ids: List[str]
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    ndcg_at_k: Dict[int, float] = field(default_factory=dict)
    retrieval_time_ms: float = 0.0


@dataclass
class BenchmarkResult:
    """整体评估结果"""
    name: str
    total_queries: int
    avg_recall: Dict[int, float] = field(default_factory=dict)
    avg_precision: Dict[int, float] = field(default_factory=dict)
    avg_ndcg: Dict[int, float] = field(default_factory=dict)
    avg_retrieval_time_ms: float = 0.0
    per_query_results: List[EvalResult] = field(default_factory=list)


def create_ground_truth() -> List[EvalQuery]:
    """
    创建评估基准测试集 (Ground Truth)
    基于已有的文档数据，构建查询-相关文档对
    """
    queries = [
        # === 角色相关查询 ===
        EvalQuery(
            query="孙悟空大闹天宫的故事",
            relevant_doc_ids=["doc_21", "doc_51", "doc_52"],  # 安天会相关
            character="孙悟空",
            category="character_story"
        ),
        EvalQuery(
            query="诸葛亮空城计退敌",
            relevant_doc_ids=["doc_57", "doc_58", "doc_61"],  # 空城计相关
            character="诸葛亮",
            category="character_story"
        ),
        EvalQuery(
            query="孙悟空三借芭蕉扇",
            relevant_doc_ids=["doc_16", "doc_17", "doc_18", "doc_19", "doc_20"],  # 芭蕉扇
            character="孙悟空",
            category="character_story"
        ),
        EvalQuery(
            query="诸葛亮骂死王朗",
            relevant_doc_ids=["doc_94", "doc_95", "doc_96", "doc_97", "doc_98"],  # 骂王朗
            character="诸葛亮",
            category="character_story"
        ),
        EvalQuery(
            query="孙悟空降妖除魔金钱豹",
            relevant_doc_ids=["doc_0", "doc_1", "doc_2", "doc_6", "doc_8"],  # 金钱豹
            character="孙悟空",
            category="character_story"
        ),

        # === 场景/表演相关查询 ===
        EvalQuery(
            query="京剧中武打场面的表演",
            relevant_doc_ids=["doc_8", "doc_11", "doc_12", "doc_13", "doc_52"],
            category="performance"
        ),
        EvalQuery(
            query="京剧中的唱腔和念白表演",
            relevant_doc_ids=["doc_58", "doc_61", "doc_98"],
            category="performance"
        ),
        EvalQuery(
            query="猪八戒的滑稽表演",
            relevant_doc_ids=["doc_14", "doc_47", "doc_48", "doc_49", "doc_50"],
            category="performance"
        ),

        # === 剧情查询 ===
        EvalQuery(
            query="师徒四人西天取经路上遇到妖怪",
            relevant_doc_ids=["doc_0", "doc_14", "doc_16", "doc_22", "doc_33"],
            character="孙悟空",
            category="plot"
        ),
        EvalQuery(
            query="诸葛亮用计谋打败敌人",
            relevant_doc_ids=["doc_57", "doc_73", "doc_86", "doc_94", "doc_99"],
            character="诸葛亮",
            category="plot"
        ),
        EvalQuery(
            query="流沙河收服沙僧",
            relevant_doc_ids=["doc_22", "doc_23", "doc_24", "doc_25", "doc_26", "doc_27", "doc_28", "doc_29", "doc_30", "doc_31", "doc_32"],
            character="孙悟空",
            category="plot"
        ),
        EvalQuery(
            query="刘备三顾茅庐请诸葛亮出山",
            relevant_doc_ids=["doc_100"],
            character="诸葛亮",
            category="plot"
        ),

        # === 脸谱/妆容查询 ===
        EvalQuery(
            query="孙悟空的猴脸脸谱和服装",
            relevant_doc_ids=["doc_0", "doc_14", "doc_16", "doc_21", "doc_22", "doc_34"],
            character="孙悟空",
            category="costume"
        ),
        EvalQuery(
            query="诸葛亮的八卦衣和鹅毛扇",
            relevant_doc_ids=["doc_57", "doc_64", "doc_71", "doc_73", "doc_81", "doc_86", "doc_94"],
            character="诸葛亮",
            category="costume"
        ),

        # === 跨角色查询 ===
        EvalQuery(
            query="京剧中的战争场面和军事对阵",
            relevant_doc_ids=["doc_21", "doc_52", "doc_86", "doc_85"],
            category="cross_character"
        ),
        EvalQuery(
            query="京剧中忠义精神的表现",
            relevant_doc_ids=["doc_57", "doc_72", "doc_87", "doc_106"],
            category="cross_character"
        ),

        # === 专有名词/术语查询 ===
        EvalQuery(
            query="西皮二六板唱腔",
            relevant_doc_ids=["doc_58", "doc_61", "doc_98"],
            category="terminology"
        ),
        EvalQuery(
            query="靠旗和帅盔的穿戴",
            relevant_doc_ids=["doc_0", "doc_16", "doc_21", "doc_57"],
            category="terminology"
        ),

        # === 模糊/口语化查询 ===
        EvalQuery(
            query="猴子打妖怪",
            relevant_doc_ids=["doc_0", "doc_8", "doc_11", "doc_13", "doc_33"],
            character="孙悟空",
            category="fuzzy"
        ),
        EvalQuery(
            query="诸葛亮怎么打仗的",
            relevant_doc_ids=["doc_57", "doc_73", "doc_86", "doc_94", "doc_99"],
            character="诸葛亮",
            category="fuzzy"
        ),
    ]

    return queries


def compute_recall_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """计算 Recall@k"""
    if not relevant_ids:
        return 0.0
    retrieved_set = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    return len(retrieved_set & relevant_set) / len(relevant_set)


def compute_precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """计算 Precision@k"""
    if k == 0:
        return 0.0
    retrieved_set = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    return len(retrieved_set & relevant_set) / k


def compute_dcg(relevances: List[float], k: int) -> float:
    """计算 DCG@k"""
    dcg = 0.0
    for i, rel in enumerate(relevances[:k]):
        dcg += rel / np.log2(i + 2)  # i+2 because log2(1) = 0
    return dcg


def compute_ndcg_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """计算 NDCG@k"""
    if not relevant_ids:
        return 0.0

    relevant_set = set(relevant_ids)

    # 实际的 relevance scores
    relevances = [1.0 if doc_id in relevant_set else 0.0 for doc_id in retrieved_ids[:k]]

    # 理想的 relevance scores
    ideal_relevances = sorted(
        [1.0 if doc_id in relevant_set else 0.0 for doc_id in retrieved_ids[:k]] +
        [1.0] * max(0, len(relevant_set) - sum(1 for r in relevances if r > 0)),
        reverse=True
    )

    dcg = compute_dcg(relevances, k)
    idcg = compute_dcg(ideal_relevances, k)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate_retriever(
    retriever_fn,
    queries: List[EvalQuery],
    k_values: List[int] = [3, 5, 10, 20],
    name: str = "baseline"
) -> BenchmarkResult:
    """
    评估检索器性能

    Args:
        retriever_fn: 检索函数，接受 query 字符串，返回 List[Dict] 结果
        queries: 评估查询列表
        k_values: 要评估的 k 值列表
        name: 评估名称

    Returns:
        BenchmarkResult 评估结果
    """
    all_results = []
    max_k = max(k_values)

    for eq in queries:
        start_time = time.time()
        results = retriever_fn(eq.query, top_k=max_k)
        elapsed_ms = (time.time() - start_time) * 1000

        retrieved_ids = [r.get("id", "") for r in results]

        eval_result = EvalResult(
            query=eq.query,
            retrieved_ids=retrieved_ids,
            relevant_ids=eq.relevant_doc_ids,
            retrieval_time_ms=elapsed_ms
        )

        for k in k_values:
            eval_result.recall_at_k[k] = compute_recall_at_k(retrieved_ids, eq.relevant_doc_ids, k)
            eval_result.precision_at_k[k] = compute_precision_at_k(retrieved_ids, eq.relevant_doc_ids, k)
            eval_result.ndcg_at_k[k] = compute_ndcg_at_k(retrieved_ids, eq.relevant_doc_ids, k)

        all_results.append(eval_result)

    # 计算平均指标
    benchmark = BenchmarkResult(
        name=name,
        total_queries=len(queries),
        per_query_results=all_results,
        avg_retrieval_time_ms=np.mean([r.retrieval_time_ms for r in all_results])
    )

    for k in k_values:
        benchmark.avg_recall[k] = np.mean([r.recall_at_k[k] for r in all_results])
        benchmark.avg_precision[k] = np.mean([r.precision_at_k[k] for r in all_results])
        benchmark.avg_ndcg[k] = np.mean([r.ndcg_at_k[k] for r in all_results])

    return benchmark


def print_benchmark_result(result: BenchmarkResult):
    """打印评估结果"""
    print("\n" + "=" * 70)
    print(f"📊 评估结果: {result.name}")
    print("=" * 70)
    print(f"总查询数: {result.total_queries}")
    print(f"平均检索时间: {result.avg_retrieval_time_ms:.1f} ms")
    print()

    # 表头
    k_values = sorted(result.avg_recall.keys())
    header = f"{'指标':<20}" + "".join([f"{'@' + str(k):<12}" for k in k_values])
    print(header)
    print("-" * len(header))

    # Recall
    row = f"{'Recall':<20}"
    for k in k_values:
        row += f"{result.avg_recall[k]:<12.4f}"
    print(row)

    # Precision
    row = f"{'Precision':<20}"
    for k in k_values:
        row += f"{result.avg_precision[k]:<12.4f}"
    print(row)

    # NDCG
    row = f"{'NDCG':<20}"
    for k in k_values:
        row += f"{result.avg_ndcg[k]:<12.4f}"
    print(row)

    print("=" * 70)

    # 按类别统计
    categories = {}
    for i, eq in enumerate(create_ground_truth()):
        if i < len(result.per_query_results):
            cat = eq.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result.per_query_results[i])

    if categories:
        print("\n📋 按类别统计 (Recall@5):")
        print("-" * 40)
        for cat, results in categories.items():
            avg_recall = np.mean([r.recall_at_k.get(5, 0) for r in results])
            print(f"  {cat:<25} {avg_recall:.4f}")


def compare_benchmarks(results: List[BenchmarkResult]):
    """对比多个评估结果"""
    print("\n" + "=" * 80)
    print("📊 评估结果对比")
    print("=" * 80)

    k_values = sorted(results[0].avg_recall.keys())

    for k in k_values:
        print(f"\n--- @{k} ---")
        header = f"{'系统':<25}{'Recall':<12}{'Precision':<12}{'NDCG':<12}"
        print(header)
        print("-" * len(header))
        for r in results:
            row = f"{r.name:<25}{r.avg_recall.get(k, 0):<12.4f}{r.avg_precision.get(k, 0):<12.4f}{r.avg_ndcg.get(k, 0):<12.4f}"
            print(row)

    # 检索时间对比
    print(f"\n--- 平均检索时间 ---")
    for r in results:
        print(f"  {r.name:<25} {r.avg_retrieval_time_ms:.1f} ms")

    print("=" * 80)
