# 多Agent剧本生成系统（已重构为 CrewAI 架构）

> ⚠️ **注意**：本目录为旧版多Agent剧本生成模块。系统已重构为基于 **CrewAI** 框架的新架构，核心代码已迁移至以下目录：
>
> - `src/agents/` — Agent 定义层
> - `src/tools/` — Tool 工具层
> - `src/memory/` — 记忆系统
> - `src/crew/` — CrewAI 编排层

---

## 新架构概述

### 从旧架构到 CrewAI

| 维度 | 旧架构 | 新架构（CrewAI） |
|------|--------|-----------------|
| **框架** | 自研提示词工程 | CrewAI 多Agent框架 |
| **Agent 定义** | 继承 `AgentBase` 类 | CrewAI `Agent`（role/goal/backstory） |
| **任务分配** | 硬编码流程 | CrewAI `Task` 驱动 |
| **工具调用** | 内嵌在 Agent 方法中 | CrewAI `BaseTool` 独立封装 |
| **记忆系统** | 无 | 滑动窗口短期记忆 + RAG 长期记忆 |
| **审查机制** | 导演单层审查 | 编剧审查设计 + 演员自审 + 导演审查 |

### 新架构核心组件

#### 1. Agent 层 (`src/agents/`)

| Agent | 文件 | 职责 |
|-------|------|------|
| 编剧 Agent | `screenwriter.py` | 创作大纲、审查服装/场景设计、规划演员行动 |
| 服装设计 Agent | `costume_designer.py` | 设计角色服装和脸谱方案 |
| 场景设计 Agent | `scene_designer.py` | 设计舞台布景和音效方案 |
| 演员 Agent | `actor.py` | 扮演特定角色，生成对话，自我审查 |
| 导演 Agent | `director.py` | 控制对话流程，审查表演，最终评估 |

每个 Agent 通过 CrewAI 的 `Agent` 类创建，拥有：
- **role**：角色名称（如"京剧编剧"）
- **goal**：工作目标
- **backstory**：详细的角色背景和工作原则
- **tools**：可调用的工具列表
- **memory**：启用 CrewAI 内置记忆

#### 2. Tool 层 (`src/tools/`)

将原来内嵌在 Agent 中的功能抽取为独立的 CrewAI Tool：

| 工具 | 文件 | 功能 |
|------|------|------|
| `RAGSearchTool` | `rag_tools.py` | 语义检索历史京剧知识 |
| `CharacterSceneRetrieveTool` | `rag_tools.py` | 检索角色相关场景片段 |
| `LoadCharacterProfileTool` | `character_tools.py` | 加载角色档案 |
| `LoadCharacterDataTool` | `character_tools.py` | 加载角色详细数据 |
| `ExtractCharactersTool` | `character_tools.py` | 从用户输入提取角色名 |
| `ParseJSONTool` | `script_tools.py` | 从 LLM 输出提取 JSON |
| `FormatScriptTool` | `script_tools.py` | 格式化京剧剧本 |

所有工具继承自 `crewai.tools.BaseTool`，实现 `_run()` 方法。

#### 3. Memory 层 (`src/memory/`)

双层记忆系统：

- **`SlidingWindowMemory`**（短期记忆）
  - 保留最近 N 条消息（默认 10 条）
  - 超出窗口的消息自动压缩为摘要
  - 支持按角色过滤、获取上下文字符串

- **`RAGLongTermMemory`**（长期记忆）
  - 基于现有 FAISS 向量索引
  - 支持语义检索和文本匹配两种模式
  - 提供角色知识摘要接口

#### 4. Crew 层 (`src/crew/`)

- **`tasks.py`**：定义所有 Task 模板（大纲、服装设计、场景设计、行动规划、对话生成、审查、评估等）
- **`opera_crew.py`**：`PekingOperaCrew` 主编排类，实现 4 阶段创作流程

### 创作流程（4 Phase Pipeline）

```
Phase 1: 大纲创作
  编剧 Agent → 提取角色 → 加载档案 → 创作大纲

Phase 2: 设计阶段
  2a. 服装设计 Agent → 编剧审查 → (修改)
  2b. 场景设计 Agent → 编剧审查 → (修改)

Phase 3: 对话生成（逐场景循环）
  编剧规划行动 → 导演选择说话者 →
  演员生成对话(含自审) → 导演审查 → (修改) →
  更新短期记忆 → 下一轮

Phase 4: 最终评估
  导演 Agent → 多维度评分 → 评估报告
```

---

## 旧版模块文件说明

以下文件为旧版实现，保留供参考：

| 文件 | 说明 | 新版对应 |
|------|------|----------|
| `agent_base.py` | Agent 基类 | `src/agents/*.py`（CrewAI Agent） |
| `director_agent.py` | 导演 Agent | `src/agents/director.py` |
| `screenwriter_agent.py` | 编剧 Agent | `src/agents/screenwriter.py` |
| `actor_agent.py` | 演员 Agent | `src/agents/actor.py` |
| `costume_designer_agent.py` | 服装设计 Agent | `src/agents/costume_designer.py` |
| `scene_setting_agent.py` | 场景设定 Agent | `src/agents/scene_designer.py` |
| `dialogue_manager.py` | 对话管理器 | `src/memory/sliding_window_memory.py` |
| `context_builder.py` | 上下文构建器 | `src/tools/character_tools.py` + `src/tools/rag_tools.py` |
| `script_formatter.py` | 剧本格式化 | `src/tools/script_tools.py` |
| `main.py` | 旧版入口 | `src/crew/opera_crew.py` + 根目录 `main.py` |

---

## 使用方法（新版）

### 基本使用

```python
from src.crew.opera_crew import PekingOperaCrew

# 初始化 Crew
crew = PekingOperaCrew()

# 执行完整创作流程
result = crew.run("请创作一出诸葛亮和孙悟空的京剧")

# 查看结果
print(result['outline'])       # 大纲
print(result['costume_design']) # 服装设计
print(result['scene_design'])   # 场景设计
print(result['dialogues'])      # 对话历史
print(result['evaluation'])     # 评估报告
```

### 命令行运行

```bash
# 交互式
python main.py

# 直接指定需求
python main.py "请创作一出诸葛亮和孙悟空的京剧"
```

---

## 依赖项

```
crewai
crewai-tools
openai
faiss-cpu
numpy
```

---

## 版本历史

- **v2.0** (2025-03): 重构为 CrewAI 架构，新增 Tool 层、双层记忆系统、编剧审查机制、演员自审机制
- **v1.0** (2025-11): 初始版本，自研多Agent协作剧本生成
