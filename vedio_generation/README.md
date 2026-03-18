# 智能视频生成系统

基于导演Agent机制的智能京剧视频生成系统，支持质量评估、迭代优化和自动重试。

## ✨ 特性亮点

- 🎭 **智能评估**：导演Agent多维度评估视频质量
- 🔄 **迭代优化**：自动改进prompt，保留场景和装扮信息
- 📊 **质量保证**：只有高质量视频（≥7分）才会通过
- 🎬 **京剧专注**：专门优化的京剧视频生成流程

## 🚀 快速开始

```bash
# 1. 激活环境
conda activate llm

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥（编辑 config/api_config.py）

# 4. 运行流水线
python run_pipeline.py
```

## 📁 项目结构

```
vedio_2/
├── config/              # 配置文件
├── src/                 # 源代码
│   ├── extractor/      # Prompt提取器
│   ├── evaluator/      # 导演Agent评估
│   ├── generator/      # 视频生成器
│   ├── pipeline/       # 智能流水线
│   ├── processor/      # 视频处理器
│   └── utils/          # 工具模块
├── generated_scripts/   # 输入：剧本数据
├── generated_videos/    # 输出：生成的视频
├── results/            # 最终结果
├── tests/              # 测试文件
└── docs/               # 详细文档
```

## 📊 工作流程

```
加载剧本 → 提取Prompt → 生成视频 → 导演评估
                                        ↓
                  ← 改进建议 ← 未通过（<7分）
                  ↓
            重新生成（保留场景和装扮）
                  ↓
            通过（≥7分）→ 保存到approved/
```

## 🎯 核心功能

### 1. 导演Agent评估

- 装扮准确性
- 动作质量
- 对话表达
- 场景一致性
- 整体印象

### 2. 智能迭代优化

- ✅ 保留场景设定
- ✅ 保留角色装扮
- ✅ 应用改进建议
- ✅ 质量稳定提升

### 3. 完整的数据流

输入数据（generated_scripts/）：
- `{剧本名}_对话历史.json`
- `{剧本名}_场景设定.json`
- `{剧本名}_装扮设计.json`

输出结果（results/）：
- `videos/approved/` - 通过的视频
- `videos/rejected/` - 未通过的视频
- `reports/` - 评估报告
- `merged/` - 合并后的完整视频

## 📖 文档

详细文档位于 `docs/` 目录：

- **[README.md](docs/README.md)** - 完整使用指南
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - 架构设计
- **[CHANGELOG.md](docs/CHANGELOG.md)** - 更新日志
- **[ITERATION_FIX.md](docs/ITERATION_FIX.md)** - 迭代修复说明

## 🧪 测试

```bash
conda activate llm

# 测试迭代机制
python tests/test_iteration_fix.py

# 测试系统功能
python tests/test_system.py
```

详见：[tests/README.md](tests/README.md)

## 📝 使用示例

```python
from src.pipeline.intelligent_pipeline import IntelligentPipeline

# 创建流水线
pipeline = IntelligentPipeline(max_iterations=5)

# 运行生成
report = pipeline.run("煮酒论英雄")

# 查看结果
print(f"通过: {report['summary']['passed']}")
print(f"失败: {report['summary']['failed']}")
```

## ⚙️ 配置

在 `config/api_config.py` 中配置：

```python
# 评估API（Gemini）
API_KEY = "your-api-key"
API_BASE_URL = "https://api.openai.com/v1"

# 视频生成API（Sora）
VIDEO_API_KEY = "your-video-api-key"
VIDEO_API_BASE_URL = "https://api.zyai.online/v1"

# 模型配置
MODELS = {
    'evaluation': 'gemini-2.5-pro',
    'video': 'sora-2'
}
```

## 🔍 故障排除

### API密钥错误
检查 `config/api_config.py` 配置

### 剧本数据加载失败
确保 `generated_scripts/{剧本名}/` 包含所需JSON文件

### 视频生成失败
查看日志文件和网络连接

详见文档的常见问题部分。

## 📈 最新更新 (v2.1.0)

- ✅ 修复迭代机制中prompt信息丢失问题
- ✅ 实现"保留基础 + 应用改进"策略
- ✅ 场景和装扮信息在迭代中保持不变
- ✅ 整合和简化文档结构
- ✅ 统一测试文件组织

详见：[CHANGELOG.md](docs/CHANGELOG.md)

## 📄 许可证

MIT License

---

**版本**: 2.1.0  
**最后更新**: 2025-11-24

需要帮助？查看 [完整文档](docs/README.md) 或提交 Issue。
