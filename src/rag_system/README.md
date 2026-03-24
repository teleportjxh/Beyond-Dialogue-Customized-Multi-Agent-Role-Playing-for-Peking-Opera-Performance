# RAG 检索增强系统 — 技术文档

## 概述

本模块实现了面向京剧剧本领域的 **检索增强生成（RAG）** 系统，为多智能体剧本生成提供精准的历史表演知识检索。系统采用 **三阶段增强 Pipeline**：Query 改写 → Hybrid 混合检索 → Rerank 重排序，在消融实验中相比纯 Dense 基线实现了 **Recall@5 +75.7%、MRR +34.2%** 的显著提升。

---

## 系统架构

```
                         ┌─────────────────────────────────────────────────────────┐
                         │              Enhanced Retriever Pipeline                │
                         │                                                         │
  用户查询 ──────────────►│  ① Query Rewrite ──► ② Hybrid Retrieval ──► ③ Rerank   │──► Top-K 结果
  "孔明用空城计退敌"      │     │                    │                     │         │
                         │     ▼                    ▼                     ▼         │
                         │  同义词还原           Dense(FAISS)          多维度特征    │
                         │  意图补全             + BM25(jieba)         加权评分      │
                         │  子问题拆解           RRF 融合排序          精排 Top-K    │
                         └─────────────────────────────────────────────────────────┘
```

---

## 模块文件说明

| 文件 | 类/函数 | 功能 |
|------|---------|------|
| `vector_processor.py` | `VectorProcessor` | 多级语义切分 + Embedding 向量化 |
| `vector_store.py` | `VectorStoreManager` | FAISS 向量索引的存储、加载、检索 |
| `semantic_retriever.py` | `SemanticRetriever` | 基础 Dense 语义检索器 |
| `query_rewriter.py` | `rewrite_query()` | Query 改写/扩展（同义词、意图、子问题） |
| `hybrid_retriever.py` | `BM25Retriever`, `HybridRetriever` | BM25 稀疏检索 + RRF 混合融合 |
| `reranker.py` | `CrossEncoderReranker` | 多维度特征加权重排器 |
| `enhanced_retriever.py` | `EnhancedRetriever` | 集成全部优化的增强检索器 |
| `evaluation.py` | `RAGEvaluator` | 评估框架（Recall/Precision/NDCG/MRR） |
| `scene_enhancer.py` | `SceneEnhancer` | 场景增强器（供 Agent 调用） |
| `main.py` | — | RAG 系统构建入口 |

---

## 第一阶段：多级语义切分与向量化

### 1.1 切分策略（`vector_processor.py`）

传统 RAG 系统使用固定长度切分（如 500 字符一块），但京剧剧本具有明确的语义结构（唱腔、念白、武打、角色描述等），固定切分会破坏语义完整性。本系统采用 **基于内容类型的多级语义切分**，将每部增强剧本（`enhanced_script/` 目录下的 `.txt` 文件）按语义结构切分为 5 种文档类型：

| 文档类型 | 标识关键词 | 说明 | 切分逻辑 |
|----------|-----------|------|----------|
| `plot_summary` | `剧情概述`、`故事背景`、`剧目简介` | 剧情大纲摘要 | 提取剧本开头的概述段落，按段落边界切分 |
| `character_profile` | `角色`、`扮相`、`行当`、`脸谱`、`服装` | 角色描述信息 | 按角色逐条切分，每个角色的描述为一个独立块 |
| `dialogue` | `念白`、`白`、`对白`、`独白` | 念白对话片段 | 按场次切分，以念白为主的场景归为此类 |
| `singing` | `唱`、`西皮`、`二黄`、`反二黄`、`唱腔` | 唱腔片段 | 按场次切分，以唱腔为主的场景归为此类 |
| `performance` | `武打`、`身段`、`动作`、`锣鼓`、`开打` | 舞台表演动作 | 按场次切分，以表演指示为主的场景归为此类 |

**切分参数**：

```python
MIN_CHUNK = 150   # 最小块长度（字符），过短的块合并到相邻块
MAX_CHUNK = 1200  # 最大块长度（字符），超长块按句子边界拆分
OVERLAP = 80      # 相邻块重叠字符数，保持上下文连贯
```

**切分执行流程**：

