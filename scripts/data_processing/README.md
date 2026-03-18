# 数据处理脚本 (Data Processing)

本目录包含对原始京剧剧本数据进行提取和处理的脚本，是数据管线的核心环节。

## 脚本说明

| 文件 | 功能 |
|------|------|
| `extract.py` | 从 PDF/TXT 原始剧本中提取结构化数据（角色台词、唱腔、动作等） |
| `process_with_model.py` | 使用大语言模型对提取的剧本数据进行语义增强处理（单文件模式） |
| `process_with_model_batch.py` | 批量调用大语言模型处理多个角色的多个剧本文件 |

## 处理流程

```
pdfdata/ 或 txtdata/（原始剧本）
        ↓
  extract.py（结构化提取）
        ↓
  process_with_model_batch.py（LLM语义增强）
        ↓
  enhanced_script/（增强后剧本）
        ↓
  character_data/（角色数据 JSON）
```

## 使用方法

```bash
# 步骤1：提取原始剧本
python scripts/data_processing/extract.py

# 步骤2：单文件增强处理
python scripts/data_processing/process_with_model.py

# 步骤3：批量增强处理（推荐）
python scripts/data_processing/process_with_model_batch.py
```

## 输出

- `enhanced_script/` — 经过语义增强的结构化剧本文本
- `character_data/` — 角色属性、唱腔、行为模式的 JSON 数据