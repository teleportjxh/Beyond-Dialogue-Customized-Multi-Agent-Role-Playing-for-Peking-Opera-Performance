# 测试脚本 (Tests)

本目录包含系统各模块的功能测试脚本，用于验证各组件的正确性。

## 脚本说明

| 文件 | 功能 |
|------|------|
| `simple_test.py` | 基础功能快速验证，测试系统基本运行状态 |
| `test_cleaning.py` | 测试文本清洗模块，验证剧本文本预处理效果 |
| `test_import.py` | 测试模块导入，确认依赖包和项目模块均可正常加载 |
| `test_scene_fix.py` | 测试场景修复功能，验证场景设定错误处理逻辑 |
| `test_scene_setting.py` | 完整测试场景设定智能体的生成能力和输出格式 |

## 使用方法

```bash
# 运行所有测试（建议从项目根目录执行）
python scripts/tests/simple_test.py
python scripts/tests/test_import.py
python scripts/tests/test_cleaning.py
python scripts/tests/test_scene_setting.py
python scripts/tests/test_scene_fix.py
```

## 测试顺序建议

首次运行时建议按以下顺序执行：

1. `test_import.py` — 确认环境配置正确
2. `simple_test.py` — 快速验证系统可用
3. `test_cleaning.py` — 验证数据预处理
4. `test_scene_setting.py` — 验证核心智能体功能
5. `test_scene_fix.py` — 验证错误修复机制