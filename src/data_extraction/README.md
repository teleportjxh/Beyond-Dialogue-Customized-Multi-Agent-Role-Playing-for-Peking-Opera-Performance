# 京剧角色数据提取模块

## 模块概述

本模块用于从京剧剧本文本中提取角色信息和表演数据，使用大语言模型（LLM）进行智能解析和结构化。

### 主要功能

1. **角色信息提取**：从剧本中提取角色的基本信息（姓名、性别、年龄、性格等）
2. **对话数据提取**：提取角色之间的对话内容，包括上下文和情感
3. **表演数据提取**：提取角色的表演动作、唱段等内容
4. **数据验证与清洗**：自动验证JSON格式，清理无效数据
5. **错误处理**：保存解析失败的JSON到错误目录，便于调试

## 目录结构

```
src/data_extraction/
├── __init__.py           # 模块初始化，导出主要类
├── main.py              # 主入口文件，提供命令行接口
├── config.py            # 配置文件（位于src/目录）
├── data_models.py       # 数据模板定义
├── llm_client.py        # LLM客户端封装
├── utils.py             # 工具函数集合
├── extractor.py         # 核心提取器实现
└── README.md            # 本文档
```

## 使用方法

### 1. 环境准备

确保已安装必要的依赖：
```bash
pip install langchain-openai
```

### 2. 配置设置

在 `src/config.py` 中配置以下参数：

```python
class Config:
    # API配置
    API_KEY = "your-api-key"
    BASE_URL = "https://api.shubiaobiao.cn/v1/"
    MODEL_NAME = "gpt-4o"
    
    # 路径配置
    ENHANCED_SCRIPT_PATH = "./jingju/enhanced_script"  # 剧本输入路径
    CHARACTER_PATH = "./jingju/character"              # 角色信息输出路径
    CHARACTER_DATA_PATH = "./jingju/character_data"    # 角色数据输出路径
    ERROR_JSON_DIR = "./jingju/error_json"             # 错误JSON保存路径
    
    # 提取参数
    EXTRACT_TEMPERATURE = 0.1  # 提取时的温度参数
    JUDGE_TEMPERATURE = 0.0    # 判断时的温度参数
    MAX_TOKENS = 5000          # 最大token数
```

### 3. 运行提取

在项目根目录下运行：

```bash
python src/data_extraction/main.py
```

或者在Python代码中使用：

```python
from src.data_extraction import CharacterDataExtractor

# 创建提取器
extractor = CharacterDataExtractor()

# 执行提取
extractor.process_all_characters()
```

### 4. 输出结果

提取完成后，会在以下目录生成数据：

- `jingju/character/{角色名}/profile.json` - 角色基本信息
- `jingju/character_data/{角色名}/data.json` - 角色对话和表演数据
- `jingju/error_json/` - 解析失败的JSON（如果有）

## 代码架构

### 1. 配置管理 (config.py)

集中管理所有配置参数，包括API配置、路径配置和提取参数。

**关键配置项**：
- `API_KEY`, `BASE_URL`: LLM API配置
- `ENHANCED_SCRIPT_PATH`: 剧本文件路径
- `CHARACTER_PATH`, `CHARACTER_DATA_PATH`: 输出路径
- `SCRIPT_CONTENT_LIMIT`: 单次处理的剧本内容长度限制
- `MIN_PERFORMANCE_LENGTH`: 最小表演文本长度
- `MIN_DIALOGUE_GROUP_SIZE`: 最小对话组大小

### 2. 数据模型 (data_models.py)

定义所有数据模板，确保数据结构的一致性。

**主要模板**：
- `PERSON_SCRIPT_DATA_TEMPLATE`: 单个剧本的角色信息模板
- `UNIVERSAL_INFO_TEMPLATE`: 通用角色信息模板
- `PERSON_TEMPLATE`: 完整角色信息模板
- `DIALOGUE_DATA_TEMPLATE`: 对话数据模板
- `PERFORMANCE_DATA_TEMPLATE`: 表演数据模板

**使用方式**：
```python
from src.data_extraction.data_models import DataTemplates

# 获取模板的深拷贝
dialogue_template = DataTemplates.get_dialogue_template()
```

### 3. LLM客户端 (llm_client.py)

封装OpenAI API调用，提供统一的LLM接口。

**核心类**：
- `CustomOpenAILLM`: 继承自langchain的LLM基类，封装API调用
- `LLMClientManager`: 管理不同温度参数的LLM实例

**特点**：
- 支持自定义base_url和api_key
- 分离提取和判断两种LLM实例（不同温度参数）
- 统一的错误处理

### 4. 工具函数 (utils.py)

提供各种辅助功能，支持主提取流程。

**工具类**：

#### FileManager
- `ensure_directory(path)`: 确保目录存在
- `save_failed_json(content, filename, error_type)`: 保存失败的JSON

#### CharacterIDManager
- `load_character_ids()`: 加载角色ID映射
- `generate_character_id(role_name)`: 生成新的角色ID

