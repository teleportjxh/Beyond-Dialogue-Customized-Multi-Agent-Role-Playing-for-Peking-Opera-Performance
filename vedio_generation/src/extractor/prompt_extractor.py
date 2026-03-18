"""
Prompt提取器 - 从generated_scripts文件夹提取视频生成prompt
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PromptExtractor:
    """从剧本文件中提取视频生成prompt"""
    
    def __init__(self, script_folder: str):
        """
        初始化提取器
        
        Args:
            script_folder: generated_scripts文件夹路径
        """
        self.script_folder = Path(script_folder)
        self.dialogue_history = None
        self.costume_design = None
        self.scene_settings = None
        
    def load_script_data(self, script_name: str) -> bool:
        """
        加载剧本相关的所有数据文件
        
        Args:
            script_name: 剧本名称（如"煮酒论英雄"）
            
        Returns:
            是否成功加载
        """
        try:
            # 加载对话历史
            dialogue_file = self.script_folder / f"{script_name}_对话历史.json"
            with open(dialogue_file, 'r', encoding='utf-8') as f:
                self.dialogue_history = json.load(f)
            logger.info(f"加载对话历史: {len(self.dialogue_history)} 个turn")
            
            # 加载装扮设计
            costume_file = self.script_folder / f"{script_name}_装扮设计.json"
            with open(costume_file, 'r', encoding='utf-8') as f:
                self.costume_design = json.load(f)
            logger.info(f"加载装扮设计: {len(self.costume_design)} 个角色")
            
            # 加载场景设定
            scene_file = self.script_folder / f"{script_name}_场景设定.json"
            with open(scene_file, 'r', encoding='utf-8') as f:
                self.scene_settings = json.load(f)
            logger.info(f"加载场景设定: {len(self.scene_settings)} 个场景")
            
            return True
            
        except Exception as e:
            logger.error(f"加载剧本数据失败: {e}")
            return False
    
    def extract_video_prompts(self) -> List[Dict]:
        """
        提取所有视频的prompt列表
        每个视频对应对话历史中的一个turn，时长10-15秒
        
        Returns:
            视频prompt列表，每个元素包含：
            {
                'turn': turn编号,
                'character': 角色名,
                'prompt': 生成的prompt文本,
                'scene': 场景信息,
                'metadata': 元数据
            }
        """
        if not self.dialogue_history:
            logger.error("对话历史未加载")
            return []
        
        video_prompts = []
        
        for turn_data in self.dialogue_history:
            try:
                prompt_data = self._build_single_prompt(turn_data)
                if prompt_data:
                    video_prompts.append(prompt_data)
            except Exception as e:
                logger.error(f"提取turn {turn_data.get('turn')} 的prompt失败: {e}")
                continue
        
        logger.info(f"成功提取 {len(video_prompts)} 个视频prompt")
        return video_prompts
    
    def _build_single_prompt(self, turn_data: Dict) -> Optional[Dict]:
        """
        为单个turn构建视频生成prompt
        
        Args:
            turn_data: 对话历史中的一个turn数据
            
        Returns:
            包含prompt和元数据的字典
        """
        try:
            character = turn_data.get('character')
            if not character:
                return None
            
            # 跳过系统消息
            if character == '系统':
                return None
            
            # 获取角色装扮信息
            costume_info = self._get_costume_info(character)
            
            # 获取场景信息
            scene_name = turn_data.get('scene')
            scene_info = self._get_scene_info(scene_name) if scene_name else {}
            
            # 获取动作/对话内容
            parsed = turn_data.get('parsed', {})
            
            # 安全地提取parsed字段，处理可能为空dict的情况
            emotion = parsed.get('emotion', '') if isinstance(parsed, dict) else ''
            content_type = parsed.get('type', '') if isinstance(parsed, dict) else ''
            content_text = parsed.get('text', '') if isinstance(parsed, dict) else ''
            
            # 如果没有有效内容，跳过此turn
            if not content_text:
                return None
            
            # 构建prompt
            prompt = self._compose_prompt(
                character=character,
                costume=costume_info,
                scene=scene_info,
                emotion=emotion,
                content_type=content_type,
                content_text=content_text
            )
            
            return {
                'turn': turn_data.get('turn'),
                'character': character,
                'prompt': prompt,
                'scene': scene_name,
                'emotion': emotion,
                'content_type': content_type,
                'content_text': content_text,
                'metadata': turn_data.get('metadata', {})
            }
        except Exception as e:
            turn_num = turn_data.get('turn', 'unknown')
            logger.error(f"构建turn {turn_num} 的prompt时出错: {e}", exc_info=True)
            return None
    
    def _get_costume_info(self, character: str) -> Dict:
        """获取角色装扮信息"""
        if not self.costume_design:
            return {}
        
        # costume_design是字典格式: {"孙悟空": {...}, "诸葛亮": {...}}
        if isinstance(self.costume_design, dict):
            return self.costume_design.get(character, {})
        
        # 兼容列表格式（如果有的话）
        if isinstance(self.costume_design, list):
            for costume in self.costume_design:
                if isinstance(costume, dict) and costume.get('character') == character:
                    return costume
        
        return {}
    
    def _get_scene_info(self, scene_name: str) -> Dict:
        """获取场景信息"""
        if not self.scene_settings or not scene_name:
            return {}
        
        # scene_settings是字典格式: {"1": {...}, "2": {...}, "3": {...}}
        # scene_name格式可能是 "场景1：未命名" 或 "场景1"
        if isinstance(self.scene_settings, dict):
            # 提取场景编号
            scene_num = None
            if "场景" in scene_name:
                # 从 "场景1：未命名" 或 "场景1" 中提取 "1"
                parts = scene_name.split("：")[0] if "：" in scene_name else scene_name
                scene_num = parts.replace("场景", "").strip()
            
            if scene_num and scene_num in self.scene_settings:
                return self.scene_settings[scene_num]
        
        # 兼容列表格式（如果有的话）
        if isinstance(self.scene_settings, list):
            for scene in self.scene_settings:
                if isinstance(scene, dict) and scene.get('scene') == scene_name:
                    return scene
        
        return {}
    
    def _compose_prompt(
        self,
        character: str,
        costume: Dict,
        scene: Dict,
        emotion: str,
        content_type: str,
        content_text: str
    ) -> str:
        """
        组合生成最终的prompt
        
        重点：
        1. 10-15秒短视频
        2. 一个人物的一次对话/动作
        3. 通过对话历史指导视频
        4. 不出现其他东西，直接表演
        """
        prompt_parts = []
        
        # 1. 角色和装扮描述
        if costume:
            costume_desc = self._format_costume_description(character, costume)
            prompt_parts.append(costume_desc)
        else:
            prompt_parts.append(f"A character named {character}")
        
        # 2. 场景环境（简洁）
        if scene:
            scene_desc = self._format_scene_description(scene)
            if scene_desc:
                prompt_parts.append(f"in {scene_desc}")
        
        # 3. 情感状态
        if emotion:
            prompt_parts.append(f"with emotion: {emotion}")
        
        # 4. 核心动作/对话（最重要）
        action_desc = self._format_action_description(content_type, content_text)
        if action_desc:
            prompt_parts.append(action_desc)
        
        # 5. 视频时长要求
        prompt_parts.append("Duration: 10-15 seconds")
        
        # 6. 质量要求
        prompt_parts.append("High quality, cinematic, focused on the character's performance")
        
        prompt = ", ".join(prompt_parts)
        return prompt
    
    def _format_costume_description(self, character: str, costume: Dict) -> str:
        """格式化装扮描述"""
        parts = [character]
        
        try:
            # 脸谱
            face_pattern = costume.get('face_pattern')
            if face_pattern and isinstance(face_pattern, str):
                parts.append(f"with {face_pattern}")
            
            # 妆容
            makeup = costume.get('makeup')
            if makeup and isinstance(makeup, str):
                parts.append(makeup)
            
            # 服装
            costume_item = costume.get('costume')
            if costume_item and isinstance(costume_item, str):
                parts.append(f"wearing {costume_item}")
            
            # 配饰
            accessories = costume.get('accessories')
            if accessories:
                if isinstance(accessories, list):
                    acc_strs = [str(a) for a in accessories if a]
                    if acc_strs:
                        parts.append(f"with {', '.join(acc_strs)}")
                elif isinstance(accessories, str):
                    parts.append(f"with {accessories}")
        except Exception as e:
            logger.error(f"格式化装扮描述失败: {e}, costume={costume}")
        
        return " ".join(parts)
    
    def _format_scene_description(self, scene: Dict) -> str:
        """格式化场景描述（简洁版）"""
        try:
            scenery = scene.get('scenery', {})
            if not scenery or not isinstance(scenery, dict):
                return ""
            
            # 只提取关键场景元素
            key_elements = []
            
            location = scenery.get('location')
            if location and isinstance(location, str):
                key_elements.append(location)
            
            props = scenery.get('props')
            if props and isinstance(props, list):
                prop_strs = [str(p) for p in props[:2] if p]  # 最多2个道具
                key_elements.extend(prop_strs)
            
            return ", ".join(key_elements) if key_elements else ""
        except Exception as e:
            logger.error(f"格式化场景描述失败: {e}, scene={scene}")
            return ""
    
    def _format_action_description(self, content_type: str, content_text: str) -> str:
        """
        格式化动作/对话描述
        这是prompt的核心部分
        """
        if not content_text:
            return ""
        
        if content_type == "动作":
            return f"performing action: {content_text}"
        elif content_type == "念白":
            return f"speaking: {content_text}"
        elif content_type == "唱段":
            return f"singing: {content_text}"
        else:
            return f"performing: {content_text}"
    
    def get_prompt_by_turn(self, turn_number: int) -> Optional[Dict]:
        """
        获取指定turn的prompt
        
        Args:
            turn_number: turn编号
            
        Returns:
            prompt数据字典
        """
        if not self.dialogue_history:
            return None
        
        for turn_data in self.dialogue_history:
            if turn_data.get('turn') == turn_number:
                return self._build_single_prompt(turn_data)
        
        return None
    
    def get_prompts_by_character(self, character: str) -> List[Dict]:
        """
        获取指定角色的所有prompt
        
        Args:
            character: 角色名
            
        Returns:
            prompt列表
        """
        all_prompts = self.extract_video_prompts()
        return [p for p in all_prompts if p['character'] == character]
    
    def get_prompts_by_scene(self, scene_name: str) -> List[Dict]:
        """
        获取指定场景的所有prompt
        
        Args:
            scene_name: 场景名称
            
        Returns:
            prompt列表
        """
        all_prompts = self.extract_video_prompts()
        return [p for p in all_prompts if p['scene'] == scene_name]
