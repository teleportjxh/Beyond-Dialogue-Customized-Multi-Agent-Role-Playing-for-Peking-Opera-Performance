# 多Agent剧本生成系统

## 概述

本模块实现了基于多Agent协作的京剧剧本生成系统，通过模拟编剧、导演和演员之间的协作，生成具有京剧艺术特色的剧本。

## 系统架构

### 核心组件

1. **Agent基类** (`agent_base.py`)
   - 所有Agent的基础类
   - 封装LLM客户端和消息管理
   - 提供统一的消息处理接口

2. **上下文构建器** (`context_builder.py`)
   - 整合RAG检索和角色数据
   - 为不同Agent构建专属上下文
   - 从用户需求中提取角色信息

3. **编剧Agent** (`screenwriter_agent.py`)
   - 生成剧本大纲
   - 设计场景结构
   - 规划剧情发展

4. **演员Agent** (`actor_agent.py`)
   - 扮演特定角色
   - 生成符合角色性格的对话
   - 实时接收其他角色的对话（同步机制）
   - 输出格式：【情】情感 + 【念/唱/做/打】内容

5. **导演Agent** (`director_agent.py`)
   - 控制对话流程
   - 决定下一个说话角色
   - 评估场景质量
   - 判断场景是否继续

6. **对话管理器** (`dialogue_manager.py`)
   - 管理完整对话历史
   - 支持按场景、按角色查询
   - 提供格式化输出

7. **剧本格式化器** (`script_formatter.py`)
   - 将对话历史格式化为标准京剧剧本
   - 生成美观的剧本文档

## 工作流程

```
用户需求
    ↓
1. 提取角色（从需求中识别角色名称）
    ↓
2. 生成大纲（编剧Agent创建剧本结构）
    ↓
3. 初始化Agents（为每个角色创建演员Agent）
    ↓
4. 生成场景对话（多Agent协作）
    │
    ├─→ 演员Agent生成对话
    │       ↓
    ├─→ 同步给其他演员（实时通信）
    │       ↓
    ├─→ 导演Agent决定下一个说话者
    │       ↓
    └─→ 判断是否继续（循环直到场景结束）
    ↓
5. 格式化剧本（生成标准格式）
    ↓
6. 保存结果（剧本、大纲、对话历史）
```

## 关键特性

### 1. 实时同步机制

演员Agent每说一句话，都会立即同步给其他演员：

```python
# 演员A生成对话
dialogue_data = actor_a.generate_dialogue(...)

# 立即同步给演员B
actor_b.receive_other_dialogue(dialogue_data)
```

### 2. RAG增强

- 根据用户需求检索相关场景片段
- 为Agent提供丰富的上下文信息
- 提升生成内容的京剧特色

### 3. 角色数据整合

- 加载角色profile.json（基本信息）
- 加载角色data.json（详细数据）
- 确保生成内容符合角色性格

### 4. 京剧艺术风格

- 唱念做打四功
- 文言文表达
- 情感标注
- 舞台指示

## 使用方法

### 基本使用

```python
from src.script_generation.main import ScriptGenerationSystem

# 初始化系统
system = ScriptGenerationSystem(
    character_dir="character",
    character_data_dir="character_data",
    vector_index_dir="vector_index",
    output_dir="generated_scripts"
)

# 生成剧本
result = system.generate_script(
    user_request="诸葛亮和孙悟空煮酒论英雄",
    max_scenes=3,
    max_rounds_per_scene=10
)

# 查看结果
print(f"剧本文件：{result['output_files']['script']}")
print(f"大纲文件：{result['output_files']['outline']}")
print(f"对话历史：{result['output_files']['dialogue']}")
```

### 命令行运行

```bash
# 运行示例
cd h:/pythonwork/project/extract
python -m src.script_generation.main
```

## 输出文件

生成的文件保存在 `generated_scripts/` 目录：

1. **{剧名}_剧本.txt** - 格式化的完整剧本
2. **{剧名}_大纲.json** - 剧本大纲（JSON格式）
3. **{剧名}_对话历史.json** - 完整对话历史（JSON格式）

## 剧本格式示例

```
╔══════════════════════════════════════════════════════════════╗
║                        京剧剧本                              ║
╚══════════════════════════════════════════════════════════════╝

剧名：煮酒论英雄
主题：智慧与勇武的对话
创作时间：2025年11月11日 16:00

═══════════════════════════════════════════════════════════════

【角色表】
• 诸葛亮（智者）：蜀汉丞相，智谋超群
• 孙悟空（英雄）：齐天大圣，神通广大

═══════════════════════════════════════════════════════════════

【第1场】
────────────────────────────────────────────────────────────

〔场景〕丞相府内，夜色深沉
〔说明〕诸葛亮与孙悟空对坐，煮酒论天下

诸葛亮【沉思】：
    【念】今夜月明星稀，正是论英雄之时...

孙悟空【豪迈】：
    〔拱手作揖〕
    【念】俺老孙虽是山野之猴，却也知天下大势...

═══════════════════════════════════════════════════════════════

【剧终】
```

## 配置说明

### 环境变量

系统使用 `src/config.py` 中的配置：

```python
OPENAI_API_KEY = "your-api-key"
OPENAI_API_BASE = "https://api.openai.com/v1"
MODEL_NAME = "gpt-4"
```

### 参数调整

- `max_scenes`: 最大场景数（默认3）
- `max_rounds_per_scene`: 每场景最大对话轮数（默认10）
- `temperature`: LLM温度参数（在各Agent中可调整）

## 依赖项

```
langchain
langchain-openai
faiss-cpu
numpy
```

## 注意事项

1. **API密钥**：确保在 `src/config.py` 中配置了有效的OpenAI API密钥
2. **数据准备**：需要先运行目标1和目标2，生成角色数据和向量索引
3. **角色识别**：用户需求中必须包含已有的角色名称（如"诸葛亮"、"孙悟空"）
4. **生成时间**：根据场景数和对话轮数，生成可能需要几分钟
5. **成本控制**：每次生成会调用多次LLM API，注意控制成本

## 扩展开发

### 添加新Agent类型

1. 继承 `AgentBase` 类
2. 实现特定的系统提示
3. 添加专属方法
4. 在 `main.py` 中集成

### 自定义输出格式

修改 `script_formatter.py` 中的模板和格式化方法。

### 调整对话策略

修改 `director_agent.py` 中的决策逻辑。

## 故障排除

### 常见问题

1. **角色未识别**
   - 检查角色名称是否在 `character/` 目录中存在
   - 确保用户需求中包含完整的角色名称

2. **API调用失败**
   - 检查API密钥是否正确
   - 检查网络连接
   - 查看API配额是否充足

3. **生成内容不符合预期**
   - 调整各Agent的系统提示
   - 增加RAG检索的相关片段数量
   - 调整temperature参数

4. **向量索引加载失败**
   - 确保已运行目标2生成向量索引
   - 检查 `vector_index/` 目录是否存在

## 版本历史

- v1.0 (2025-11-11): 初始版本，实现多Agent协作剧本生成

## 作者

京剧剧本生成项目团队