```
enhanced_script/诸葛亮/01001001_空城计_enhanced_script.txt
    │
    ▼ 读取全文
    │
    ▼ 正则匹配段落标题（如"【剧情概述】"、"【第一场】"、"【角色介绍】"）
    │
    ▼ 按标题将文本分割为语义段落
    │
    ▼ 对每个段落：
    │   ├─ 根据关键词判断文档类型（plot_summary / character_profile / ...）
    │   ├─ 如果段落 < MIN_CHUNK → 合并到相邻段落
    │   ├─ 如果段落 > MAX_CHUNK → 按句号/感叹号/问号边界拆分
    │   └─ 相邻块之间保留 OVERLAP 字符的重叠
    │
    ▼ 为每个块生成元数据：
        {
          "id": "doc_42",
          "text": "诸葛亮端坐城楼之上，手持鹅毛扇...",
          "metadata": {
            "character": "诸葛亮",
            "play": "空城计",
            "doc_type": "dialogue",
            "source_file": "01001001_空城计_enhanced_script.txt"
          }
        }
```

**最终统计**：

| 指标 | 值 |
|------|-----|
| 总文档数 | **812** 个语义块 |
| plot_summary | 55 个 |
| character_profile | 217 个 |
| dialogue | 133 个 |
| singing | 242 个 |
| performance | 165 个 |
| 角色分布 | 孙悟空 212、诸葛亮 309、赵匡胤 291 |
| 文本长度 | min=42, max=1335, avg=621, median=490 字符 |

### 1.2 Embedding 向量化

每个文档块通过 OpenAI `text-embedding-3-small` 模型转换为 1536 维向量，存储到 FAISS `IndexFlatIP`（内积索引，等价于余弦相似度，因为向量已归一化）。

```
文档文本 → text-embedding-3-small API → 1536维向量 → FAISS IndexFlatIP
```

索引文件存储在 `vector_index/` 目录：
- `faiss.index` — FAISS 二进制索引文件
- `documents.json` — 文档元数据（text、metadata、id）
- `stats.json` — 索引统计信息

### 1.3 构建命令

```bash
python scripts/rebuild_vector_index.py
```

---

## 第二阶段：Query 改写/扩展

### 2.1 模块位置

`query_rewriter.py` → `rewrite_query(query: str) -> List[str]`

### 2.2 执行流程

输入一个用户查询，输出一组改写后的查询列表（包含原始查询）。改写过程包含三个子步骤，依次执行：

```
原始查询: "孔明怎么打仗"
    │
    ├─ Step 1: 同义词/缩写还原
    │   查找 SYNONYM_MAP 中的映射：孔明 → 诸葛亮
    │   输出: "孔明(诸葛亮)怎么打仗"
    │
    ├─ Step 2: 意图模板补全
    │   匹配 INTENT_PATTERNS 中的正则：(.+)怎么打仗 → \1的战斗场面和军事谋略
    │   输出: "孔明的战斗场面和军事谋略"
    │
    └─ Step 3: 子问题拆解
        检测"和"/"与"等连接词，拆分并列查询
        检测多维度关键词（脸谱+服装 → 分别查询）
        输出: [原始查询] (本例无拆解)
    
最终返回: ["孔明怎么打仗", "孔明(诸葛亮)怎么打仗", "孔明的战斗场面和军事谋略"]
```

#### Step 1: 同义词/缩写还原 (`expand_synonyms`)

维护一个京剧领域的同义词映射表 `SYNONYM_MAP`，包含：

- **角色别名**：猴子/猴王/美猴王/齐天大圣/大圣/弼马温/行者/悟空 → 孙悟空，孔明/卧龙/武侯/丞相/军师 → 诸葛亮
- **京剧术语**：西皮 → 西皮唱腔，花脸 → 净行花脸，靠 → 硬靠铠甲
- **剧目简称**：空城计 → 空城计诸葛亮，安天会 → 安天会大闹天宫孙悟空

**执行逻辑**：遍历映射表，如果查询中包含短名且不包含全名，则将短名替换为 `短名(全名)` 格式。例如 `"猴子打妖怪"` → `"猴子(孙悟空)打妖怪"`。

#### Step 2: 意图模板补全 (`apply_intent_patterns`)

定义一组正则表达式模板 `INTENT_PATTERNS`，匹配常见的查询模式并补全京剧领域上下文：

```python
INTENT_PATTERNS = [
    (r"(.+)怎么打仗", r"\1的战斗场面和军事谋略"),
    (r"(.+)怎么唱",   r"\1的唱腔表演和念白"),
    (r"(.+)长什么样", r"\1的脸谱妆容和服饰装扮"),
    (r"(.+)穿什么",   r"\1的服饰头饰和装扮"),
    (r"(.+)的故事",   r"\1的剧情大纲和场景"),
    (r"(.+)打(.+)",   r"\1与\2的战斗武打场面"),
    (r"(.+)和(.+)的关系", r"\1与\2之间的人物关系和互动"),
]
```

