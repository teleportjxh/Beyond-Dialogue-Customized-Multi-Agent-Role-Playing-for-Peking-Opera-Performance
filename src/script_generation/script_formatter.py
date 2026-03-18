"""
剧本格式化器
负责将生成的对话内容格式化为标准京剧剧本格式
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import re


class ScriptFormatter:
    """剧本格式化器，将对话历史格式化为京剧剧本"""
    
    def __init__(self):
        """初始化格式化器"""
        pass
    
    def format_script(self, 
                     outline: Dict[str, Any],
                     dialogue_history: List[Dict[str, Any]],
                     scene_settings: Optional[Dict[int, Dict[str, Any]]] = None) -> str:
        """
        格式化完整剧本
        
        Args:
            outline: 剧本大纲
            dialogue_history: 对话历史
            scene_settings: 场景设定（可选），格式为 {scene_number: {scenery: str, sound_effects: list}}
            
        Returns:
            格式化后的剧本文本
        """
        title = outline.get('title', '未命名剧本')
        
        # 构建剧本
        script_parts = []
        script_parts.append(f"## 标题：《{title}》\n")
        
        # 按场景组织对话
        scenes_dict = self._organize_by_scenes(dialogue_history)
        scene_outlines = outline.get('scenes', [])
        
        # 格式化每个场景
        for scene_idx, scene_num in enumerate(sorted(scenes_dict.keys())):
            scene_dialogues = scenes_dict[scene_num]
            scene_outline = scene_outlines[scene_idx] if scene_idx < len(scene_outlines) else {}
            
            # 获取该场景的场景设定（如果有）
            scene_setting = None
            if scene_settings:
                # 尝试整数键和字符串键（兼容不同格式）
                scene_setting = scene_settings.get(scene_num) or scene_settings.get(str(scene_num))
            
            formatted_scene = self._format_single_scene(
                scene_idx + 1,
                scene_dialogues,
                scene_outline,
                scene_setting
            )
            script_parts.append(formatted_scene)
        
        return '\n'.join(script_parts)
    
    def _organize_by_scenes(self, dialogue_history: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """按场景组织对话"""
        scenes_dict = {}
        
        for dialogue in dialogue_history:
            # 跳过系统消息
            if dialogue.get('character') == '系统':
                continue
            
            scene_num = dialogue.get('metadata', {}).get('scene_number', 1)
            if scene_num not in scenes_dict:
                scenes_dict[scene_num] = []
            scenes_dict[scene_num].append(dialogue)
        
        return scenes_dict
    
    def _format_single_scene(self,
                            scene_num: int,
                            dialogues: List[Dict[str, Any]],
                            outline: Dict[str, Any] = None,
                            scene_setting: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化单个场景
        
        Args:
            scene_num: 场景编号
            dialogues: 对话列表
            outline: 场景大纲
            scene_setting: 场景设定（可选），包含scenery和sound_effects
        """
        lines = []
        
        # 场景标题
        scene_name = outline.get('name', f'场景{scene_num}') if outline else f'场景{scene_num}'
        lines.append(f"### 第{self._number_to_chinese(scene_num)}场：{scene_name}\n")
        
        # 场景设定
        lines.append("#### 场景设定")
        if outline and outline.get('description'):
            lines.append(outline['description'])
        else:
            lines.append("（场景描述待补充）")
        
        # 添加布景和音效（如果有场景设定）
        if scene_setting:
            # 布景描述
            if scene_setting.get('scenery'):
                lines.append("\n**【布景】**")
                lines.append(scene_setting['scenery'])
            
            # 音效设计
            if scene_setting.get('sound_effects'):
                lines.append("\n**【音效】**")
                sound_effects = scene_setting['sound_effects']
                if sound_effects.get('environment'):
                    lines.append(f"- 环境音：{sound_effects['environment']}")
                if sound_effects.get('background_music'):
                    lines.append(f"- 背景音乐：{sound_effects['background_music']}")
        
        lines.append("")
        
        # 出场角色及顺序
        lines.append("#### 出场角色及顺序")
        characters = self._extract_characters_in_order(dialogues)
        for idx, char in enumerate(characters, 1):
            lines.append(f"{idx}. {char}")
        lines.append("")
        
        # 表演流程
        lines.append("#### 表演流程\n")
        
        # 格式化对话
        current_character = None
        for dialogue in dialogues:
            character = dialogue.get('character', '未知')
            
            # 如果是新角色出场，添加出场标记
            if character != current_character:
                if current_character is None:
                    lines.append(f"**【{character}出场】**")
                else:
                    lines.append(f"**【{character}登场】**")
                current_character = character
            
            formatted_dialogue = self._format_dialogue(dialogue)
            lines.append(formatted_dialogue)
        
        # 添加锣鼓经提示
        lines.append("**【锣鼓经】**")
        lines.append("- [提示] [四击头]\n")
        
        return '\n'.join(lines)
    
    def _format_dialogue(self, dialogue: Dict[str, Any]) -> str:
        """格式化单条对话"""
        content = dialogue.get('content', '')
        parsed = dialogue.get('parsed', {})
        emotion = parsed.get('emotion', '')
        
        lines = []
        
        # 解析内容
        parts = self._parse_content(content)
        
        # 重新组织parts：确保动作只跟在念白/唱段后面
        organized_parts = self._organize_parts_with_actions(parts)
        
        # 添加情绪描述（如果有）
        if emotion:
            lines.append(f"- (内心：{emotion})")
        
        # 处理各个部分
        for part in organized_parts:
            if part['type'] == 'speech':
                lines.append(f"- [念白] {part['text']}")
                # 如果有关联的动作，紧跟在念白后面
                if part.get('actions'):
                    lines.append(f"- [动作] {part['actions']}")
            elif part['type'] == 'singing':
                lines.append(f"- [唱词] {part['style']}")
                lines.append("  ```")
                for line in part['lyrics']:
                    lines.append(f"  {line}")
                lines.append("  ```")
                # 如果有关联的动作，紧跟在唱段后面
                if part.get('actions'):
                    lines.append(f"- [动作] {part['actions']}")
        
        lines.append("")
        return '\n'.join(lines)
    
    def _organize_parts_with_actions(self, parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重新组织parts，确保动作只跟在念白/唱段后面
        
        规则：
        1. 动作必须跟在念白或唱段后面
        2. 如果有孤立的动作，将其附加到最近的念白/唱段
        3. 连续的动作合并为一个
        4. 连续的念白合并为一个
        """
        if not parts:
            return []
        
        organized = []
        pending_actions = []  # 暂存待分配的动作
        
        for i, part in enumerate(parts):
            part_type = part['type']
            
            # 将entrance视为action
            if part_type == 'entrance':
                part_type = 'action'
            
            if part_type == 'action':
                # 收集动作，等待分配给念白/唱段
                pending_actions.append(part['text'])
            
            elif part_type == 'speech':
                # 合并连续的念白
                speech_texts = [part['text']]
                j = i + 1
                while j < len(parts):
                    if parts[j]['type'] == 'speech':
                        speech_texts.append(parts[j]['text'])
                        parts[j]['type'] = 'processed'  # 标记为已处理
                        j += 1
                    else:
                        break
                
                # 创建念白条目
                speech_entry = {
                    'type': 'speech',
                    'text': '，'.join(speech_texts)
                }
                
                # 收集这个念白后面的所有动作
                j = i + 1
                while j < len(parts):
                    next_type = parts[j]['type']
                    if next_type == 'entrance':
                        next_type = 'action'
                    
                    if next_type == 'action' and parts[j].get('type') != 'processed':
                        pending_actions.append(parts[j]['text'])
                        parts[j]['type'] = 'processed'  # 标记为已处理
                        j += 1
                    elif parts[j].get('type') == 'processed':
                        j += 1
                    else:
                        break
                
                # 如果有待分配的动作，附加到这个念白
                if pending_actions:
                    speech_entry['actions'] = '，'.join(pending_actions)
                    pending_actions = []
                
                organized.append(speech_entry)
            
            elif part_type == 'singing':
                # 唱段保持独立
                singing_entry = {
                    'type': 'singing',
                    'style': part['style'],
                    'lyrics': part['lyrics']
                }
                
                # 收集这个唱段后面的所有动作
                j = i + 1
                while j < len(parts):
                    next_type = parts[j]['type']
                    if next_type == 'entrance':
                        next_type = 'action'
                    
                    if next_type == 'action' and parts[j].get('type') != 'processed':
                        pending_actions.append(parts[j]['text'])
                        parts[j]['type'] = 'processed'  # 标记为已处理
                        j += 1
                    elif parts[j].get('type') == 'processed':
                        j += 1
                    else:
                        break
                
                # 如果有待分配的动作，附加到这个唱段
                if pending_actions:
                    singing_entry['actions'] = '，'.join(pending_actions)
                    pending_actions = []
                
                organized.append(singing_entry)
        
        # 如果最后还有未分配的动作，附加到最后一个念白/唱段
        if pending_actions and organized:
            last_entry = organized[-1]
            if 'actions' in last_entry:
                last_entry['actions'] += '，' + '，'.join(pending_actions)
            else:
                last_entry['actions'] = '，'.join(pending_actions)
        elif pending_actions and not organized:
            # 如果只有动作没有念白/唱段，创建一个简短念白
            organized.append({
                'type': 'speech',
                'text': '（上场）',
                'actions': '，'.join(pending_actions)
            })
        
        return organized
    
    def _parse_content(self, content: str) -> List[Dict[str, Any]]:
        """解析对话内容，分离动作、念白、唱词等"""
        parts = []
        
        # 移除情绪标记
        content = re.sub(r'【情】（[^）]+）\s*', '', content)
        
        # 提取锣鼓经（入场动作）
        entrance_pattern = r'\[〖[^〗]+〗[^\]]+\]'
        entrance_matches = re.findall(entrance_pattern, content)
        if entrance_matches:
            for match in entrance_matches:
                parts.append({
                    'type': 'entrance',
                    'text': match.strip('[]')
                })
                content = content.replace(match, '', 1)
        
        # 提取唱词
        singing_pattern = r'\(唱\)\s*\*\*\[([^\]]+)\]\*\*\s*((?:[^\n]+\n?)+?)(?=【|$)'
        singing_matches = re.findall(singing_pattern, content, re.MULTILINE)
        if singing_matches:
            for style, lyrics in singing_matches:
                lyrics_lines = [line.strip() for line in lyrics.strip().split('\n') if line.strip()]
                parts.append({
                    'type': 'singing',
                    'style': f'[{style}]',
                    'lyrics': lyrics_lines
                })
                # 移除已处理的唱词
                content = re.sub(r'\(唱\)\s*\*\*\[' + re.escape(style) + r'\]\*\*\s*' + re.escape(lyrics), '', content, count=1)
        
        # 提取念白（韵白）
        speech_pattern = r'【念】（韵白）([^\【]+)'
        speech_matches = re.findall(speech_pattern, content)
        if speech_matches:
            for match in speech_matches:
                # 分离动作和台词
                text = match.strip()
                # 提取方括号中的动作
                action_in_speech = re.findall(r'\[([^\]]+)\]', text)
                if action_in_speech:
                    # 先添加动作
                    for action in action_in_speech:
                        parts.append({
                            'type': 'action',
                            'text': action
                        })
                    # 移除动作，保留台词
                    text = re.sub(r'\[([^\]]+)\]\s*', '', text).strip()
                
                if text:
                    parts.append({
                        'type': 'speech',
                        'text': text
                    })
                
                content = content.replace(f'【念】（韵白）{match}', '', 1)
        
        # 提取剩余的动作【做】
        action_pattern = r'【做】\s*\[([^\]]+)\]'
        action_matches = re.findall(action_pattern, content)
        if action_matches:
            for match in action_matches:
                parts.append({
                    'type': 'action',
                    'text': match
                })
        
        return parts
    
    def _extract_characters_in_order(self, dialogues: List[Dict[str, Any]]) -> List[str]:
        """提取场景中出场的角色（按出场顺序）"""
        characters = []
        seen = set()
        
        for dialogue in dialogues:
            character = dialogue.get('character', '未知')
            if character not in seen:
                characters.append(character)
                seen.add(character)
        
        return characters
    
    def _number_to_chinese(self, num: int) -> str:
        """将数字转换为中文"""
        chinese_nums = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        if num < 11:
            return chinese_nums[num]
        elif num < 20:
            return '十' + chinese_nums[num - 10]
        else:
            return str(num)
    
    def export_to_file(self, script: str, output_path: str) -> None:
        """导出剧本到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script)
