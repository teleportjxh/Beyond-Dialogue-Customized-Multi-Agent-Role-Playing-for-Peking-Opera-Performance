"""分析消融实验结果，找出指标低的原因"""
import json

data = json.load(open('scripts/evaluation/results/ablation_results_latest.json', 'r', encoding='utf-8'))

# Full Pipeline per-query
full = data['ablation_results'][-1]
baseline = data['ablation_results'][0]

print("=" * 120)
print("Per-Query Analysis (Full Pipeline H vs Baseline A)")
print("=" * 120)
print(f"{'Query':<35} {'Cat':<18} {'#rel':<5} {'BL_R@10':<9} {'FP_R@10':<9} {'FP_R@20':<9} {'hits@10':<8} {'ret_ids[:5]'}")
print("-" * 120)

for qf, qb in zip(full['per_query'], baseline['per_query']):
    rel = set(qf['relevant_ids'])
    ret10 = qf['retrieved_ids'][:10]
    hits = len(set(ret10) & rel)
    bl_r10 = qb['metrics']['recall@10']
    fp_r10 = qf['metrics']['recall@10']
    fp_r20 = qf['metrics']['recall@20']
    ret5_str = str(qf['retrieved_ids'][:5])
    print(f"{qf['query'][:33]:<35} {qf['category']:<18} {len(rel):<5} {bl_r10:<9.3f} {fp_r10:<9.3f} {fp_r20:<9.3f} {hits:<8} {ret5_str[:50]}")

# Summary: queries with 0 hits at @10
print(f"\n{'='*80}")
print("Queries with R@10 = 0 (Full Pipeline):")
print(f"{'='*80}")
for q in full['per_query']:
    if q['metrics']['recall@10'] == 0:
        print(f"  Q: {q['query']}")
        print(f"    relevant: {q['relevant_ids'][:5]}...")
        print(f"    retrieved: {q['retrieved_ids'][:5]}")

# Key issue: how many relevant docs per query
print(f"\n{'='*80}")
print("Ground Truth Stats:")
print(f"{'='*80}")
rel_counts = [len(q['relevant_ids']) for q in full['per_query']]
print(f"  Avg relevant docs per query: {sum(rel_counts)/len(rel_counts):.1f}")
print(f"  Min: {min(rel_counts)}, Max: {max(rel_counts)}")
print(f"  Total queries: {len(full['per_query'])}")

# Check: are retrieved IDs matching format?
print(f"\n{'='*80}")
print("ID Format Check:")
print(f"{'='*80}")
sample_ret = full['per_query'][0]['retrieved_ids'][:3]
sample_rel = full['per_query'][0]['relevant_ids'][:3]
print(f"  Sample retrieved IDs: {sample_ret}")
print(f"  Sample relevant IDs: {sample_rel}")
print(f"  ID format match: {type(sample_ret[0])} vs {type(sample_rel[0])}")

# Check actual document store
docs = json.load(open('vector_index/documents.json', 'r', encoding='utf-8'))
print(f"\n  Doc store sample IDs: {[d.get('id','NO_ID') for d in docs[:5]]}")
print(f"  Doc store has 'id' field: {'id' in docs[0]}")
