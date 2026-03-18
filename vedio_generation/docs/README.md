# 智能视频生成系统

基于导演Agent机制的智能京剧视频生成系统，支持质量评估、迭代优化和自动重试。

## 🎯 核心特性

### 1. 导演Agent评估机制
- 使用Gemini-2.5-pro模型对每个生成的视频进行多维度质量评估
- 评估维度：装扮准确性、动作质量、对话表达、场景一致性、整体印象
- 只有评分≥7.0的视频才会被接受
- 未通过的视频会获得具体改进建议，最多支持5次迭代优化

### 2. 智能迭代优化机制
- **保留基础信息**：场景设定和角色装扮在迭代中保持不变
- **应用改进建议**：根据导演评估反馈，精准改进表演部分
- **增量修改**：不是完全替换prompt，而是在原有基础上优化
- **质量保证**：避免迭代过程中信息丢失导致的质量下降

### 3. 智能Prompt构建
- 从`generated_scripts`自动提取场景设定、装扮设计、对话历史
- 动态构建完整prompt：通用描述 + 场景 + 装扮 + 表演 + 改进建议
- 支持迭代时保留基础信息，仅更新改进点

### 4. 智能生成流水线
- 逐个场景生成，每个视频立即评估
- 通过评估才继续下一个场景
- 支持自动重试机制（最多5次）
- 完整的生成报告和评估历史

---

## 📋 快速开始

### 前置要求

- Python 3.8+
- conda环境管理器
- 足够的磁盘空间（视频文件较大）

### 安装步骤

#### 1. 激活虚拟环境

```bash
conda activate llm
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `openai>=1.0.0` - OpenAI API客户端
- `requests>=2.31.0` - HTTP请求库
- `opencv-python>=4.8.0` - 视频处理
- `moviepy>=1.0.3` - 视频编辑
- `numpy>=1.24.0` - 数值计算

#### 3. 配置API密钥

创建 `config/api_config.py`：

```python
# 评估和Prompt优化API（Gemini）
API_KEY = "your-api-key-here"
API_BASE_URL = "https://api.openai.com/v1"

# 视频生成API（Sora）
VIDEO_API_KEY = "your-video-api-key-here"
VIDEO_API_BASE_URL = "https://api.zyai.online/v1"

# 模型配置
MODELS = {
    'evaluation': 'gemini-2.5-pro',  # 用于视频评估
    'video': 'sora-2'                 # 用于视频生成
}
```

### 使用方法

#### 方式1：使用智能流水线（推荐）

```bash
conda activate llm
python run_pipeline.py
```

智能流水线会：
1. 从`generated_scripts/`读取剧本数据
2. 提取prompt并构建完整描述
3. 逐个生成视频
4. 导演Agent评估每个视频
5. 不通过则迭代优化（最多5次）
6. 生成详细报告

#### 方式2：使用主程序

```bash
conda activate llm
python main.py
```

---

## 📁 项目结构

```
vedio_2/
├── config/                      # 配置文件
│   ├── api_config.py           # API配置（需创建）
│   └── settings.py             # 系统设置
│
├── src/                         # 源代码
│   ├── extractor/              # Prompt提取器
│   │   └── simple_prompt_extractor.py  # 从JSON提取prompt
│   │
│   ├── generator/              # 视频生成器
│   │   ├── prompt_builder.py  # Prompt构建
│   │   └── sora2_generator.py # Sora2 API调用
│   │
│   ├── evaluator/              # 质量评估器
│   │   └── director_agent.py  # 导演Agent评估
│   │
│   ├── pipeline/               # 流水线
│   │   └── intelligent_pipeline.py  # 智能生成流水线
│   │
│   ├── processor/              # 视频处理器
│   │   ├── video_editor.py    # 视频编辑
│   │   └── video_merger.py    # 视频合并
│   │
│   └── utils/                  # 工具模块
│       ├── logger.py          # 日志工具
│       └── file_manager.py    # 文件管理
│
├── generated_scripts/          # 剧本数据（输入）
│   ├── {剧本名}_对话历史.json
│   ├── {剧本名}_场景设定.json
│   ├── {剧本名}_装扮设计.json
│   └── {剧本名}_prompts_complete.json  # 提取的完整prompt
│
├── generated_videos/           # 生成的视频（输出）
│   └── output/                # 临时输出目录
│
├── results/                    # 最终结果
│   ├── videos/
│   │   ├── approved/          # 通过评估的视频
│   │   └── rejected/          # 未通过的视频
│   ├── reports/               # 评估报告
│   └── merged/                # 合并后的完整视频
│
├── tests/                      # 测试文件
│   ├── test_iteration_fix.py  # 迭代机制测试
│   └── test_system.py         # 系统功能测试
│
├── docs/                       # 文档
│   ├── README.md              # 本文档
│   ├── ARCHITECTURE.md        # 架构设计
│   ├── CHANGELOG.md           # 更新日志
│   └── ITERATION_FIX.md       # 迭代修复说明
│
├── main.py                     # 主程序入口
├── run_pipeline.py            # 流水线入口
└── requirements.txt           # 依赖列表
```

---

## 🔧 核心功能详解

### Prompt提取与构建

系统使用`simple_prompt_extractor.py`从剧本数据中提取信息：

```python
from src.extractor.simple_prompt_extractor import extract_prompts_simple

