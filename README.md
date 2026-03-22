# Beyond Dialogue: Customized Multi-Agent Role-Playing for Peking Opera Performance

> 超越对话：面向京剧表演的定制化多智能体角色扮演系统

## 项目概述

本项目构建了一套面向京剧表演的**多智能体角色扮演剧本生成系统**，通过大语言模型（LLM）与检索增强生成（RAG）技术，实现对特定京剧角色（如诸葛亮、孙悟空、赵匡胤等）的深度定制化剧本自动创作。系统不仅能够生成符合京剧规范（西皮/二黄唱腔、念白风格、舞台动作）的剧本对话，还能根据角色历史表演数据生成个性化的唱腔设计、服装配置与场景布局，并通过下游视频生成子系统实现最终的数字京剧表演内容。

## 系统流程图

![系统流程图](流程图.png)

系统由三个核心阶段组成：

1. **数据提取阶段**：从历史京剧剧本（PDF/TXT）中提取结构化角色数据，经 LLM 语义增强后构建角色知识库
2. **RAG 检索增强阶段**：基于 FAISS 向量索引，为剧本生成提供精准的历史表演片段参考
3. **多智能体剧本生成阶段**：基于 **CrewAI** 框架，由编剧、导演、演员、服装设计师、场景设计师等多个专业智能体协作，生成完整的定制化京剧剧本

---

## 技术架构

### 多Agent框架：CrewAI

系统采用 **CrewAI** 作为多智能体编排框架，实现了以下核心能力：

- **Agent 定义**：每个智能体拥有独立的角色（role）、目标（goal）、背景故事（backstory）和工具集（tools）
- **Task 驱动**：所有工作以 Task 为单位分配给 Agent，支持顺序执行和委派
- **Tool 集成**：将 RAG 检索、角色数据加载、剧本格式化等功能封装为 CrewAI Tool，供 Agent 按需调用
- **记忆系统**：双层记忆架构——滑动窗口短期记忆 + RAG 长期记忆

### 记忆系统

| 记忆类型 | 实现方式 | 用途 |
|----------|----------|------|
| **短期记忆** | 滑动窗口（SlidingWindowMemory） | 保留最近 N 轮对话，超出窗口自动摘要压缩 |
| **长期记忆** | RAG 向量检索（RAGLongTermMemory） | 基于 FAISS 索引检索历史京剧知识 |

### Agent 角色分工

| Agent | 角色 | 职责 | 可委派 |
|-------|------|------|--------|
| **编剧 Agent** | 京剧编剧 | 创作剧本大纲、审查服装/场景设计、规划演员行动 | ✅ |
| **服装设计 Agent** | 京剧服装设计师 | 设计角色服装、脸谱方案，接受编剧审查 | ❌ |
| **场景设计 Agent** | 京剧场景设计师 | 设计舞台布景、音效方案，接受编剧审查 | ❌ |
| **演员 Agent** | 京剧演员（动态创建） | 扮演特定角色，生成对话，自我审查 | ❌ |
| **导演 Agent** | 京剧导演 | 控制对话流程，审查演员表演，最终评估 | ✅ |

### Tool 工具集

| 工具 | 类型 | 功能 |
|------|------|------|
| `RAGSearchTool` | RAG | 语义检索历史京剧知识 |
| `CharacterSceneRetrieveTool` | RAG | 检索角色相关场景片段 |
| `LoadCharacterProfileTool` | 角色 | 加载角色档案（profile.json） |
| `LoadCharacterDataTool` | 角色 | 加载角色详细数据（data.json） |
| `ExtractCharactersTool` | 角色 | 从用户输入中提取角色名 |
| `ParseJSONTool` | 剧本 | 从 LLM 输出中提取 JSON |
| `FormatScriptTool` | 剧本 | 格式化京剧剧本文本 |

---

## 创作流程（4 Phase Pipeline）

```
用户需求输入
    ↓
╔══════════════════════════════════════════════════╗
║  Phase 1: 大纲创作（编剧 Agent 主导）              ║
║  - 提取角色 → 加载角色档案 → 创作剧本大纲          ║
╚══════════════════════════════════════════════════╝
    ↓
╔══════════════════════════════════════════════════╗
║  Phase 2: 设计阶段（编剧审查）                     ║
║  2a. 服装设计 Agent → 编剧审查 → (修改)            ║
║  2b. 场景设计 Agent → 编剧审查 → (修改)            ║
╚══════════════════════════════════════════════════╝
    ↓
╔══════════════════════════════════════════════════╗
║  Phase 3: 对话生成（导演控制 + 演员表演）           ║
║  每场戏循环：                                      ║
║    编剧规划行动 → 导演选择说话者 →                  ║
║    演员生成对话(含自审) → 导演审查 → (修改)         ║
║    → 更新短期记忆 → 下一轮                         ║
╚══════════════════════════════════════════════════╝
    ↓
╔══════════════════════════════════════════════════╗
║  Phase 4: 最终评估（导演 Agent）                   ║
║  - 多维度评分 → 生成评估报告                       ║
╚══════════════════════════════════════════════════╝
    ↓
generated_scripts/（完整剧本 + 场景设定 + 装扮设计 + 评估报告）
```

