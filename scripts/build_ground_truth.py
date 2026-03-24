"""
分析新的文档索引，为消融实验构建 Ground Truth
输出每个剧目的文档ID映射
"""
import json

docs = json.load(open('vector_index/documents.json', 'r', encoding='utf-8'))

# 按角色和剧目分组
by_script = {}
for d in docs:
    key = f"{d['character']}_{d['title']}"
    if key not in by_script:
        by_script[key] = []
    by_script[key].append({
        "id": d["id"],
        "type": d["type"],
        "text_len": len(d["text"]),
        "text_preview": d["text"][:80].replace("\n", " ")
    })

# 打印每个剧目的文档
for key in sorted(by_script.keys()):
    items = by_script[key]
    print(f"\n{'='*60}")
    print(f"{key} ({len(items)} docs)")
    print(f"{'='*60}")
    for item in items:
        print(f"  {item['id']:>8} | {item['type']:<20} | len={item['text_len']:>5} | {item['text_preview'][:60]}")

# 按类型统计
print(f"\n\n{'='*60}")
print("按类型统计")
print(f"{'='*60}")
type_ids = {}
for d in docs:
    t = d["type"]
    if t not in type_ids:
        type_ids[t] = []
    type_ids[t].append(d["id"])

for t, ids in sorted(type_ids.items()):
    print(f"\n{t} ({len(ids)} docs): {ids[:10]}...")

# 输出关键剧目的ID映射（用于ground truth）
print(f"\n\n{'='*60}")
print("关键剧目ID映射（用于Ground Truth）")
print(f"{'='*60}")

key_scripts = [
    "孙悟空_金钱豹", "孙悟空_盗魂铃", "孙悟空_芭蕉扇", "孙悟空_安天会",
    "孙悟空_流沙河", "孙悟空_大闹御马监", "孙悟空_高老庄", "孙悟空_盘丝洞",
    "孙悟空_安天会·偷桃", "孙悟空_安天会·大战",
    "诸葛亮_空城计", "诸葛亮_失街亭", "诸葛亮_斩马谡", "诸葛亮_骂王朗",
    "诸葛亮_三气周瑜", "诸葛亮_三顾茅庐", "诸葛亮_舌战群儒", "诸葛亮_群英会",
    "诸葛亮_定军山", "诸葛亮_七星灯",
    "赵匡胤_斩黄袍", "赵匡胤_陈桥兵变", "赵匡胤_送京娘", "赵匡胤_打龙篷",
]

for ks in key_scripts:
    if ks in by_script:
        items = by_script[ks]
        ids = [item["id"] for item in items]
        types = [item["type"] for item in items]
        print(f"\n  {ks}:")
        print(f"    all_ids = {ids}")
        # 按类型分组
        type_groups = {}
        for item in items:
            t = item["type"]
            if t not in type_groups:
                type_groups[t] = []
            type_groups[t].append(item["id"])
        for t, tids in type_groups.items():
            print(f"    {t}: {tids}")
