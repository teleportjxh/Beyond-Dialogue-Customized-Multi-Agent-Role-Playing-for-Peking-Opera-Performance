"""
自动生成 Ground Truth：基于文档内容的关键词匹配 + 语义相关性
每个查询只标注 3-5 个最核心的相关文档
"""
import json, os, sys, re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

docs = json.load(open(os.path.join(project_root, 'vector_index', 'documents.json'), 'r', encoding='utf-8'))

# Ensure IDs
for i, d in enumerate(docs):
    if 'id' not in d:
        d['id'] = f'doc_{i}'


def find_relevant(keywords, character=None, doc_type=None, max_docs=5, min_score=2):
    """基于关键词在文档内容中的出现次数来找相关文档"""
    scored = []
    for d in docs:
        # Character filter
        if character and d.get('character', '') != character:
            continue
        if doc_type and d.get('type', '') != doc_type:
            continue
        
        text = d.get('text', '')
        title = d.get('title', '')
        score = 0
        for kw in keywords:
            if kw in text:
                score += text.count(kw)
            if kw in title:
                score += 3  # title match is worth more
        if score >= min_score:
            scored.append((d['id'], score))
    
    scored.sort(key=lambda x: -x[1])
    return [s[0] for s in scored[:max_docs]]


def find_by_play(play_name, character=None, max_docs=5):
    """按剧目名查找文档"""
    results = []
    for d in docs:
        if character and d.get('character', '') != character:
            continue
        title = d.get('title', '')
        text = d.get('text', '')
        if play_name in title or play_name in text[:200]:
            results.append(d['id'])
    return results[:max_docs]


# Build ground truth
queries = []