# 提取prompt
prompts = extract_prompts_simple("煮酒论英雄")

# 每个prompt包含：
# - prompt: 完整的生成指令
# - scene_desc: 场景描述（迭代时保持不变）
# - costume_desc: 装扮描述（迭代时保持不变）
# - emotion: 情感
# - content_text: 表演内容
```

**Prompt结构**：
```
1. 通用京剧描述（固定）
2. 场景设定（从场景设定.json，迭代中保持不变）
3. 角色装扮（从装扮设计.json，迭代中保持不变）
4. 表演内容（从对话历史.json）
5. 改进建议（迭代时添加）
```

### 导演Agent评估

```python
from src.evaluator.director_agent import DirectorAgent

director = DirectorAgent()

# 评估视频
passed, evaluation, improved_prompt = director.analyze_and_improve(
    video_url="http://example.com/video.mp4",
    original_prompt="原始prompt",
    expected_content={
        'character': '孙悟空',
        'emotion': '机敏活泼',
        'content_text': '表演内容'
    },
    scene_desc="场景描述",      # 保留基础信息
    costume_desc="装扮描述"     # 保留基础信息
)

# 返回：
# - passed: 是否通过（总分>=7.0）
# - evaluation: 详细评估结果
# - improved_prompt: 改进后的prompt（保留场景和装扮）
```

### 智能流水线

```python
from src.pipeline.intelligent_pipeline import IntelligentPipeline

pipeline = IntelligentPipeline(max_iterations=5)

# 运行流水线
report = pipeline.run("煮酒论英雄")

