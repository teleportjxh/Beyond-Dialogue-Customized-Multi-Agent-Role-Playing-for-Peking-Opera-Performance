# 评估脚本 (Evaluation)

本目录包含用于评估和对比生成剧本质量的脚本。

## 脚本说明

| 文件 | 功能 |
|------|------|
| `compare_scripts.py` | 对比不同版本生成剧本的差异，分析改进效果 |
| `regenerate_script.py` | 根据评估报告重新生成或修订剧本，支持迭代优化 |

## 使用方法

```bash
# 对比剧本版本
python scripts/evaluation/compare_scripts.py

# 基于评估报告重新生成剧本
python scripts/evaluation/regenerate_script.py
```

## 评估维度

- **角色一致性**：生成剧本与历史剧本的角色行为、唱腔风格匹配度
- **情节连贯性**：多幕剧情逻辑连贯程度
- **京剧规范性**：唱腔格式（西皮/二黄）、念白风格的规范程度
- **创新性**：在保留传统风格基础上的个性化创作程度

## 输出

评估结果保存至 `generated_scripts/` 目录下的 `*_评估报告.json` 文件。