**执行逻辑**：按顺序尝试匹配每个正则模式，首个匹配成功的模式用于生成补全查询。

#### Step 3: 子问题拆解 (`generate_sub_queries`)

处理两种复合查询场景：

1. **并列连接词拆解**：检测"和"、"与"、"以及"等连接词，将 `"孙悟空的脸谱和服装"` 拆分为 `["脸谱", "服装"]`
2. **多维度关键词拆解**：检测预定义的维度关键词（脸谱、服装、唱腔、武打、剧情、表演），提取主体后分别组合。例如 `"孙悟空的脸谱和服装"` → `["孙悟空 脸谱妆容", "孙悟空 服饰装扮"]`

### 2.3 在 Pipeline 中的作用

改写后的多个查询分别送入检索器，各自返回候选文档，最终按 `doc_id` 去重合并（取最高分数）。这样可以扩大召回覆盖面，但消融实验发现 **单独使用 Query Rewrite 反而降低性能**（MRR 从 0.394 → 0.207），原因是多查询融合稀释了原始查询的精确匹配信号。需要与 Hybrid+Rerank 组合使用才能发挥正向作用。

---

## 第三阶段：Hybrid 混合检索

### 3.1 模块位置

`hybrid_retriever.py` → `BM25Retriever` + `HybridRetriever`

### 3.2 BM25 稀疏检索器 (`BM25Retriever`)

BM25 是经典的基于词频的文本检索算法，与 Dense Embedding 互补：Dense 擅长语义相似度匹配，BM25 擅长精确关键词匹配（如角色名、剧目名等专有名词）。

#### 分词策略 (`_tokenize`)

针对京剧领域设计的混合分词方案：

```
输入文本: "孙悟空大闹天宫，与天兵天将大战"
    │
    ├─ Step 1: 专有名词优先匹配
    │   维护一个包含 80+ 个京剧专有名词的列表（角色名、剧目名、术语）
    │   按长度降序匹配，避免短词覆盖长词（如"孙悟空"优先于"悟空"）
    │   匹配到的专有名词作为完整 token 保留
    │   输出: ["孙悟空", "大闹天宫"]
    │
    ├─ Step 2: 剩余文本字符级分词 + bigram
    │   未被专有名词覆盖的文本按单字切分，并生成相邻字的 bigram
    │   输出: ["与", "天", "兵", "天", "将", "大", "战", "天兵", "兵天", "天将", "将大", "大战"]
    │
    └─ Step 3: 英文/数字提取
        提取英文单词和数字序列作为独立 token
    
最终 tokens: ["孙悟空", "大闹天宫", "与", "天", "兵", "天兵", "兵天", "天将", ...]
```

**设计考量**：
- 专有名词优先匹配确保"孙悟空"不会被拆成"孙"+"悟"+"空"
- bigram 补充了字级别的局部上下文（如"天兵"、"天将"）
- 不依赖外部分词库（如 jieba），避免京剧专有名词被错误切分

#### BM25 评分公式

对每个查询 token $t$ 在文档 $d$ 中的 BM25 分数：

$$\text{score}(t, d) = \text{IDF}(t) \times \frac{tf(t,d) \times (k_1 + 1)}{tf(t,d) + k_1 \times (1 - b + b \times \frac{|d|}{\text{avgdl}})}$$

其中：
- $tf(t,d)$：token $t$ 在文档 $d$ 中的出现次数
- $\text{IDF}(t) = \log\frac{N - df(t) + 0.5}{df(t) + 0.5} + 1$：逆文档频率
- $k_1 = 1.5$：词频饱和参数
- $b = 0.75$：文档长度归一化参数
- $|d|$：文档长度，$\text{avgdl}$：平均文档长度

最终文档分数 = 所有查询 token 的 BM25 分数之和。

### 3.3 Hybrid 融合 (`HybridRetriever`)

将 Dense（FAISS 语义检索）和 Sparse（BM25 词汇检索）的结果通过 **Reciprocal Rank Fusion (RRF)** 融合为统一排序。

#### RRF 融合执行流程