# 报告包含：
# - 总视频数
# - 通过/失败数量
# - 各场景详情
# - 迭代历史
```

---

## 🎬 使用示例

### 示例：生成京剧视频

假设你有以下剧本数据：

**generated_scripts/煮酒论英雄_对话历史.json**
```json
[
  {
    "character": "曹操",
    "content": "今天下英雄，唯使君与操耳！",
    "parsed": {
      "type": "念白",
      "emotion": "豪迈自信",
      "text": "今天下英雄，唯使君与操耳！"
    }
  }
]
```

**generated_scripts/煮酒论英雄_场景设定.json**
```json
{
  "1": {
    "scenery": "舞台中央布置一张方桌，两侧各置一椅...",
    "sound_effects": {
      "environment": "偶有风声、虫鸣声",
      "background_music": "轻柔的琵琶背景音乐"
    }
  }
}
```

**generated_scripts/煮酒论英雄_装扮设计.json**
```json
{
  "曹操": {
    "role_type": "净",
    "face_pattern": "白色脸谱，象征奸诈...",
    "costume": "蟒袍，龙纹华丽...",
    "overall_style": "威严霸气"
  }
}
```

运行：
```bash
conda activate llm
python run_pipeline.py
```

系统会：
1. 提取完整prompt（包含场景、装扮、表演）
2. 生成视频
3. 导演评估
4. 如果不通过，保留场景和装扮信息，应用改进建议重新生成
5. 最多迭代5次
6. 保存通过的视频到`results/videos/approved/`

---

## 🔍 迭代优化机制说明

### 问题背景

在早期版本中，迭代时会出现"视频越迭代越差"的问题。根本原因是采用了**完全替换prompt**的策略，导致场景和装扮等关键信息在迭代中丢失。

### 解决方案

新版本采用**"保留基础信息 + 应用改进建议"**策略：

**第1次生成（完整prompt）**：
```
Chinese Peking Opera performance...
Scene: 舞台中央布置一张方桌...
Character: 曹操 - 净 role type. Face: 白色脸谱...
Performance: 曹操 performs: 今天下英雄，唯使君与操耳！
```

**评估不通过，导演给出建议**：
- 动作质量：需要更流畅的手势动作
- 情感表达：需要更强的自信和霸气

**第2次生成（保留基础 + 改进）**：
```
Chinese Peking Opera performance...
Scene: 舞台中央布置一张方桌...        ← 完全保留
Character: 曹操 - 净 role type. Face: 白色脸谱...  ← 完全保留
Performance: 曹操 performs: 今天下英雄，唯使君与操耳！
Refinements: Add more fluid hand gestures; Emphasize confidence  ← 新增
```

### 关键改进

1. **场景设定始终保持**：舞台布置、音效等基础信息不会丢失
2. **角色装扮始终保持**：脸谱、服装等视觉信息不会丢失
3. **改进建议追加**：作为Refinements追加，不覆盖原有内容
4. **质量稳定提升**：每次迭代都是在完整上下文基础上的优化

详见：[ITERATION_FIX.md](ITERATION_FIX.md)

---

## 📊 评估标准

### 评分维度

| 维度 | 描述 | 分数范围 |
|------|------|----------|
| 装扮准确性 | 角色的装扮是否符合要求（脸谱、服装、配饰） | 0-10 |
| 动作质量 | 动作是否流畅自然，是否符合角色特点 | 0-10 |
| 对话表达 | 对话/唱段表达是否清晰，情感是否到位 | 0-10 |
| 场景一致性 | 场景设置是否合理，是否有不相关元素 | 0-10 |
| 整体印象 | 视频整体质量，是否达到专业水准 | 0-10 |

### 通过标准

- 总分（5个维度平均分）≥ 7.0
- 评分客观严格
- 7分以上代表专业水准

---

## 🚀 高级功能

### 自定义评估阈值

```python
pipeline = IntelligentPipeline(
    max_iterations=5,           # 最大迭代次数
)

director = DirectorAgent(
    pass_threshold=7.0          # 通过阈值
)
```

### 批量处理多个剧本

```python
scripts = ["煮酒论英雄", "三打白骨精", "空城计"]

for script_name in scripts:
    report = pipeline.run(script_name)
    print(f"{script_name} 生成完成")
```

---

## ❓ 常见问题

### Q1: 视频生成失败怎么办？
检查：
1. API密钥是否正确配置
2. 网络连接是否正常
3. prompt是否符合要求
4. 查看日志获取详细错误信息

### Q2: 如何提高视频通过率？
- 确保剧本数据完整（场景设定、装扮设计、对话历史）
- 使用清晰、具体的表演描述
- 适当调整评估阈值

### Q3: 迭代多次仍未通过怎么办？
- 查看`results/reports/`中的评估报告
- 分析具体哪个维度得分低
- 手动优化对应的剧本数据
- 重新运行流水线

### Q4: 如何查看生成进度？
- 查看控制台输出
- 查看`results/videos/`目录
- 查看生成报告

---

## 📝 更新日志

详见：[CHANGELOG.md](CHANGELOG.md)

### 最新更新（2025-11-24）

- ✅ 修复迭代机制中prompt信息丢失问题
- ✅ 实现"保留基础 + 应用改进"策略
- ✅ 场景和装扮信息在迭代中保持不变
- ✅ 改进建议作为Refinements追加
- ✅ 添加完整的测试验证

---

## 📖 相关文档

- [架构设计](ARCHITECTURE.md) - 系统架构和设计思想
- [更新日志](CHANGELOG.md) - 版本更新记录
- [迭代修复](ITERATION_FIX.md) - 迭代机制修复详情

---

## 📧 支持

如有问题，请查看：
1. 文档目录`docs/`
2. 测试示例`tests/`
3. 代码注释

---

**版本**: 2.1.0  
**最后更新**: 2025-11-24