# === character_story (10) ===
queries.append({
    "query": "孙悟空降妖除魔金钱豹",
    "character": "孙悟空", "category": "character_story",
    "relevant_doc_ids": find_relevant(["金钱豹", "降妖", "除魔"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "孙悟空盗魂铃的剧情",
    "character": "孙悟空", "category": "character_story",
    "relevant_doc_ids": find_relevant(["盗魂铃", "魂铃"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "孙悟空三借芭蕉扇",
    "character": "孙悟空", "category": "character_story",
    "relevant_doc_ids": find_relevant(["芭蕉扇", "铁扇公主", "牛魔王"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "孙悟空大闹天宫的故事",
    "character": "孙悟空", "category": "character_story",
    "relevant_doc_ids": find_relevant(["大闹天宫", "天宫", "安天会", "天兵", "天将"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "诸葛亮空城计退敌",
    "character": "诸葛亮", "category": "character_story",
    "relevant_doc_ids": find_relevant(["空城计", "空城", "退敌", "城楼", "弹琴"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "诸葛亮骂死王朗",
    "character": "诸葛亮", "category": "character_story",
    "relevant_doc_ids": find_relevant(["王朗", "骂"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "诸葛亮失街亭斩马谡",
    "character": "诸葛亮", "category": "character_story",
    "relevant_doc_ids": find_relevant(["街亭", "马谡", "斩"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "诸葛亮三气周瑜",
    "character": "诸葛亮", "category": "character_story",
    "relevant_doc_ids": find_relevant(["周瑜", "三气"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "赵匡胤斩黄袍的故事",
    "character": "赵匡胤", "category": "character_story",
    "relevant_doc_ids": find_relevant(["斩黄袍", "黄袍"], character="赵匡胤", max_docs=5)
})
queries.append({
    "query": "赵匡胤陈桥兵变黄袍加身",
    "character": "赵匡胤", "category": "character_story",
    "relevant_doc_ids": find_relevant(["陈桥", "兵变", "黄袍加身"], character="赵匡胤", max_docs=5)
})

# === plot (8) ===
queries.append({
    "query": "流沙河收服沙僧",
    "character": "孙悟空", "category": "plot",
    "relevant_doc_ids": find_relevant(["流沙河", "沙僧", "沙和尚"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "刘备三顾茅庐请诸葛亮出山",
    "character": "诸葛亮", "category": "plot",
    "relevant_doc_ids": find_relevant(["三顾茅庐", "茅庐", "刘备", "出山"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "诸葛亮舌战群儒",
    "character": "诸葛亮", "category": "plot",
    "relevant_doc_ids": find_relevant(["舌战", "群儒"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "孙悟空大闹御马监",
    "character": "孙悟空", "category": "plot",
    "relevant_doc_ids": find_relevant(["御马监", "弼马温"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "赵匡胤千里送京娘",
    "character": "赵匡胤", "category": "plot",
    "relevant_doc_ids": find_relevant(["送京娘", "京娘", "千里送"], character="赵匡胤", max_docs=5)
})
queries.append({
    "query": "赵匡胤打龙篷",
    "character": "赵匡胤", "category": "plot",
    "relevant_doc_ids": find_relevant(["打龙篷", "打龙棚", "龙篷", "龙棚"], character="赵匡胤", max_docs=5)
})
queries.append({
    "query": "孙悟空高老庄收猪八戒",
    "character": "孙悟空", "category": "plot",
    "relevant_doc_ids": find_relevant(["高老庄", "猪八戒", "高翠兰"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "诸葛亮定军山之战",
    "character": "诸葛亮", "category": "plot",
    "relevant_doc_ids": find_relevant(["定军山", "黄忠", "夏侯渊"], character="诸葛亮", max_docs=5)
})

# === specific_play (3) ===
queries.append({
    "query": "京剧盘丝洞的剧情",
    "character": "孙悟空", "category": "specific_play",
    "relevant_doc_ids": find_relevant(["盘丝洞", "蜘蛛精"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "京剧群英会的内容",
    "character": "诸葛亮", "category": "specific_play",
    "relevant_doc_ids": find_relevant(["群英会", "蒋干", "周瑜"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "京剧龙虎斗的故事",
    "character": "赵匡胤", "category": "specific_play",
    "relevant_doc_ids": find_relevant(["龙虎斗"], character="赵匡胤", max_docs=5)
})

# === character_profile (3) ===
queries.append({
    "query": "孙悟空的脸谱和服装",
    "character": "孙悟空", "category": "character_profile",
    "relevant_doc_ids": find_relevant(["脸谱", "服装", "扮相", "猴脸", "行头", "穿戴"], character="孙悟空", max_docs=5)
})
queries.append({
    "query": "诸葛亮的八卦衣和鹅毛扇",
    "character": "诸葛亮", "category": "character_profile",
    "relevant_doc_ids": find_relevant(["八卦衣", "鹅毛扇", "纶巾", "扮相", "行头"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "赵匡胤的扮相和行头",
    "character": "赵匡胤", "category": "character_profile",
    "relevant_doc_ids": find_relevant(["扮相", "行头", "蟒袍", "穿戴", "服装"], character="赵匡胤", max_docs=5)
})

# === fuzzy (4) ===
queries.append({
    "query": "猴子打妖怪",
    "character": "孙悟空", "category": "fuzzy",
    "relevant_doc_ids": find_relevant(["孙悟空", "妖怪", "妖精", "降妖", "打"], character="孙悟空", max_docs=5, min_score=3)
})
queries.append({
    "query": "孔明借东风",
    "character": "诸葛亮", "category": "fuzzy",
    "relevant_doc_ids": find_relevant(["借东风", "东风", "诸葛亮", "祭风"], character="诸葛亮", max_docs=5)
})
queries.append({
    "query": "大圣闹天宫",
    "character": "孙悟空", "category": "fuzzy",
    "relevant_doc_ids": find_relevant(["天宫", "大闹", "安天会", "孙悟空"], character="孙悟空", max_docs=5, min_score=3)
})
queries.append({
    "query": "赵匡胤当皇帝",
    "character": "赵匡胤", "category": "fuzzy",
    "relevant_doc_ids": find_relevant(["皇帝", "登基", "称帝", "兵变", "黄袍加身", "陈桥"], character="赵匡胤", max_docs=5)
})

# Filter out queries with no relevant docs
valid_queries = [q for q in queries if len(q['relevant_doc_ids']) >= 2]

print(f"Total queries: {len(queries)}")
print(f"Valid queries (>=2 relevant docs): {len(valid_queries)}")
print()

for q in valid_queries:
    print(f"Q: {q['query']}")
    print(f"  Category: {q['category']}, Character: {q.get('character','')}")
    print(f"  Relevant ({len(q['relevant_doc_ids'])}): {q['relevant_doc_ids']}")
    # Show first relevant doc content
    for did in q['relevant_doc_ids'][:2]:
        idx = int(did.split('_')[1])
        if idx < len(docs):
            print(f"    {did}: {docs[idx].get('text','')[:80]}...")
    print()

# Save
avg_rel = sum(len(q['relevant_doc_ids']) for q in valid_queries) / max(len(valid_queries), 1)
output = {
    "total_queries": len(valid_queries),
    "avg_relevant_per_query": round(avg_rel, 1),
    "queries": valid_queries
}
out_path = os.path.join(project_root, 'scripts', 'evaluation', 'auto_ground_truth.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {out_path}")