```
查询: "孙悟空大闹天宫的唱腔"
    │
    ├─ Dense 检索 (FAISS, top_k=30)
    │   返回按语义相似度排序的文档列表
    │   [doc_A(rank=1), doc_B(rank=2), doc_C(rank=3), ...]
    │
    ├─ Sparse 检索 (BM25, top_k=30)
    │   返回按 BM25 分数排序的文档列表
    │   [doc_C(rank=1), doc_D(rank=2), doc_A(rank=3), ...]
    │
    └─ RRF 融合
        对每个文档计算 RRF 分数：
        
        RRF_score(doc) = α/(k + rank_dense) + (1-α)/(k + rank_sparse)
        
        其中 α=0.5（Dense 权重），k=60（RRF 常数）
        
        示例：
        doc_A: 0.5/(60+1) + 0.5/(60+3) = 0.00820 + 0.00794 = 0.01614
        doc_C: 0.5/(60+3) + 0.5/(60+1) = 0.00794 + 0.00820 = 0.01614
        doc_B: 0.5/(60+2) + 0/(未出现)  = 0.00806
        doc_D: 0/(未出现)  + 0.5/(60+2) = 0.00806
        
        按 RRF 分数降序排列 → 返回 Top-K
```

**RRF 的优势**：
- 不需要对两种检索器的分数进行归一化（Dense 分数范围 [0,1]，BM25 分数范围不固定）
- 只依赖排名位置，对分数分布不敏感
- 参数 $k=60$ 是经验值，使得排名靠前的文档获得更高权重

### 3.4 消融实验中的效果

| 配置 | R@5 | P@5 | MRR |
|------|-----|-----|-----|
| A: Baseline (Dense Only) | 0.179 | 0.179 | 0.394 |
| C: + Hybrid (Dense+BM25) | 0.236 | 0.236 | 0.469 |
| **提升** | **+31.8%** | **+31.8%** | **+19.0%** |

BM25 对包含角色名、剧目名等专有名词的查询效果尤为显著，因为这些词在 Dense Embedding 空间中可能与其他词距离较近，但在 BM25 中可以精确匹配。

---

## 第四阶段：Rerank 重排序

### 4.1 模块位置

`reranker.py` → `CrossEncoderReranker`

### 4.2 设计思路

检索阶段（Dense + BM25）返回 top-50 个候选文档，但排序质量有限。Rerank 阶段对这 50 个候选进行精细评分，重新排序后返回 top-K（通常 5~10 个）。

本系统实现了一个 **多维度特征加权的轻量级重排器**，不依赖外部 Transformer 模型（如 BAAI/bge-reranker），避免额外的 GPU/API 开销。

### 4.3 六维度特征评分 (`_lightweight_score`)

对每个 (query, document) 对，计算 6 个维度的特征分数，加权求和得到最终重排分数：

```
总分 = 0.40 × 关键词精确匹配
     + 0.20 × 关键词频率加权
     + 0.15 × 连续子串匹配
     + 0.15 × 位置权重
     + 0.05 × 文档长度适中奖励
     + 0.05 × 字符覆盖率
```

#### 维度 1：关键词精确匹配（权重 0.40）

```python
# 提取查询中的 2-4 字中文词
query_keywords = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
# 例如 "孙悟空大闹天宫" → ["孙悟空", "大闹", "闹天", "天宫", "大闹天", "闹天宫"]（2-4字组合）

# 计算匹配比例
matched = sum(1 for kw in query_keywords if kw in document)
keyword_ratio = matched / len(query_keywords)
# 如果 4/6 个关键词在文档中出现 → 0.40 × (4/6) = 0.267
```

**作用**：最重要的信号，直接衡量查询关键词是否出现在文档中。

#### 维度 2：关键词频率加权（权重 0.20）

```python
# 对每个匹配的关键词，统计其在文档中的出现次数
for kw in query_keywords:
    count = document.count(kw)
    freq_score += min(count / 5.0, 1.0)  # 出现 5 次以上视为饱和
freq_score /= len(query_keywords)
```

**作用**：区分"提到一次"和"反复讨论"的文档。例如查询"孙悟空"，一个文档提到 1 次 vs 另一个文档提到 8 次，后者更可能是核心相关文档。

#### 维度 3：连续子串匹配（权重 0.15）

```python
# 在文档中查找查询的最长连续子串
max_substr_len = 0
for i in range(len(query)):
    for j in range(i+2, min(i+15, len(query)+1)):
        substr = query[i:j]
        if substr in document:
            max_substr_len = max(max_substr_len, len(substr))
substr_ratio = min(max_substr_len / len(query), 1.0)
```

