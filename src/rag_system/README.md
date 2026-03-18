# RAG检索系统完整文档

## 系统概述

RAG（Retrieval-Augmented Generation）系统通过语义检索技术，从已有的京剧剧本数据中检索相关场景，为多agent剧本生成系统提供上下文增强。

### 数据来源
- **数据源**: `enhanced_script/角色名/*.txt`
- **提取方式**: 按场景分段（识别【第X场】标记）
- **文档类型**: outline（剧情大纲）、scene（场景片段）、full_script（完整剧本）

### 核心特性

- **语义检索**：基于OpenAI Embedding模型的语义相似度匹配，而非关键词匹配
- **智能意图识别**：自动识别查询中的角色和场景关键词
- **多角色联合检索**：支持多个角色的联合场景检索
- **场景上下文增强**：将检索结果格式化为适合剧本生成的上下文
- **轻量级向量数据库**：使用FAISS实现高效的向量检索

### 当前索引状态
- **总文档数**: 124个场景片段
- **角色数**: 2个（孙悟空、诸葛亮）
- **剧本数**: 34个
  - 孙悟空: 13个剧本，57个场景
  - 诸葛亮: 21个剧本，67个场景

## 系统架构

```
src/rag_system/
├── __init__.py              # 模块初始化
├── vector_processor.py      # 向量化处理器
├── vector_store.py          # 向量数据库管理
├── semantic_retriever.py    # 语义检索器
├── scene_enhancer.py        # 场景增强器
├── main.py                  # 主入口和CLI
└── README.md                # 本文档
```

### 模块说明

#### 1. VectorProcessor（向量化处理器）
- 从enhanced_script目录加载剧本txt文件
- 按场景分段提取文本内容
- 调用OpenAI Embedding API进行向量化
- 批量处理以提高效率（batch_size=50）

#### 2. VectorStoreManager（向量数据库管理器）
- 使用FAISS创建和管理向量索引
- 支持索引的保存和加载
- 提供多种搜索策略（基础搜索、按角色搜索、按类型搜索）
- 索引统计和重建功能

#### 3. SemanticRetriever（语义检索器）
- 智能查询意图识别
- 从查询中提取角色名称和场景关键词
- 多角色联合检索
- 相似场景检索
- 角色上下文获取

#### 4. SceneEnhancer（场景增强器）
- 格式化检索结果为可读文本
- 生成多agent系统所需的上下文提示
- 为特定角色agent准备专属上下文
- 提取关键元素用于决策

#### 5. RAGSystem（主系统类）
- 整合所有功能模块
- 提供统一的API接口
- 命令行工具支持

## 安装依赖

```bash
pip install langchain-openai faiss-cpu numpy
```

## 使用方法

### 1. 构建向量索引

首次使用需要构建向量索引：

```bash
python -m src.rag_system.main build
```

强制重建索引：

```bash
python -m src.rag_system.main build --rebuild
```

**输出示例**:
```
============================================================
开始构建RAG向量索引...
============================================================

步骤1: 加载和处理角色数据...
找到 2 个角色目录

处理角色: 孙悟空
  找到 13 个剧本文件
    金钱豹: 提取 14 个场景
    ...

总共提取了 124 个文档片段

步骤2: 创建向量索引...
步骤3: 保存索引到 vector_index...

============================================================
索引构建完成！
============================================================
```

### 2. 语义搜索

搜索相关场景：

```bash
# 基本搜索
python -m src.rag_system.main search "诸葛亮舌战群儒"

# 指定返回结果数量
python -m src.rag_system.main search "孙悟空大战妖怪" --top-k 10

# 保存结果到文件
python -m src.rag_system.main search "诸葛亮的智谋" --output results.json
```

**搜索示例1**: 诸葛亮舌战群儒
```bash
python -m src.rag_system.main search "诸葛亮舌战群儒" --top-k 3
```

