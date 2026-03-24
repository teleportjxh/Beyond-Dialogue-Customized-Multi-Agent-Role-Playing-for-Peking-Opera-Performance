"""
RAG 系统消融实验 (Ablation Study)
使用自动生成的 Ground Truth（基于文档内容关键词匹配）
"""
import os, sys, json, time, math
import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

RESULTS_DIR = os.path.join(project_root, "scripts", "evaluation", "results")
CACHE_DIR = os.path.join(project_root, "scripts", "evaluation", "cache")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
EMBEDDING_CACHE_FILE = os.path.join(CACHE_DIR, "query_embeddings.json")


def load_embedding_cache():
    if os.path.exists(EMBEDDING_CACHE_FILE):
        with open(EMBEDDING_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_embedding_cache(cache):
    with open(EMBEDDING_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)


def get_cached_embedding(query, emb_model, cache, retries=5):
    if query in cache:
        return cache[query]
    for i in range(retries):
        try:
            vec = emb_model.embed_query(query)
            cache[query] = vec
            save_embedding_cache(cache)
            return vec
        except Exception as e:
            if i < retries - 1:
                time.sleep(3 * (i + 1))
    raise RuntimeError(f"Embedding failed: {query}")


def create_embeddings_with_timeout():
    from langchain_openai import OpenAIEmbeddings
    from src.config import Config
    import httpx
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=Config.API_KEY,
        openai_api_base=Config.BASE_URL,
        http_client=httpx.Client(timeout=httpx.Timeout(120.0, connect=30.0)),
        timeout=120,
    )


def precompute_embeddings(queries, emb_model):
    cache = load_embedding_cache()
    missing = [q for q in queries if q not in cache]
    if missing:
        print(f"  Pre-computing {len(missing)} embeddings (cached: {len(cache)})...")
        for q in missing:
            get_cached_embedding(q, emb_model, cache)
    return cache


def load_ground_truth():
    """从自动生成的 ground truth 文件加载"""
    from src.rag_system.evaluation import EvalQuery
    gt_path = os.path.join(project_root, "scripts", "evaluation", "auto_ground_truth.json")
    if not os.path.exists(gt_path):
        print(f"Ground truth not found: {gt_path}")
        print("Run: python scripts/auto_ground_truth.py")
        sys.exit(1)
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = []
    for q in data['queries']:
        queries.append(EvalQuery(
            query=q['query'],
            character=q.get('character', ''),
            category=q.get('category', ''),
            relevant_doc_ids=q['relevant_doc_ids']
        ))
    return queries


def compute_recall(ret_ids, rel_ids, k):
    if not rel_ids: return 0.0
    return len(set(ret_ids[:k]) & set(rel_ids)) / len(rel_ids)

def compute_precision(ret_ids, rel_ids, k):
    if k == 0: return 0.0
    return len(set(ret_ids[:k]) & set(rel_ids)) / k

def compute_ndcg(ret_ids, rel_ids, k):
    if not rel_ids: return 0.0
    rel_set = set(rel_ids)
    rels = [1.0 if d in rel_set else 0.0 for d in ret_ids[:k]]
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels))
    ideal = sorted(rels + [1.0] * max(0, len(rel_set) - sum(1 for r in rels if r > 0)), reverse=True)
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal[:k]))
    return dcg / idcg if idcg > 0 else 0.0

def compute_mrr(ret_ids, rel_ids):
    rel_set = set(rel_ids)
    for i, rid in enumerate(ret_ids):
        if rid in rel_set:
            return 1.0 / (i + 1)
    return 0.0