**作用**：捕捉查询与文档之间的短语级匹配。例如查询"大闹天宫"，如果文档中包含完整的"大闹天宫"（4字连续匹配），比只包含"大闹"和"天宫"（分散匹配）得分更高。

#### 维度 4：位置权重（权重 0.15）

```python
# 关键词在文档中出现的位置越靠前，分数越高
for kw in query_keywords:
    pos = document.find(kw)
    if pos != -1:
        position_score = max(0, 1.0 - pos / len(document))
        early_match += position_score
early_ratio = early_match / len(query_keywords)
```

**作用**：文档开头通常包含标题、摘要等核心信息，关键词出现在开头比出现在末尾更有指示性。

#### 维度 5：文档长度适中奖励（权重 0.05）

```python
if doc_len < 100:
    len_score = doc_len / 100      # 过短文档惩罚
elif doc_len > 1500:
    len_score = 1500 / doc_len     # 过长文档惩罚
else:
    len_score = 1.0                # 100-1500 字符为最佳范围
```

**作用**：避免过短（信息不足）或过长（噪声过多）的文档获得过高排名。

#### 维度 6：字符覆盖率（权重 0.05）

```python
query_chars = set(c for c in query if '\u4e00' <= c <= '\u9fff')
overlap = sum(1 for c in query_chars if c in document)
char_coverage = overlap / len(query_chars)
```

**作用**：作为兜底信号，即使关键词未完全匹配，单字级别的覆盖也能提供微弱的相关性信号。

### 4.4 消融实验中的效果

| 配置 | R@5 | P@3 | NDCG@3 | MRR |
|------|-----|-----|--------|-----|
| A: Baseline | 0.179 | 0.202 | 0.216 | 0.394 |
| D: + Rerank | 0.279 | 0.310 | 0.311 | 0.465 |
| **提升** | **+55.9%** | **+53.5%** | **+44.0%** | **+18.0%** |

Rerank 是单组件中提升最大的模块，尤其在 Precision 和 NDCG 上效果显著，说明重排序有效地将相关文档推到了更靠前的位置。

---

## 集成 Pipeline：EnhancedRetriever

### 5.1 模块位置

`enhanced_retriever.py` → `EnhancedRetriever`

### 5.2 完整执行流程

```python
enhanced = EnhancedRetriever(
    vector_store=vector_store,
    base_retriever=base_retriever,
    enable_query_rewrite=True,   # 启用 Query 改写
    enable_hybrid=True,          # 启用 Hybrid 检索
    enable_rerank=True,          # 启用 Rerank
    retrieve_top_n=50,           # 初始检索 50 个候选
    rerank_top_k=5,              # 重排后返回 5 个
)
enhanced.build_bm25_index()      # 构建 BM25 索引
results = enhanced.search("孙悟空大闹天宫的唱腔", top_k=5)
```

**内部执行流程**：

```
输入: "孙悟空大闹天宫的唱腔"
    │
    ▼ Step 1: Query 改写 (enable_query_rewrite=True)
    │   rewrite_query("孙悟空大闹天宫的唱腔")
    │   → ["孙悟空大闹天宫的唱腔",
    │       "孙悟空大闹天宫的唱腔表演和念白"]  (意图补全)
    │
    ▼ Step 2: 对每个改写查询执行 Hybrid 检索
    │   查询1: hybrid.search("孙悟空大闹天宫的唱腔", top_k=50)
    │     ├─ Dense(FAISS): 返回 30 个语义相似文档
    │     ├─ Sparse(BM25): 返回 30 个关键词匹配文档
    │     └─ RRF 融合: 合并去重 → 50 个候选
    │   查询2: hybrid.search("孙悟空大闹天宫的唱腔表演和念白", top_k=50)
    │     └─ 同上
    │
    ▼ Step 3: 多查询结果合并
    │   按 doc_id 去重，同一文档取最高分数
    │   合并后约 60-80 个唯一候选文档
    │
    ▼ Step 4: Rerank 重排序 (enable_rerank=True)
    │   CrossEncoderReranker.rerank(query, candidates, top_k=5)
    │   对每个候选文档计算 6 维度特征分数
    │   按总分降序排列 → 返回 Top-5
    │
    ▼ 输出: 5 个最相关的文档
        [
          {"id": "doc_123", "text": "安天会·大战 唱腔...", "rerank_score": 0.72},
          {"id": "doc_456", "text": "大闹天宫 西皮快板...", "rerank_score": 0.68},
          ...
        ]
```

### 5.3 组件开关控制