**输出**:
```
============================================================
查询: 诸葛亮舌战群儒
============================================================

识别到的角色: 诸葛亮
提取的关键词: 无
找到 3 个相关结果

结果 1:
  剧本: 舌战群儒
  角色: 诸葛亮
  类型: outline
  相似度: 0.515
  内容预览: 好的，遵照您的指示，我将严格依据您提供的视频内容...

结果 2:
  剧本: 定军山
  角色: 诸葛亮
  类型: scene
  相似度: 0.496
  内容预览: 【第十四场】...

结果 3:
  剧本: 骂王朗
  角色: 诸葛亮
  类型: scene
  相似度: 0.484
  内容预览: 【第一场】...
```

**搜索示例2**: 孙悟空大战妖怪
```bash
python -m src.rag_system.main search "孙悟空大战妖怪" --top-k 3
```

**输出**:
```
结果 1:
  剧本: 芭蕉扇
  角色: 孙悟空
  类型: scene
  相似度: 0.574

结果 2:
  剧本: 金钱豹
  角色: 孙悟空
  类型: scene
  相似度: 0.557

结果 3:
  剧本: 金钱豹
  角色: 孙悟空
  类型: scene
  相似度: 0.532
```

### 3. 场景增强

生成用于剧本生成的增强上下文：

```bash
# 基本增强
python -m src.rag_system.main enhance "诸葛亮和孙悟空煮酒论英雄"

# 保存增强上下文
python -m src.rag_system.main enhance "诸葛亮和孙悟空煮酒论英雄" --output context.json
```

**输出示例**:
```
============================================================
生成场景增强上下文...
============================================================

生成的上下文提示:
------------------------------------------------------------
# 剧本生成上下文

## 用户需求
诸葛亮与孙悟空相遇

## 涉及角色
孙悟空, 诸葛亮

# 角色背景参考
...

## 使用说明
请基于以上参考内容，保持京剧艺术风格，生成符合角色特点的新剧本。
------------------------------------------------------------
```

### 4. 交互式搜索

进入交互式搜索模式：

```bash
python -m src.rag_system.main interactive
```

**交互示例**:
```
============================================================
RAG交互式搜索模式
============================================================
输入查询内容，输入 'quit' 或 'exit' 退出
输入 'enhance' 进入场景增强模式
------------------------------------------------------------

请输入查询: 诸葛亮舌战群儒
[显示搜索结果...]

请输入查询: 孙悟空大战妖怪
[显示搜索结果...]

请输入查询: enhance
请输入场景描述: 诸葛亮与孙悟空相遇
[显示增强上下文...]

请输入查询: quit
退出交互模式
```

### 5. 高级用法

#### 自定义索引路径
```bash
python -m src.rag_system.main build --index-path custom_index
python -m src.rag_system.main search "查询内容" --index-path custom_index
```

#### 批量查询
创建查询文件`queries.txt`:
```
诸葛亮舌战群儒
孙悟空大战妖怪
空城计
```

执行批量查询:
```bash
cat queries.txt | while read query; do
    echo "查询: $query"
    python -m src.rag_system.main search "$query" --top-k 3
    echo "---"
done
```

## Python API使用

### 基础使用

```python
from src.rag_system.main import RAGSystem

# 创建RAG系统实例
rag = RAGSystem(index_path="vector_index")

# 构建索引（首次使用）
rag.build_index()

# 执行搜索
results = rag.search("诸葛亮和孙悟空的对话", top_k=5)

# 场景增强
enhanced_context = rag.enhance_scene("诸葛亮和孙悟空煮酒论英雄")
```

### 高级使用

```python
from src.rag_system import (
    VectorProcessor,
    VectorStoreManager,
    SemanticRetriever,
    SceneEnhancer
)

# 1. 向量化处理
processor = VectorProcessor()
vectorized_docs = processor.process_all_characters()

# 2. 创建向量索引
vector_store = VectorStoreManager(dimension=1536)
vector_store.create_index(vectorized_docs)
vector_store.save_index("my_index")

# 3. 语义检索
retriever = SemanticRetriever(vector_store)

# 智能检索
results = retriever.smart_retrieve(
    query="诸葛亮和孙悟空煮酒论英雄",
    top_k_per_character=3,
    min_similarity=0.3
)

# 多角色场景检索
scenes = retriever.retrieve_multi_character_scenes(
    characters=["诸葛亮", "孙悟空"],
    scene_description="煮酒论英雄",
    top_k=5
)

# 获取角色上下文
context = retriever.get_character_context("诸葛亮", top_k=10)

# 4. 场景增强
enhancer = SceneEnhancer()

# 增强场景上下文
enhanced = enhancer.enhance_scene_context(
    query="诸葛亮和孙悟空煮酒论英雄",
    retrieval_results=results
)

# 生成上下文提示
prompt = enhancer.generate_context_prompt(enhanced)

# 为特定角色生成上下文
agent_context = enhancer.format_for_agent("诸葛亮", enhanced)
```