---

## 项目结构

```
.
├── main.py                       # 🚀 主入口：CrewAI 剧本生成系统
├── src/
│   ├── config.py                 # 全局配置（API密钥、模型参数等）
│   ├── agents/                   # 🤖 Agent 定义层（CrewAI Agent）
│   │   ├── __init__.py
│   │   ├── screenwriter.py       # 编剧 Agent
│   │   ├── costume_designer.py   # 服装设计 Agent
│   │   ├── scene_designer.py     # 场景设计 Agent
│   │   ├── actor.py              # 演员 Agent（动态创建）
│   │   └── director.py           # 导演 Agent
│   ├── tools/                    # 🔧 Tool 工具层（CrewAI Tool）
│   │   ├── __init__.py
│   │   ├── rag_tools.py          # RAG 检索工具
│   │   ├── character_tools.py    # 角色数据工具
│   │   └── script_tools.py       # 剧本处理工具
│   ├── memory/                   # 🧠 记忆系统
│   │   ├── __init__.py
│   │   ├── sliding_window_memory.py  # 滑动窗口短期记忆
│   │   └── rag_long_term_memory.py   # RAG 长期记忆
│   ├── crew/                     # 🎬 CrewAI 编排层
│   │   ├── __init__.py
│   │   ├── tasks.py              # Task 定义（所有任务模板）
│   │   └── opera_crew.py         # PekingOperaCrew 主编排类
│   ├── data_extraction/          # 数据提取模块
│   │   ├── extractor.py          # PDF/TXT 剧本结构化提取
│   │   ├── llm_client.py         # LLM API 客户端
│   │   ├── data_models.py        # 数据结构定义
│   │   ├── utils.py              # 工具函数
│   │   └── main.py               # 数据提取入口
│   ├── rag_system/               # RAG 检索增强模块
│   │   ├── vector_processor.py   # 文本向量化处理
│   │   ├── vector_store.py       # FAISS 向量存储管理
│   │   ├── semantic_retriever.py # 语义相似度检索
│   │   ├── scene_enhancer.py     # 场景增强器
│   │   └── main.py               # RAG 系统入口
│   └── script_generation/        # 旧版多智能体模块（已重构为 agents/crew/）
│       └── README.md             # 模块说明
├── scripts/                      # 工具脚本集合
│   ├── data_collection/          # 数据采集脚本
│   ├── data_processing/          # 数据处理脚本
│   ├── demo/                     # 功能演示脚本
│   ├── evaluation/               # 评估与对比脚本
│   └── tests/                    # 测试脚本
├── pdfdata/                      # 原始 PDF 剧本（按角色分类）
├── txtdata/                      # 原始 TXT 剧本（按角色分类）
├── enhanced_script/              # LLM 增强后的结构化剧本
├── character_data/               # 角色知识库 JSON 数据
├── character/                    # 角色档案（Profile）
├── vector_index/                 # FAISS 向量索引
├── generated_scripts/            # 系统生成的剧本输出
├── example/                      # 示例剧本参考
├── doc/                          # 开发文档
└── vedio_generation/             # 🎬 视频生成子项目（下游任务）
```

---

## 核心模块详解

### 1. 数据提取模块 (`src/data_extraction/`)

从原始京剧剧本（PDF/TXT格式）中提取结构化数据，通过大语言模型进行语义增强，生成包含以下信息的角色知识库：

- **唱腔数据**：西皮、二黄等唱腔类型的完整唱词
- **念白数据**：韵白、散白的台词风格
- **动作数据**：水袖、圆场、亮相等身段动作描述
- **情节数据**：剧目故事背景与角色关系

### 2. RAG 检索增强模块 (`src/rag_system/`)

基于 FAISS 向量数据库构建语义检索系统：

- **向量化**：将增强剧本切片并编码为语义向量
- **检索**：根据当前剧情需求，检索历史相似表演片段
- **增强**：将检索结果注入剧本生成提示词，提升角色一致性

### 3. CrewAI 多智能体系统 (`src/agents/` + `src/crew/` + `src/tools/` + `src/memory/`)

采用 CrewAI 框架的专业化多智能体协作架构：

