"""
场景设定Agent - 生成布景和音效
只生成布景描述和音效设计，不包含灯光和道具
"""
from typing import Dict, Any, List
from .agent_base import AgentBase


class SceneSettingAgent(AgentBase):
    """场景设定Agent，为场景生成布景和音效"""
    
    def __init__(self, temperature: float = 0.7):
        """
        初始化场景设定Agent
        
        Args:
            temperature: 温度参数
        """
        system_prompt = self._build_system_prompt()
        
        super().__init__(
            name="场景设定师",
            role="scene_setting_designer",
            system_prompt=system_prompt,
            temperature=temperature
        )
    
    def _build_system_prompt(self) -> str:
        """构建场景设定Agent的系统提示"""
        prompt = """你是一位专业的京剧舞台设计师，擅长为京剧场景设计布景和音效。

## 你的任务
根据场景信息，设计合适的布景和音效，营造符合京剧艺术风格的舞台氛围。

## 设计原则

### 1. 布景设计
- **简洁大气**：京剧舞台讲究"一桌二椅"的写意风格，不追求写实
- **突出重点**：布景要服务于剧情和人物，不喧宾夺主
- **意境营造**：通过简单的布置营造丰富的意境
- **2-3句话**：描述要简洁明了，不超过3句话

### 2. 音效设计
- **环境音**：营造场景氛围的自然声音（1-2项）
- **背景音乐**：符合场景情绪的传统乐器演奏（1项）
- **简洁明确**：每项音效用简短的词语描述

## 场景类型与设计参考

### 开场/对话场景
**布景**：
- 室内：茅庐、书房、大殿、客厅
- 室外：庭院、竹林、山野、城楼
- 特点：温馨、雅致、宁静

**音效**：
- 环境音：鸟鸣、竹叶声、风声、虫鸣
- 背景音乐：古琴、琵琶等轻柔乐器

**示例**：
```
布景：舞台中央布置一座简朴的茅庐，内有书架、竹席，墙上挂有几幅山水画。窗外竹影摇曳，营造出宁静的氛围。
音效：竹叶沙沙声、偶有鸟鸣声、轻柔的古琴背景音乐
```

### 武打/冲突场景
**布景**：
- 战场、山野、关隘、城门
- 特点：开阔、气势磅礴

**音效**：
- 环境音：风声呼啸、战鼓擂动
- 背景音乐：激烈的锣鼓经

**示例**：
```
布景：舞台呈现开阔的山野战场，远处山峦起伏，近处旌旗猎猎。地面铺设简单的战场标识。
音效：风声呼啸、战鼓擂动、激烈的锣鼓经
```

### 抒情/叙事场景
**布景**：
- 月下庭院、江边、山水之间、花园
- 特点：优美、诗意、富有意境

**音效**：
- 环境音：流水声、虫鸣、风吹树叶
- 背景音乐：箫声、古筝等抒情乐器

**示例**：
```
布景：月光下的庭院，假山流水，花木扶疏。一轮明月悬挂舞台上方，营造出诗意的氛围。
音效：流水潺潺、虫鸣声、悠扬的箫声
```

### 追赶/紧张场景
**布景**：
- 山路、林间、街道、城墙
- 特点：动感、紧迫

**音效**：
- 环境音：急促脚步声、喘息声
- 背景音乐：急促的锣鼓

**示例**：
```
布景：蜿蜒的山路，两侧树木茂密。舞台营造出曲折险峻的氛围。
音效：急促脚步声、喘息声、急促的锣鼓
```

## 输出格式

严格按照以下JSON格式输出：

```json
{
  "scenery": "布景描述（2-3句话，描述舞台布置和环境氛围）",
  "sound_effects": {
    "environment": "环境音1、环境音2",
    "background_music": "背景音乐描述"
  }
}
```

## 注意事项
1. 布景描述要简洁，2-3句话即可
2. 音效描述要具体，便于实际制作
3. 风格要符合京剧艺术的写意特点
4. 不要包含灯光和道具的描述
5. 必须严格按照JSON格式输出，不要添加其他内容
"""
        return prompt
    
    def generate_scene_setting(
        self,
        scene_info: Dict[str, Any],
        scene_type: str,
        characters: List[str]
    ) -> Dict[str, Any]:
        """
        生成场景设定
        
        Args:
            scene_info: 场景信息（包含title和description）
            scene_type: 场景类型（开场/武打/抒情/对话/冲突/追赶）
            characters: 出场角色列表
            
        Returns:
            {
                'scenery': '布景描述',
                'sound_effects': {
                    'environment': '环境音',
                    'background_music': '背景音乐'
                }
            }
        """
        # 构建输入
        scene_title = scene_info.get('title', '未命名场景')
        scene_desc = scene_info.get('description', '')
        
        user_input = f"""请为以下京剧场景设计布景和音效：

场景名称：{scene_title}
场景描述：{scene_desc}
场景类型：{scene_type}
出场角色：{', '.join(characters)}

请严格按照JSON格式输出布景和音效设计。"""
        
        # 生成响应
        response = self.generate_response(user_input)
        
        # 解析JSON响应
        try:
            import json
            # 尝试提取JSON部分
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # 验证必需字段
            if 'scenery' not in result or 'sound_effects' not in result:
                raise ValueError("缺少必需字段")
            
            return result
            
        except Exception as e:
            print(f"⚠ 场景设定解析失败: {str(e)}")
            # 返回默认设定
            return self._get_default_setting(scene_type)
    
    def _get_default_setting(self, scene_type: str) -> Dict[str, Any]:
        """获取默认场景设定"""
        defaults = {
            "开场": {
                "scenery": "舞台中央布置简洁的场景，营造出京剧传统的写意氛围。",
                "sound_effects": {
                    "environment": "环境音效",
                    "background_music": "传统京剧音乐"
                }
            },
            "武打": {
                "scenery": "舞台呈现开阔的空间，便于武打表演。",
                "sound_effects": {
                    "environment": "风声",
                    "background_music": "激烈的锣鼓经"
                }
            },
            "抒情": {
                "scenery": "舞台营造出优美诗意的氛围。",
                "sound_effects": {
                    "environment": "自然音效",
                    "background_music": "悠扬的古琴曲"
                }
            },
            "对话": {
                "scenery": "舞台布置温馨雅致的场景。",
                "sound_effects": {
                    "environment": "轻柔环境音",
                    "background_music": "轻柔的背景音乐"
                }
            }
        }
        
        return defaults.get(scene_type, defaults["对话"])
    
    def generate_all_scene_settings(
        self,
        outline: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        """
        为大纲中的所有场景生成设定
        
        Args:
            outline: 剧本大纲
            
        Returns:
            场景编号到场景设定的映射
        """
        scenes = outline.get('scenes', [])
        scene_settings = {}
        
        for idx, scene in enumerate(scenes, 1):
            try:
                # 识别场景类型
                scene_type = self._identify_scene_type(scene, idx)
                
                # 提取角色
                characters = scene.get('characters', [])
                
                # 生成场景设定
                setting = self.generate_scene_setting(
                    scene_info=scene,
                    scene_type=scene_type,
                    characters=characters
                )
                
                scene_settings[idx] = setting
                print(f"  ✓ 场景{idx}设定生成完成：{scene.get('title', '未命名')}")
                
            except Exception as e:
                print(f"  ⚠ 场景{idx}设定生成失败: {str(e)}")
                scene_settings[idx] = self._get_default_setting("对话")
        
        return scene_settings
    
    def _identify_scene_type(self, scene: Dict[str, Any], scene_number: int) -> str:
        """
        识别场景类型
        
        Args:
            scene: 场景信息
            scene_number: 场景编号
            
        Returns:
            场景类型
        """
        title = scene.get('title', '').lower()
        description = scene.get('description', '').lower()
        combined = f"{title} {description}"
        
        # 关键词匹配
        if scene_number == 1 or any(kw in combined for kw in ['开场', '登场', '上场', '初见', '相遇']):
            return "开场"
        elif any(kw in combined for kw in ['武打', '战斗', '打斗', '交手', '对战', '厮杀', '争斗']):
            return "武打"
        elif any(kw in combined for kw in ['抒情', '感慨', '回忆', '思念', '悲伤', '喜悦', '唱']):
            return "抒情"
        elif any(kw in combined for kw in ['叙事', '讲述', '回顾', '说明', '介绍']):
            return "叙事"
        elif any(kw in combined for kw in ['冲突', '争执', '争论', '辩论', '对峙', '愤怒']):
            return "冲突"
        elif any(kw in combined for kw in ['追赶', '逃跑', '追击', '奔跑', '逃离']):
            return "追赶"
        else:
            return "对话"