## 数据格式

### 输入数据

系统从以下位置读取数据：
- `enhanced_script/{角色名}/*.txt`：角色的剧本文件

### 文档类型
- **outline**: 剧情大纲，包含整个剧本的故事概要
- **scene**: 场景片段，包含完整的一场戏
- **full_script**: 完整剧本（当剧本没有场景分段时）

### 输出格式

#### 搜索结果

```json
{
  "query": "诸葛亮和孙悟空的对话",
  "characters": ["诸葛亮", "孙悟空"],
  "keywords": ["对话"],
  "results_by_character": {
    "诸葛亮": [...],
    "孙悟空": [...]
  },
  "combined_results": [
    {
      "id": "doc_0",
      "character": "诸葛亮",
      "title": "空城计",
      "script_id": "01001001",
      "type": "scene",
      "text": "【第一场】...",
      "metadata": {
        "character_name": "诸葛亮",
        "script_id": "01001001",
        "script_name": "空城计",
        "scene_number": 1,
        "scene_name": "第一场",
        "type": "scene"
      },
      "similarity_score": 0.85,
      "vector": [...]
    }
  ],
  "total_results": 10
}
```

#### 增强上下文

```json
{
  "query": "诸葛亮和孙悟空煮酒论英雄",
  "characters": ["诸葛亮", "孙悟空"],
  "character_contexts": {
    "诸葛亮": "## 诸葛亮角色参考\n...",
    "孙悟空": "## 孙悟空角色参考\n..."
  },
  "dialogue_context": "## 相关对话参考\n...",
  "performance_context": "## 相关表演参考\n...",
  "total_references": 15,
  "raw_results": [...]
}
```

### 元数据字段
每个检索结果包含以下元数据:
```json
{
  "id": "doc_0",
  "character": "孙悟空",
  "title": "金钱豹",
  "script_id": "01013014",
  "type": "scene",
  "text": "【第一场】...",
  "metadata": {
    "character_name": "孙悟空",
    "script_id": "01013014",
    "script_name": "金钱豹",
    "scene_number": 1,
    "scene_name": "第一场",
    "type": "scene"
  },
  "similarity_score": 0.574,
  "distance": 0.742,
  "rank": 1
}
```

## 配置说明

系统配置在 `src/config.py` 中：

```python
class Config:
    # API配置
    API_KEY = "your-api-key"
    BASE_URL = "https://api.openai.com/v1"
    MODEL_NAME = "gpt-4"
    
    # 数据路径
    ENHANCED_SCRIPT_PATH = "./enhanced_script"
    CHARACTER_DATA_DIR = "character_data"
    CHARACTER_DIR = "character"
    
    # Embedding配置
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSION = 1536
```

## 工作流程

### 索引构建流程

```
1. 扫描enhanced_script目录
   ↓
2. 解析剧本txt文件
   ↓
3. 按场景分段提取文本
   ↓
4. 调用OpenAI Embedding API向量化
   ↓
5. 创建FAISS索引
   ↓
6. 保存索引到磁盘
```

### 检索流程

```
1. 接收用户查询
   ↓
2. 提取角色名称和关键词
   ↓
3. 查询向量化
   ↓
4. FAISS相似度搜索
   ↓
5. 结果排序和过滤
   ↓
6. 返回Top-K结果
```

### 场景增强流程

```
1. 执行语义检索
   ↓
2. 按角色和类型分组结果
   ↓
3. 格式化为可读文本
   ↓
4. 生成上下文提示
   ↓
5. 为每个角色准备专属上下文
```

## 检索结果说明

### 相似度分数
- 范围: 0.0 - 1.0
- 越接近1.0表示相似度越高
- 通常0.5以上表示较强相关性