def run_ablation():
    from src.rag_system.vector_store import VectorStoreManager
    from src.rag_system.semantic_retriever import SemanticRetriever
    from src.rag_system.enhanced_retriever import EnhancedRetriever

    print("=" * 80)
    print("RAG Ablation Study (Auto Ground Truth)")
    print("=" * 80)

    # 1. Load vector index
    print("\nLoading vector index...")
    vector_store = VectorStoreManager(index_dir="vector_index")
    if not vector_store.load_index():
        print("Failed to load vector index!")
        return
    stats = vector_store.get_statistics()
    print(f"  Documents: {stats['total_documents']}, Characters: {', '.join(stats['characters'])}")

    for i, doc in enumerate(vector_store.documents):
        if "id" not in doc:
            doc["id"] = f"doc_{i}"

    # 2. Init retriever
    base_retriever = SemanticRetriever(vector_store)
    try:
        base_retriever.embeddings = create_embeddings_with_timeout()
    except Exception:
        pass

    # 3. Ground truth
    ground_truth = load_ground_truth()
    print(f"  Test queries: {len(ground_truth)}")
    avg_rel = np.mean([len(q.relevant_doc_ids) for q in ground_truth])
    print(f"  Avg relevant docs per query: {avg_rel:.1f}")

    # 4. Precompute embeddings
    from src.rag_system.query_rewriter import rewrite_query
    all_texts = set()
    for eq in ground_truth:
        all_texts.add(eq.query)
        for rq in rewrite_query(eq.query):
            all_texts.add(rq)
    emb_cache = precompute_embeddings(list(all_texts), base_retriever.embeddings)

    class CachedEmb:
        def __init__(self, orig, cache):
            self._orig = orig
            self._cache = cache
        def embed_query(self, text):
            if text in self._cache:
                return self._cache[text]
            vec = self._orig.embed_query(text)
            self._cache[text] = vec
            save_embedding_cache(self._cache)
            return vec
        def embed_documents(self, texts):
            return self._orig.embed_documents(texts)

    cached_emb = CachedEmb(base_retriever.embeddings, emb_cache)
    base_retriever.embeddings = cached_emb

    # 5. Ablation configs: (name, query_rewrite, hybrid, rerank)
    configs = [
        ("A: Baseline (Dense Only)",            False, False, False),
        ("B: + Query Rewrite",                  True,  False, False),
        ("C: + Hybrid (Dense+BM25)",            False, True,  False),
        ("D: + Rerank",                         False, False, True),
        ("E: QR + Hybrid",                      True,  True,  False),
        ("F: QR + Rerank",                      True,  False, True),
        ("G: Hybrid + Rerank",                  False, True,  True),
        ("H: Full Pipeline (QR+Hybrid+Rerank)", True,  True,  True),
    ]

    k_values = [1, 3, 5, 10]
    all_results = []

    for cfg_name, qr, hybrid, rerank in configs:
        print(f"\n{'='*70}")
        print(f"  {cfg_name}")
        print(f"{'='*70}")

        retriever = EnhancedRetriever(
            vector_store=vector_store, base_retriever=base_retriever,
            enable_query_rewrite=qr, enable_hybrid=hybrid, enable_rerank=rerank,
            retrieve_top_n=50, rerank_top_k=10,
        )
        # Use lightweight reranker (no embedding calls for reranking)
        if hybrid:
            retriever.build_bm25_index()

        per_query = []
        total_time = 0.0

        for eq in ground_truth:
            t0 = time.time()
            if not qr and not hybrid and not rerank:
                results = base_retriever.retrieve(query=eq.query, top_k=max(k_values))
                for idx, r in enumerate(results):
                    if "id" not in r:
                        r["id"] = f"doc_{idx}"
            else:
                results = retriever.search(eq.query, top_k=max(k_values))
            elapsed = (time.time() - t0) * 1000
            total_time += elapsed

            ret_ids = [r.get("id", "") for r in results]
            q_res = {"query": eq.query, "category": eq.category, "character": eq.character,
                     "retrieved_ids": ret_ids[:20], "relevant_ids": eq.relevant_doc_ids,
                     "time_ms": round(elapsed, 2), "metrics": {}}
            for k in k_values:
                q_res["metrics"][f"recall@{k}"] = round(compute_recall(ret_ids, eq.relevant_doc_ids, k), 4)
                q_res["metrics"][f"precision@{k}"] = round(compute_precision(ret_ids, eq.relevant_doc_ids, k), 4)
                q_res["metrics"][f"ndcg@{k}"] = round(compute_ndcg(ret_ids, eq.relevant_doc_ids, k), 4)
            q_res["metrics"]["mrr"] = round(compute_mrr(ret_ids, eq.relevant_doc_ids), 4)
            per_query.append(q_res)

        # Aggregate
        avg_m = {}
        for k in k_values:
            for m in ["recall", "precision", "ndcg"]:
                key = f"{m}@{k}"
                avg_m[key] = round(np.mean([q["metrics"][key] for q in per_query]), 4)
        avg_m["mrr"] = round(np.mean([q["metrics"]["mrr"] for q in per_query]), 4)

        # Category breakdown
        cats = {}
        for q in per_query:
            cats.setdefault(q["category"], []).append(q)
        cat_m = {}
        for cat, qs in cats.items():
            cat_m[cat] = {"count": len(qs),
                          "recall@5": round(np.mean([q["metrics"]["recall@5"] for q in qs]), 4),
                          "precision@5": round(np.mean([q["metrics"]["precision@5"] for q in qs]), 4),
                          "ndcg@5": round(np.mean([q["metrics"]["ndcg@5"] for q in qs]), 4),
                          "mrr": round(np.mean([q["metrics"]["mrr"] for q in qs]), 4)}

        avg_time = round(total_time / len(ground_truth), 2)
        cfg_result = {"name": cfg_name,
                      "config": {"query_rewrite": qr, "hybrid": hybrid, "rerank": rerank},
                      "avg_metrics": avg_m, "avg_time_ms": avg_time,
                      "category_metrics": cat_m, "per_query": per_query}
        all_results.append(cfg_result)

        # Print summary
        print(f"\n  {'Metric':<18}", end="")
        for k in k_values:
            print(f"{'@'+str(k):<10}", end="")
        print(f"{'MRR':<10}")
        for mn in ["recall", "precision", "ndcg"]:
            print(f"  {mn:<18}", end="")
            for k in k_values:
                print(f"{avg_m[f'{mn}@{k}']:<10.4f}", end="")
            print()
        print(f"  MRR: {avg_m['mrr']:.4f}    avg_time: {avg_time:.1f} ms")

    # 6. Save results
    ts = time.strftime("%Y%m%d_%H%M%S")
    output = {
        "experiment": "RAG Ablation Study (Auto Ground Truth)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": {"total_documents": stats["total_documents"],
                     "characters": stats["characters"],
                     "total_queries": len(ground_truth),
                     "avg_relevant_per_query": round(avg_rel, 1)},
        "chunk_info": {
            "method": "Multi-level Semantic Chunking",
            "types": "plot_summary, character_profile, dialogue, singing, performance",
            "total_chunks": stats["total_documents"],
            "embedding_model": "text-embedding-3-small (1536d)",
            "index_type": "FAISS IndexFlatIP (cosine)",
        },
        "ablation_results": all_results,
    }
    for fname in [f"ablation_results_{ts}.json", "ablation_results_latest.json"]:
        with open(os.path.join(RESULTS_DIR, fname), 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    # 7. Print comparison table
    print(f"\n{'='*120}")
    print("Ablation Comparison Table")
    print(f"{'='*120}")
    hdr = f"{'Config':<42}"
    for k in [1, 3, 5]:
        hdr += f"{'R@'+str(k):<8}{'P@'+str(k):<8}{'N@'+str(k):<8}"
    hdr += f"{'MRR':<8}{'Time':<8}"
    print(hdr)
    print("-" * 120)
    for r in all_results:
        row = f"{r['name']:<42}"
        for k in [1, 3, 5]:
            rk = f"recall@{k}"
            pk = f"precision@{k}"
            nk = f"ndcg@{k}"
            row += f"{r['avg_metrics'][rk]:<8.4f}"
            row += f"{r['avg_metrics'][pk]:<8.4f}"
            row += f"{r['avg_metrics'][nk]:<8.4f}"
        row += f"{r['avg_metrics']['mrr']:<8.4f}"
        row += f"{r['avg_time_ms']:<8.1f}"
        print(row)

    if len(all_results) >= 2:
        bl = all_results[0]
        fp = all_results[-1]
        print(f"\nFull Pipeline vs Baseline improvement:")
        for k in [1, 3, 5]:
            rk = f"recall@{k}"
            pk = f"precision@{k}"
            nk = f"ndcg@{k}"
            dr = fp['avg_metrics'][rk] - bl['avg_metrics'][rk]
            dp = fp['avg_metrics'][pk] - bl['avg_metrics'][pk]
            dn = fp['avg_metrics'][nk] - bl['avg_metrics'][nk]
            print(f"  @{k}: Recall {dr:+.4f}, Precision {dp:+.4f}, NDCG {dn:+.4f}")
        dm = fp['avg_metrics']['mrr'] - bl['avg_metrics']['mrr']
        print(f"  MRR: {dm:+.4f}")

    print(f"\nResults saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    run_ablation()
