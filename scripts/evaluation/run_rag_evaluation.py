"""
RAG 系统评估运行脚本
对比 Baseline vs Enhanced 系统的 Recall@k, Precision@k, NDCG@k 等指标
"""

import os
import sys
import json
import time

# 添加项目根目录到 path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def run_evaluation():
    """运行完整评估"""
    from src.rag_system.vector_store import VectorStoreManager
    from src.rag_system.semantic_retriever import SemanticRetriever
    from src.rag_system.enhanced_retriever import (
        EnhancedRetriever,
        create_baseline_retriever_fn,
        create_enhanced_retriever_fn
    )
    from src.rag_system.evaluation import (
        create_ground_truth,
        evaluate_retriever,
        print_benchmark_result,
        compare_benchmarks
    )

    print("=" * 70)
    print("🎭 京剧 RAG 系统评估")
    print("=" * 70)

    # 1. 加载向量索引
    print("\n📦 加载向量索引...")
    vector_store = VectorStoreManager(index_dir="vector_index")
    if not vector_store.load_index():
        print("❌ 向量索引加载失败！请先运行: python -m src.rag_system.main build")
        return

    stats = vector_store.get_statistics()
    print(f"   文档数: {stats['total_documents']}")
    print(f"   角色: {', '.join(stats['characters'])}")

    # 2. 初始化检索器
    print("\n🔧 初始化检索器...")
    base_retriever = SemanticRetriever(vector_store)

    # 确保文档有 id 字段
    for i, doc in enumerate(vector_store.documents):
        if "id" not in doc:
            doc["id"] = f"doc_{i}"

    # 3. 创建 Ground Truth
    print("\n📋 创建评估基准测试集...")
    ground_truth = create_ground_truth()
    print(f"   测试查询数: {len(ground_truth)}")

    # 4. 评估 Baseline
    print("\n" + "=" * 70)
    print("📊 评估 1/5: Baseline (仅 Dense 检索)")
    print("=" * 70)
    baseline_fn = create_baseline_retriever_fn(base_retriever)
    baseline_result = evaluate_retriever(
        baseline_fn, ground_truth,
        k_values=[3, 5, 10, 20],
        name="Baseline (Dense Only)"
    )
    print_benchmark_result(baseline_result)

    # 5. 评估 Query Rewrite Only
    print("\n" + "=" * 70)
    print("📊 评估 2/5: Query Rewrite Only")
    print("=" * 70)
    qr_retriever = EnhancedRetriever(
        vector_store=vector_store,
        base_retriever=base_retriever,
        enable_query_rewrite=True,
        enable_hybrid=False,
        enable_rerank=False,
    )
    qr_fn = create_enhanced_retriever_fn(qr_retriever)
    qr_result = evaluate_retriever(
        qr_fn, ground_truth,
        k_values=[3, 5, 10, 20],
        name="+ Query Rewrite"
    )
    print_benchmark_result(qr_result)

    # 6. 评估 Query Rewrite + Hybrid
    print("\n" + "=" * 70)
    print("📊 评估 3/5: Query Rewrite + Hybrid (Dense + BM25)")
    print("=" * 70)
    hybrid_retriever = EnhancedRetriever(
        vector_store=vector_store,
        base_retriever=base_retriever,
        enable_query_rewrite=True,
        enable_hybrid=True,
        enable_rerank=False,
    )
    hybrid_retriever.build_bm25_index()
    hybrid_fn = create_enhanced_retriever_fn(hybrid_retriever)
    hybrid_result = evaluate_retriever(
        hybrid_fn, ground_truth,
        k_values=[3, 5, 10, 20],
        name="+ Query Rewrite + Hybrid"
    )
    print_benchmark_result(hybrid_result)

    # 7. 评估 Full Pipeline (Query Rewrite + Hybrid + Rerank)
    print("\n" + "=" * 70)
    print("📊 评估 4/5: Full Pipeline (QR + Hybrid + Rerank)")
    print("=" * 70)
    full_retriever = EnhancedRetriever(
        vector_store=vector_store,
        base_retriever=base_retriever,
        enable_query_rewrite=True,
        enable_hybrid=True,
        enable_rerank=True,
        retrieve_top_n=50,
        rerank_top_k=10,
    )
    full_retriever.build_bm25_index()
    full_fn = create_enhanced_retriever_fn(full_retriever)
    full_result = evaluate_retriever(
        full_fn, ground_truth,
        k_values=[3, 5, 10, 20],
        name="Full Pipeline (QR+Hybrid+Rerank)"
    )
    print_benchmark_result(full_result)

    # 8. 评估 Hybrid + Rerank (无 Query Rewrite)
    print("\n" + "=" * 70)
    print("📊 评估 5/5: Hybrid + Rerank (无 Query Rewrite)")
    print("=" * 70)
    hr_retriever = EnhancedRetriever(
        vector_store=vector_store,
        base_retriever=base_retriever,
        enable_query_rewrite=False,
        enable_hybrid=True,
        enable_rerank=True,
        retrieve_top_n=50,
        rerank_top_k=10,
    )
    hr_retriever.build_bm25_index()
    hr_fn = create_enhanced_retriever_fn(hr_retriever)
    hr_result = evaluate_retriever(
        hr_fn, ground_truth,
        k_values=[3, 5, 10, 20],
        name="Hybrid + Rerank (No QR)"
    )
    print_benchmark_result(hr_result)

    # 9. 对比所有结果
    all_results = [baseline_result, qr_result, hybrid_result, full_result, hr_result]
    compare_benchmarks(all_results)

    # 10. 保存评估结果
    output_dir = os.path.join(project_root, "scripts", "evaluation", "results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "rag_evaluation_results.json")

    eval_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_queries": len(ground_truth),
        "results": []
    }

    for r in all_results:
        eval_data["results"].append({
            "name": r.name,
            "avg_recall": {str(k): float(v) for k, v in r.avg_recall.items()},
            "avg_precision": {str(k): float(v) for k, v in r.avg_precision.items()},
            "avg_ndcg": {str(k): float(v) for k, v in r.avg_ndcg.items()},
            "avg_retrieval_time_ms": float(r.avg_retrieval_time_ms),
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 评估结果已保存到: {output_file}")

    # 11. 打印改进总结
    print("\n" + "=" * 70)
    print("📈 改进总结")
    print("=" * 70)

    for k in [3, 5, 10]:
        baseline_recall = baseline_result.avg_recall.get(k, 0)
        full_recall = full_result.avg_recall.get(k, 0)
        baseline_precision = baseline_result.avg_precision.get(k, 0)
        full_precision = full_result.avg_precision.get(k, 0)
        baseline_ndcg = baseline_result.avg_ndcg.get(k, 0)
        full_ndcg = full_result.avg_ndcg.get(k, 0)

        recall_delta = full_recall - baseline_recall
        precision_delta = full_precision - baseline_precision
        ndcg_delta = full_ndcg - baseline_ndcg

        print(f"\n@{k}:")
        print(f"  Recall:    {baseline_recall:.4f} → {full_recall:.4f} ({recall_delta:+.4f})")
        print(f"  Precision: {baseline_precision:.4f} → {full_precision:.4f} ({precision_delta:+.4f})")
        print(f"  NDCG:      {baseline_ndcg:.4f} → {full_ndcg:.4f} ({ndcg_delta:+.4f})")

    print("\n" + "=" * 70)
    print("✅ 评估完成！")
    print("=" * 70)


def run_quick_test():
    """快速测试（不需要向量索引）"""
    print("=" * 70)
    print("🧪 快速模块测试")
    print("=" * 70)

    # 测试 Query Rewriter
    print("\n--- Query Rewriter 测试 ---")
    from src.rag_system.query_rewriter import rewrite_query
    test_queries = [
        "猴子打妖怪",
        "孔明怎么打仗",
        "大圣的故事",
        "孙悟空的脸谱和服装",
        "西皮二六板唱腔",
    ]
    for q in test_queries:
        rewritten = rewrite_query(q)
        print(f"  原始: {q}")
        print(f"  改写: {rewritten}")
        print()

    # 测试 BM25
    print("\n--- BM25 Retriever 测试 ---")
    from src.rag_system.hybrid_retriever import BM25Retriever
    bm25 = BM25Retriever()
    test_docs = [
        {"id": "doc_0", "text": "孙悟空大闹天宫，与天兵天将大战", "metadata": {"title": "安天会"}},
        {"id": "doc_1", "text": "诸葛亮在空城上弹琴退敌", "metadata": {"title": "空城计"}},
        {"id": "doc_2", "text": "孙悟空三借芭蕉扇，与铁扇公主斗法", "metadata": {"title": "芭蕉扇"}},
        {"id": "doc_3", "text": "刘备三顾茅庐请诸葛亮出山", "metadata": {"title": "三顾茅庐"}},
        {"id": "doc_4", "text": "京剧武生表演翻跟头打把子", "metadata": {"title": "武打表演"}},
    ]
    bm25.build_index(test_docs)
    results = bm25.search("孙悟空打妖怪", top_k=3)
    for r in results:
        print(f"  [{r['id']}] score={r['bm25_score']:.4f} - {r['text'][:40]}")

    # 测试 Reranker
    print("\n--- CrossEncoder Reranker 测试 ---")
    from src.rag_system.reranker import CrossEncoderReranker
    reranker = CrossEncoderReranker(use_lightweight=True)
    reranked = reranker.rerank("诸葛亮用计谋", test_docs, top_k=3)
    for r in reranked:
        print(f"  [{r['id']}] rerank_score={r['rerank_score']:.4f} - {r['text'][:40]}")

    # 测试评估指标
    print("\n--- 评估指标计算测试 ---")
    from src.rag_system.evaluation import (
        compute_recall_at_k, compute_precision_at_k, compute_ndcg_at_k
    )
    retrieved = ["doc_0", "doc_3", "doc_1", "doc_4", "doc_2"]
    relevant = ["doc_0", "doc_2", "doc_5"]

    for k in [3, 5]:
        recall = compute_recall_at_k(retrieved, relevant, k)
        precision = compute_precision_at_k(retrieved, relevant, k)
        ndcg = compute_ndcg_at_k(retrieved, relevant, k)
        print(f"  @{k}: Recall={recall:.4f}, Precision={precision:.4f}, NDCG={ndcg:.4f}")

    print("\n✅ 快速测试完成！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RAG 系统评估")
    parser.add_argument(
        "--mode",
        choices=["full", "quick"],
        default="quick",
        help="评估模式: full=完整评估(需要向量索引), quick=快速模块测试"
    )
    args = parser.parse_args()

    if args.mode == "full":
        run_evaluation()
    else:
        run_quick_test()