### 支持的查询方式
- 角色名查询: "诸葛亮"、"孙悟空"
- 剧本名查询: "舌战群儒"、"空城计"
- 情节查询: "大战妖怪"、"智斗"
- 组合查询: "诸葛亮舌战群儒"

## 性能优化

1. **批量向量化**：减少API调用次数（batch_size=50）
2. **索引持久化**：避免重复构建
3. **FAISS优化**：使用IndexFlatL2实现快速检索
4. **结果缓存**：避免重复计算

### 性能优化建议

#### 1. 批量处理
向量化时使用批处理（默认batch_size=50），可以减少API调用次数。

#### 2. 缓存索引
索引构建后会保存到磁盘，后续查询直接加载，无需重新构建。

#### 3. 合理设置top_k
- 快速查询: top_k=3-5
- 全面检索: top_k=10-20
- 过大的top_k会影响性能

## 与多Agent系统集成

RAG系统为多agent剧本生成系统提供以下支持：

1. **角色上下文**：为每个角色agent提供其历史表演参考
2. **场景参考**：提供相似场景的对话和表演示例
3. **风格指导**：通过检索结果保持京剧艺术风格
4. **动态增强**：根据生成过程动态检索相关内容

### 集成示例

```python
from src.rag_system.main import RAGSystem

# 初始化RAG系统
rag = RAGSystem()
rag.load_index()

# 为剧本生成准备上下文
user_request = "诸葛亮和孙悟空煮酒论英雄"
enhanced_context = rag.enhance_scene(user_request)

# 为每个角色agent准备专属上下文
from src.rag_system.scene_enhancer import SceneEnhancer
enhancer = SceneEnhancer()

zhuge_context = enhancer.format_for_agent("诸葛亮", enhanced_context)
wukong_context = enhancer.format_for_agent("孙悟空", enhanced_context)

# 将上下文传递给agent系统
# agent_system.set_context("诸葛亮", zhuge_context)
# agent_system.set_context("孙悟空", wukong_context)
```

## 常见问题

### Q1: 索引构建需要多长时间？
A: 取决于数据量和网络速度。对于两个角色约34个剧本，通常需要2-5分钟。

### Q2: 如何提高检索准确性？
A: 
1. 使用更具体的查询描述
2. 调整min_similarity阈值
3. 增加top_k值获取更多结果

### Q3: 索引文件存储在哪里？
A: 默认存储在项目根目录的 `vector_index` 文件夹中。

### Q4: 如何更新索引？
A: 当添加新的剧本文件后，运行：
```bash
python -m src.rag_system.main build --rebuild
```

### Q5: 检索结果不准确怎么办？
A: 
1. 尝试更具体的查询词
2. 增加返回结果数量 `--top-k 10`
3. 检查剧本文件是否正确放置在`enhanced_script`目录

### Q6: 如何查看索引统计信息？
A: 构建索引时会自动显示统计信息，或者查看`vector_index/documents.json`文件。

## 技术栈

- **LangChain**: OpenAI Embedding集成
- **FAISS**: 向量相似度搜索
- **NumPy**: 数值计算
- **Python 3.8+**: 开发语言

### 技术细节

#### 向量化模型
- 模型: OpenAI text-embedding-3-small
- 维度: 1536
- 距离度量: L2距离（欧氏距离）

#### 向量数据库
- 引擎: FAISS (Facebook AI Similarity Search)
- 索引类型: IndexFlatL2（精确搜索）
- 存储格式: 
  - `vector_index/faiss.index` - FAISS索引文件
  - `vector_index/documents.json` - 文档元数据

#### 场景提取规则
1. 使用正则表达式 `【第[一二三四五六七八九十百]+[场幕]】` 识别场景标记
2. 第一个场景之前的内容作为剧情大纲（如果长度>50字符）
3. 每个场景包含从场景标记到下一个场景标记之间的所有内容
4. 如果没有场景标记，整个剧本作为一个文档

## 后续优化方向

1. 支持更多Embedding模型
2. 实现混合检索（语义+关键词）
3. 添加检索结果重排序
4. 支持增量索引更新
5. 实现分布式向量检索
6. 优化场景分段策略
7. 增强元数据提取
8. 添加性能监控

## 许可证

本项目为内部使用，未开源。