- **Agent 层** (`src/agents/`)：定义 5 类专业 Agent，每个 Agent 拥有独立的角色设定、目标和工具集
- **Tool 层** (`src/tools/`)：将 RAG 检索、角色数据加载等功能封装为 CrewAI BaseTool
- **Memory 层** (`src/memory/`)：双层记忆系统——滑动窗口短期记忆 + RAG 长期记忆
- **Crew 层** (`src/crew/`)：定义 Task 模板和 PekingOperaCrew 主编排类，实现 4 阶段创作流程

---

## 数据流向

```
[数据采集]
哔哩哔哩/戏曲资源库
        ↓
pdfdata/ & txtdata/（原始剧本）
        ↓
[数据处理]
scripts/data_processing/extract.py
        ↓
enhanced_script/（结构化剧本）
        ↓
scripts/data_processing/process_with_model_batch.py
        ↓
character_data/（角色JSON知识库）
        ↓
[RAG索引构建]
src/rag_system/
        ↓
vector_index/（FAISS向量索引）
        ↓
[CrewAI 多智能体剧本生成]
python main.py
        ↓
generated_scripts/（完整剧本 + 场景设定 + 装扮设计 + 评估报告）
        ↓
[下游：视频生成]
vedio_generation/
        ↓
京剧数字表演视频
```

---

## 快速开始

### 环境要求

- Python 3.10+
- CrewAI 框架
- 大语言模型 API（OpenAI / DeepSeek / 其他兼容接口）
- FAISS（向量检索库）

### 安装依赖

```bash
pip install crewai crewai-tools openai faiss-cpu numpy requests
```

### 配置 API

复制 `src/config.example.py` 为 `src/config.py`，填入 LLM API 密钥和接口地址：

```python
class Config:
    API_KEY = "sk-your_api_key_here"
    BASE_URL = "https://api.openai.com/v1/"   # 或其他兼容接口地址
    MODEL_NAME = "gpt-4o"                      # 或 deepseek-chat 等
```

### 运行剧本生成

```bash
# 交互式运行（系统会提示输入创作需求）
python main.py

# 命令行直接指定需求
python main.py "请创作一出诸葛亮和孙悟空的京剧"
```

### 完整数据管线（从零开始）

```bash
# Step 1: 数据处理（将原始剧本提取为结构化数据）
python scripts/data_processing/extract.py
python scripts/data_processing/process_with_model_batch.py

# Step 2: 构建 RAG 向量索引
python src/rag_system/main.py

# Step 3: 生成剧本（CrewAI 多Agent协作）
python main.py
```

---

## 示例输出

系统对"煮酒论英雄"剧目的生成结果（存储于 `generated_scripts/`）：

- `煮酒论英雄_大纲.json` — 剧情大纲与幕次规划
- `煮酒论英雄_场景设定.json` — 舞台场景、灯光、音效配置
- `煮酒论英雄_装扮设计.json` — 角色服装、头饰、道具设计
- `煮酒论英雄_剧本.txt` — 完整剧本（含唱词、念白、身段动作）
- `煮酒论英雄_评估报告.json` — 生成质量多维评估报告
- `煮酒论英雄_对话历史.json` — 完整对话历史记录

参考完整剧本示例：`example/煮酒论英雄_完整剧本(1).txt`

---

## 已支持角色

| 角色 | 行当 | 代表剧目数量 |
|------|------|-------------|
| 诸葛亮 | 老生 | 21 部 |
| 孙悟空 | 武生/猴戏 | 13 部 |
| 赵匡胤 | 老生 | 22 部 |

---

## 子项目：视频生成系统

`vedio_generation/` 目录为独立的下游视频生成子项目，接收本系统生成的剧本，自动化合成京剧表演视频。

详见 [`vedio_generation/README.md`](vedio_generation/README.md)

---

## 开发文档

详细的模块设计与改进记录见 `doc/` 目录：

- [`RAG改进总结.md`](doc/RAG改进总结.md) — 检索增强系统优化过程
- [`剧本格式改进说明.md`](doc/剧本格式改进说明.md) — 剧本格式规范与改进
- [`场景设定功能说明.md`](doc/场景设定功能说明.md) — 场景设定智能体设计
- [`目标1完成总结.md`](doc/目标1完成总结.md) — 数据提取阶段完成记录
- [`目标2完成总结.md`](doc/目标2完成总结.md) — RAG系统完成记录
- [`目标3完成总结.md`](doc/目标3完成总结.md) — 多智能体系统完成记录

---

## 技术栈

- **多Agent框架**：CrewAI
- **大语言模型**：OpenAI GPT-4 / DeepSeek（可配置）
- **向量检索**：FAISS（Facebook AI Similarity Search）
- **记忆系统**：滑动窗口短期记忆 + RAG 长期记忆
- **文本处理**：自定义京剧文本清洗与结构化管线
- **数据格式**：JSON（角色档案/场景配置）+ TXT（剧本正文）