`EnhancedRetriever` 支持通过构造参数独立开关每个组件，这也是消融实验的基础：

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `enable_query_rewrite` | `True` | 是否启用 Query 改写 |
| `enable_hybrid` | `True` | 是否启用 BM25 混合检索（关闭则仅用 Dense） |
| `enable_rerank` | `True` | 是否启用 Rerank 重排序 |
| `retrieve_top_n` | `50` | 初始检索候选数量 |
| `rerank_top_k` | `5` | 重排后返回数量 |
| `dense_weight` | `0.5` | RRF 融合中 Dense 的权重（α） |

---

## 消融实验

### 6.1 实验设计

对 3 个优化组件（Query Rewrite / Hybrid / Rerank）进行 2³ = 8 种组合的消融实验，评估每个组件的独立贡献和组合效果。

### 6.2 Ground Truth 构建

Ground Truth 通过 `scripts/auto_ground_truth.py` 自动生成，基于文档内容关键词匹配：

```
对每个查询（如"孙悟空大闹天宫"）：
    遍历 812 个文档 →
    计算关键词匹配分数（角色名+剧目名+动作词在文档中的出现次数）→
    取分数最高的 3-5 个文档作为该查询的相关文档集
```

共生成 28 个测试查询，覆盖 6 类场景，平均每个查询标注 4.9 个相关文档。

### 6.3 评估指标

| 指标 | 公式 | 说明 |
|------|------|------|
| **Recall@k** | \|retrieved ∩ relevant\| / \|relevant\| | 前 k 个结果中召回了多少相关文档 |
| **Precision@k** | \|retrieved ∩ relevant\| / k | 前 k 个结果中有多少是相关的 |
| **NDCG@k** | DCG@k / IDCG@k | 归一化折损累积增益，考虑排序位置 |
| **MRR** | 1 / rank_of_first_relevant | 第一个相关文档的排名倒数 |


### 6.5 关键结论

1. **Hybrid + Rerank (G) 是最佳配置**：NDCG@5 = 0.333，MRR = 0.530，延迟仅 3.2ms
2. **Rerank 是最有价值的单组件**：P@3 从 0.202 → 0.310（+53.5%），说明重排序显著改善了排序质量
3. **BM25 混合检索有效补充 Dense**：R@10 从 0.307 → 0.443，对专有名词查询效果显著
4. **Query Rewrite 需谨慎使用**：单独使用降低性能（MRR 0.394 → 0.207），但与 Hybrid+Rerank 组合后有正向贡献
5. **Full Pipeline vs Baseline**：Recall@5 +75.7%，Precision@3 +76.7%，MRR +34.2%

### 6.6 运行消融实验

```bash
# Step 1: 自动生成 Ground Truth
python scripts/auto_ground_truth.py

# Step 2: 运行 8 组消融实验
python scripts/evaluation/run_ablation.py

# 结果保存在 scripts/evaluation/results/ablation_results_latest.json
```

---

## 代码集成示例

```python
from src.rag_system.vector_store import VectorStoreManager
from src.rag_system.semantic_retriever import SemanticRetriever
from src.rag_system.enhanced_retriever import EnhancedRetriever

# 1. 加载向量索引
vector_store = VectorStoreManager(index_dir="vector_index")
vector_store.load_index()

# 2. 创建基础检索器
base_retriever = SemanticRetriever(vector_store)

# 3. 创建增强检索器（启用全部优化）
enhanced = EnhancedRetriever(
    vector_store=vector_store,
    base_retriever=base_retriever,
    enable_query_rewrite=True,
    enable_hybrid=True,
    enable_rerank=True,
    retrieve_top_n=50,
    rerank_top_k=5,
)
enhanced.build_bm25_index()

# 4. 检索
results = enhanced.search("孙悟空大闹天宫的唱腔", top_k=5)
for r in results:
    print(f"[{r['metadata']['doc_type']}] {r['text'][:80]}...")

# 5. 带详细信息的检索
details = enhanced.search_with_details("诸葛亮空城计", top_k=5)
print(f"改写查询: {details['rewritten_queries']}")
print(f"检索耗时: {details['retrieval_time_ms']:.1f}ms")
```

---

## 依赖

| 包 | 用途 |
|----|------|
| `faiss-cpu` | FAISS 向量索引 |
| `langchain_openai` | OpenAI Embeddings API |
| `numpy` | 数值计算 |
| `sentence-transformers`（可选） | CrossEncoder 模型（当前使用轻量级方案替代） |
