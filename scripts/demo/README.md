# 演示脚本 (Demo)

本目录包含用于展示系统功能的演示脚本。

## 脚本说明

| 文件 | 功能 |
|------|------|
| `demo_scene_setting.py` | 演示场景设定功能，展示多智能体如何协作生成京剧场景配置（服装、道具、舞台布局等） |

## 使用方法

```bash
python scripts/demo/demo_scene_setting.py
```

## 功能说明

该演示脚本展示了 `SceneSettingAgent`（场景设定智能体）的完整工作流程：

1. 接收剧目名称和角色信息
2. 生成符合历史背景的场景设定
3. 输出结构化的服装、道具、舞台场景 JSON 配置

演示结果保存至 `generated_scripts/` 目录。