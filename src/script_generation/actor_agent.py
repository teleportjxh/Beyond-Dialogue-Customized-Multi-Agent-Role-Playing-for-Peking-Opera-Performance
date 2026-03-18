"""
演员Agent - 扮演特定角色生成台词
"""
from typing import Optional, Dict, Any
from .agent_base import AgentBase


class ActorAgent(AgentBase):
    """演员Agent，扮演特定角色"""
    
    def __init__(
        self,
        character_name: str,
        character_context: str,
        temperature: float = 0.7
    ):
        """
        初始化演员Agent
        
        Args:
            character_name: 角色名称
            character_context: 角色上下文信息
            temperature: 温度参数
        """
        self.character_name = character_name
        self.character_context = character_context
        
        # 构建系统提示
        system_prompt = self._build_system_prompt()
        
        super().__init__(
            name=f"演员_{character_name}",
            role="actor",
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        # 演员特定状态
        self.dialogue_count = 0
        self.last_emotion = "平静"
    
    def _build_system_prompt(self) -> str:
        """构建演员Agent的系统提示"""
        prompt = f"""你是一位专业的京剧演员，正在扮演角色：{self.character_name}

{self.character_context}

## 你的任务
1. 完全沉浸在{self.character_name}的角色中
2. 根据剧情发展和其他角色的台词，生成符合人物性格的对话和表演
3. 保持京剧艺术风格，使用典雅的语言
4. **智能判断场景类型，在适当时机添加京剧专业元素**

## 场景类型识别与表演元素

### 1. 开场/上场场景
**识别特征**：角色首次登场、场景开始
**必须包含**：
- 身段动作：`[角色名拉起霸。]`、`[一个"筋斗"翻至台中]`、`[迈着虎步威风凛凛地从台中上]`
- 锣鼓经：`[〖急急风〗锣鼓声中]`、`[〖小锣声〗中]`
- 亮相：`[作威武"亮相"身段]`、`[手搭凉棚，作"瞭望"身段]`

### 2. 武打/冲突场景
**识别特征**：战斗、争执、激烈对抗
**应该包含**：
- 武打动作：`[起打]`、`[对打]`、`[摆开一个"叉阵"]`
- 锣鼓经：`[〖急急风〗锣鼓声中]`、`[〖四击头〗]`
- 身段：`[一个"铁板桥"身段惊险躲过]`、`[翻身败下]`

### 3. 抒情/叙事场景
**识别特征**：表达情感、讲述故事、回忆往事
**应该包含**：
- 唱腔：`(唱) **[西皮]**`、`(唱) **[二黄]**`、`(唱) **[吹腔]**`
- 唱词：使用韵文，每句7字或10字
- 情感身段：`[以袖拭泪]`、`[长叹一声]`

### 4. 舞台调度场景
**识别特征**：移动、行走、追赶、逃跑
**应该包含**：
- 圆场：`[走"圆场"]`、`[走"败兵圆场"]`
- 上下场：`[从舞台两侧上场]`、`[一溜烟下]`
- 锣鼓经：`[〖小锣声〗中]`

### 5. 情绪转折场景
**识别特征**：惊讶、愤怒、喜悦等情绪突变
**应该包含**：
- 身段：`[顿足捶胸]`、`[拍案而起]`、`[连连后退]`
- 表情：`[怒目圆睁]`、`[眉头微蹙]`

### 6. 普通对话场景
**识别特征**：日常交流、商议、问答
**主要使用**：
- 念白：韵白或散白
- 简单身段：`[拱手一礼]`、`[微微颔首]`、`[轻抚胡须]`

## 京剧专业元素库

### 身段动作
- 起霸、趟马、走边、圆场、亮相
- 拉山膀、云手、指掌、水袖
- 筋斗、跌扑、抢背、僵尸倒

### 锣鼓经
- 急急风、小锣、大锣、四击头
- 水底鱼、撕边、冲头、收头

### 唱腔板式
- 西皮：原板、慢板、快板、散板、摇板
- 二黄：原板、慢板、快板、散板
- 其他：吹腔、南梆子、四平调

### 武打程式
- 起打、对打、群打
- 走边、趟马、打出手

## 输出格式

根据场景类型，灵活组合以下元素：

**开场示例**：
【情】（威风凛凛，气势磅礴）
[〖急急风〗锣鼓声中，{self.character_name}迈着虎步从台中上，行至台中央，猛一转身，作威武"亮相"身段。]
【念】（韵白）[台词内容]
【做】[具体动作描述]

**唱段示例**：
【情】（悲愤交加，慷慨激昂）
(唱) **[西皮原板]**
[唱词第一句，七字或十字]
[唱词第二句]
【做】[配合唱词的身段动作]

**武打示例**：
【情】（怒不可遏，杀气腾腾）
[〖急急风〗锣鼓声中，{self.character_name}与对手起打。]
【做】[具体武打动作，如"一个'铁板桥'身段惊险躲过"]

**普通对话示例**：
【情】（沉思，谨慎）
【念】（韵白）[台词内容]
【做】[简单身段，如"轻抚胡须，微微颔首"]

## 重要原则

1. **不是每段都要添加所有元素**，要根据场景类型智能判断
2. **开场必须有身段和锣鼓经**，这是京剧的规范
3. **抒情场景优先使用唱腔**，展现京剧的音乐性
4. **武打场景必须有武打动作和锣鼓经**
5. **普通对话以念白为主**，配合简单身段即可
6. **所有身段、锣鼓经、唱腔都要用正确的标记格式**：
   - 身段：`[动作描述]`
   - 锣鼓经：`[〖锣鼓名〗描述]`
   - 唱腔：`(唱) **[板式名]**`

## 真实剧本参考

以下是真实京剧《金钱豹》的片段，学习其格式和节奏：

**开场片段**：
[〖急急风〗锣鼓声中，四小妖各持兵刃，翻着筋斗从舞台两侧上场，分列左右。金钱豹在强烈的锣鼓点中，迈着虎步威风凛凛地从台中上，行至台中央，猛一转身，持叉顿地，作威武"亮相"身段。]

**孙悟空上场**：
孙悟空 (白) 呔哈！[一个"筋斗"翻至台中，手搭凉棚，作"瞭望"身段]
[孙悟空拉起霸。]
[他手持金箍棒，在台上展示一套敏捷的"猴拳"身段，抓耳挠腮，眼神四处探看，活灵活现。]

**唱段片段**：
唐三藏 (唱) **[吹腔]**
身入空门修真养性，
参禅悟道探玄真。
大唐三藏奉圣命，
去到西天求取经文。

**武打片段**：
[丫鬟、书生起打。丫鬟（孙悟空）边打边退，引诱书生。丫鬟翻身下，孙悟空持金箍棒翻上，与书生开打。]
[〖急急风〗锣鼓声中，双方展开混战]

## 注意事项
- 严格遵守角色的性格特征和行为禁忌
- 台词要符合剧情逻辑和人物关系
- 保持与其他角色对话的连贯性
- 体现京剧的艺术特色和文化内涵
- 每次回复只生成一个表演片段，不要一次生成多轮对话
- **根据场景智能判断，不要机械地在每段都添加所有元素**
"""
        return prompt
    
    def generate_dialogue(
        self,
        context: str,
        other_dialogues: Optional[str] = None,
        is_first_appearance: bool = False,
        scene_type: str = "对话"
    ) -> Dict[str, Any]:
        """
        生成对话
        
        Args:
            context: 当前场景上下文
            other_dialogues: 其他角色的最近对话
            is_first_appearance: 是否首次登场
            scene_type: 场景类型（开场/武打/抒情/对话等）
            
        Returns:
            包含台词和元数据的字典
        """
        # 构建输入
        input_parts = [f"当前场景：{context}"]
        
        # 添加场景类型提示
        if is_first_appearance:
            input_parts.append(f"\n【重要】这是{self.character_name}的首次登场，必须包含：起霸/亮相身段、锣鼓经、上场动作！")
        elif scene_type:
            scene_hints = {
                "开场": "这是开场场景，需要包含身段动作、锣鼓经和亮相。",
                "武打": "这是武打场景，需要包含武打动作、急急风锣鼓经。",
                "抒情": "这是抒情场景，优先使用唱腔（西皮或二黄），配合情感身段。",
                "叙事": "这是叙事场景，可以使用唱腔讲述故事。",
                "对话": "这是普通对话场景，以念白为主，配合简单身段即可。",
                "冲突": "这是冲突场景，情绪激烈，需要强烈的身段动作。",
                "追赶": "这是追赶场景，需要走圆场、配合锣鼓经。"
            }
            hint = scene_hints.get(scene_type, "")
            if hint:
                input_parts.append(f"\n【场景提示】{hint}")
        
        if other_dialogues:
            input_parts.append(f"\n其他角色的对话：\n{other_dialogues}")
        
        input_parts.append(f"\n请以{self.character_name}的身份回应，根据场景类型智能添加京剧专业元素：")
        
        user_input = "\n".join(input_parts)
        
        # 生成响应
        response = self.generate_response(user_input)
        
        # 解析响应
        parsed = self._parse_response(response)
        
        # 更新状态
        self.dialogue_count += 1
        self.last_emotion = parsed.get('emotion', '平静')
        
        return {
            'character': self.character_name,
            'content': response,
            'parsed': parsed,
            'dialogue_number': self.dialogue_count,
            'scene_type': scene_type
        }
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析Agent响应
        
        Args:
            response: Agent的原始响应
            
        Returns:
            解析后的结构化数据
        """
        parsed = {
            'emotion': '',
            'type': '',
            'text': '',
            'raw': response
        }
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析情感
            if '【情】' in line:
                emotion = line.replace('【情】', '').strip()
                emotion = emotion.strip('（）()「」')
                parsed['emotion'] = emotion
            
            # 解析类型和内容
            elif '【念】' in line:
                parsed['type'] = '念白'
                parsed['text'] = line.replace('【念】', '').strip()
            elif '【唱】' in line:
                parsed['type'] = '唱词'
                parsed['text'] = line.replace('【唱】', '').strip()
            elif '【做】' in line:
                parsed['type'] = '动作'
                parsed['text'] = line.replace('【做】', '').strip()
            else:
                # 如果没有标记，默认为念白
                if not parsed['text']:
                    parsed['type'] = '念白'
                    parsed['text'] = line
        
        return parsed
    
    def receive_other_dialogue(self, character: str, dialogue: str):
        """
        接收其他角色的对话（实时同步）
        
        Args:
            character: 说话角色
            dialogue: 对话内容
        """
        # 将其他角色的对话添加到上下文中
        sync_message = f"【{character}刚刚说】：{dialogue}"
        self.update_state('last_received', {
            'character': character,
            'dialogue': dialogue
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取表演总结"""
        return {
            'character': self.character_name,
            'total_dialogues': self.dialogue_count,
            'last_emotion': self.last_emotion,
            'message_history_length': len(self.message_history)
        }