#### JSONProcessor
- `clean_json_string(json_str)`: 清理JSON字符串
- `parse_json_safely(json_str)`: 安全解析JSON
- `validate_json_structure(data, required_keys)`: 验证JSON结构

#### ScriptProcessor
- `extract_roles_from_script(script_content)`: 从剧本提取角色列表
- `deduplicate_roles(roles)`: 角色去重
- `collect_scripts_by_role(enhanced_script_path)`: 收集每个角色的所有剧本

### 5. 核心提取器 (extractor.py)

实现数据提取的核心逻辑。

**核心类**：

#### RoleInfoExtractor
负责提取角色信息。

**主要方法**：
- `extract_role_info(role_name, script_content, script_name)`: 提取单个剧本的角色信息
- `extract_universal_info(role_name, all_role_info)`: 提取通用角色信息
- `save_role_profile(role_name, universal_info, all_role_info)`: 保存角色档案

**提取流程**：
1. 使用LLM从剧本中提取角色信息
2. 汇总所有剧本的角色信息
3. 提取通用信息（性别、年龄等）
4. 生成并保存profile.json

#### DialoguePerformanceExtractor
负责提取对话和表演数据。

**主要方法**：
- `extract_dialogues_and_performances(role_name, script_content, script_name)`: 提取对话和表演
- `judge_dialogue_or_performance(text)`: 判断文本类型
- `extract_dialogue_data(dialogue_text, script_name, character_id)`: 提取对话数据
- `extract_performance_data(performance_text, script_name, character_id)`: 提取表演数据

**提取流程**：
1. 从剧本中提取对话和表演文本
2. 使用LLM判断每段文本的类型
3. 根据类型调用相应的提取方法
4. 验证并清洗数据
5. 返回结构化的数据

#### CharacterDataExtractor
主控制器，协调整个提取流程。

**主要方法**：
- `process_all_characters()`: 处理所有角色
- `_process_single_character(role_name, scripts)`: 处理单个角色
- `_process_dialogues(dialogues, ...)`: 处理对话数据
- `_process_performances(performances, ...)`: 处理表演数据
- `_save_character_data(role_name, all_dialogues, all_performances)`: 保存角色数据

**完整流程**：
```
1. 收集所有角色及其剧本
   ↓
2. 对每个角色：
   a. 提取角色信息 → 保存profile.json
   b. 对每个剧本：
      - 提取对话和表演
      - 判断类型
      - 提取详细数据
      - 验证和清洗
   c. 汇总所有数据 → 保存data.json
   ↓
3. 完成所有角色的处理
```

## 数据格式

### profile.json 结构

```json
{
  "universal_info": {
    "姓名": "角色名",
    "性别": "男/女",
    "年龄": "年龄描述",
    "性格": "性格描述",
    "外貌": "外貌描述",
    "背景": "背景描述"
  },
  "script_info": [
    {
      "script_name": "剧本名称",
      "姓名": "角色名",
      "性别": "男/女",
      ...
    }
  ]
}
```

### data.json 结构

```json
{
  "dialogue_data": [
    {
      "script_name": "剧本名称",
      "character_id": "角色ID",
      "dialogue_group": [...],
      "context": "上下文",
      "emotion": "情感"
    }
  ],
  "performance_data": [
    {
      "script_name": "剧本名称",
      "character_id": "角色ID",
      "performance_content": "表演内容",
      "performance_type": "表演类型"
    }
  ]
}
```

## 错误处理

模块包含完善的错误处理机制：

1. **JSON解析错误**：保存失败的JSON到error_json目录
2. **API调用错误**：捕获并记录API错误
3. **数据验证错误**：跳过无效数据，继续处理
4. **文件操作错误**：自动创建必要的目录

## 性能优化

1. **批量处理**：按角色批量处理剧本
2. **内容限制**：限制单次处理的剧本长度（SCRIPT_CONTENT_LIMIT）
3. **数据过滤**：过滤过短的表演文本和对话组
4. **错误恢复**：单个提取失败不影响整体流程

## 扩展性

模块设计考虑了后续RAG和多agent系统的需求：

1. **模块化设计**：各组件独立，易于复用
2. **配置集中**：便于调整参数
3. **数据标准化**：统一的数据格式，便于检索
4. **工具函数**：可在其他模块中复用

## 注意事项

1. 确保API_KEY有效且有足够的配额
2. 剧本文件应放在正确的目录结构中
3. 首次运行会创建必要的输出目录
4. 处理大量数据时注意API调用频率限制
5. 定期检查error_json目录，分析失败原因

## 后续开发

本模块是项目的第一个目标，后续将开发：

- **目标2**：基于提取的数据构建RAG检索系统
- **目标3**：实现多agent协作的剧本生成系统
- **最终集成**：将三个模块整合到统一的main.py入口

## 维护与更新

- 代码遵循PEP 8规范
- 使用类型注解提高代码可读性
- 详细的注释说明关键逻辑
- 模块化设计便于单元测试
