"""
Query 改写/扩展模块
- 同义词、缩写还原
- 子问题拆解
- 意图补全
直接提升：Recall@k、Context Recall
"""

import re
from typing import List, Dict, Optional


# 京剧领域同义词/缩写映射表
SYNONYM_MAP = {
    # 角色别名
    "猴子": "孙悟空",
    "猴王": "孙悟空",
    "美猴王": "孙悟空",
    "齐天大圣": "孙悟空",
    "大圣": "孙悟空",
    "弼马温": "孙悟空",
    "行者": "孙悟空",
    "悟空": "孙悟空",
    "孔明": "诸葛亮",
    "卧龙": "诸葛亮",
    "武侯": "诸葛亮",
    "丞相": "诸葛亮",
    "军师": "诸葛亮",
    "八戒": "猪八戒",
    "呆子": "猪八戒",
    "老猪": "猪八戒",
    "悟净": "沙僧",
    "沙和尚": "沙僧",
    "唐僧": "唐三藏",
    "玄奘": "唐三藏",
    "师父": "唐三藏",
    "关公": "关羽",
    "云长": "关羽",
    "关二爷": "关羽",
    "翼德": "张飞",
    "子龙": "赵云",
    "周郎": "周瑜",
    "公瑾": "周瑜",
    # 京剧术语缩写还原
    "西皮": "西皮唱腔",
    "二黄": "二黄唱腔",
    "花脸": "净行花脸",
    "老生": "老生行当",
    "武生": "武生行当",
    "青衣": "青衣旦角",
    "花旦": "花旦行当",
    "靠": "硬靠铠甲",
    "翎子": "雉翎翎子",
    # 剧目简称
    "空城计": "空城计诸葛亮",
    "定军山": "定军山黄忠",
    "芭蕉扇": "芭蕉扇孙悟空铁扇公主",
    "安天会": "安天会大闹天宫孙悟空",
    "三顾": "三顾茅庐刘备诸葛亮",
}

# 意图模板：根据查询模式补全意图
INTENT_PATTERNS = [
    # 角色+动作 -> 补全为完整查询
    (r"(.+)怎么打仗", r"\1的战斗场面和军事谋略"),
    (r"(.+)怎么唱", r"\1的唱腔表演和念白"),
    (r"(.+)长什么样", r"\1的脸谱妆容和服饰装扮"),
    (r"(.+)穿什么", r"\1的服饰头饰和装扮"),
    (r"(.+)的故事", r"\1的剧情大纲和场景"),
    (r"(.+)打(.+)", r"\1与\2的战斗武打场面"),
    (r"(.+)和(.+)的关系", r"\1与\2之间的人物关系和互动"),
]


def expand_synonyms(query: str) -> str:
    """同义词/缩写还原"""
    expanded = query
    for short, full in SYNONYM_MAP.items():
        if short in expanded and full not in expanded:
            expanded = expanded.replace(short, f"{short}({full})")
    return expanded


def apply_intent_patterns(query: str) -> str:
    """应用意图模板补全查询"""
    for pattern, replacement in INTENT_PATTERNS:
        match = re.match(pattern, query)
        if match:
            return re.sub(pattern, replacement, query)
    return query


def generate_sub_queries(query: str) -> List[str]:
    """
    子问题拆解：将复杂查询拆分为多个子查询
    """
    sub_queries = [query]

    # 检测"和"/"与"/"以及"连接的并列查询
    conjunctions = ["和", "与", "以及", "还有", "并且"]
    for conj in conjunctions:
        if conj in query:
            parts = query.split(conj)
            if len(parts) == 2:
                sub_queries.extend([p.strip() for p in parts if p.strip()])
                break

    # 检测多维度查询（如"脸谱和服装"）
    dimension_keywords = {
        "脸谱": "脸谱妆容",
        "服装": "服饰装扮",
        "唱腔": "唱腔表演",
        "武打": "武打动作",
        "剧情": "剧情故事",
        "表演": "表演身段",
    }
    found_dims = []
    for kw, full in dimension_keywords.items():
        if kw in query:
            found_dims.append(full)

    if len(found_dims) > 1:
        # 提取主体（去掉维度关键词后的部分）
        subject = query
        for kw in dimension_keywords:
            subject = subject.replace(kw, "").strip()
        subject = re.sub(r'[和与以及的]', '', subject).strip()
        if subject:
            for dim in found_dims:
                sub_queries.append(f"{subject} {dim}")

    return list(set(sub_queries))


def rewrite_query(query: str) -> List[str]:
    """
    完整的查询改写流程
    返回原始查询 + 改写后的查询列表
    """
    queries = set()
    queries.add(query)

    # 1. 同义词扩展
    expanded = expand_synonyms(query)
    if expanded != query:
        queries.add(expanded)

    # 2. 意图补全
    intent_query = apply_intent_patterns(query)
    if intent_query != query:
        queries.add(intent_query)

    # 3. 子问题拆解
    sub_queries = generate_sub_queries(query)
    queries.update(sub_queries)

    return list(queries)
