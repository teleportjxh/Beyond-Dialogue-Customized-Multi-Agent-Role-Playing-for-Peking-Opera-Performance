# 数据采集脚本 (Data Collection)

本目录包含从哔哩哔哩等平台采集京剧相关数据的脚本。

## 脚本说明

| 文件 | 功能 |
|------|------|
| `search_bilibili.py` | 搜索哔哩哔哩上的京剧视频，单次搜索模式 |
| `search_bilibili_batch.py` | 批量搜索哔哩哔哩京剧视频，支持多角色批量采集 |

## 使用方法

```bash
# 单次搜索
python scripts/data_collection/search_bilibili.py

# 批量搜索
python scripts/data_collection/search_bilibili_batch.py
```

## 输出

采集的原始数据保存至 `pdfdata/` 和 `txtdata/` 目录，按角色名称分类存储。