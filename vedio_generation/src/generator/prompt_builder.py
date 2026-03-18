#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt构建器模块
优化的prompt生成，强调直接唱戏和基于对话历史
"""

from typing import Dict, Any, List
from config import settings


class PromptBuilder:
    """Prompt构建器类"""
    
    def __init__(self):
        """初始化Prompt构建器"""
        self.constraints = settings.PROMPT_CONSTRAINTS
    
    def build_prompt(self, prompt_info: Dict[str, Any]) -> str:
        """
        根据提取的信息构建优化的prompt文本
        
        Args:
            prompt_info: 提取的prompt信息，包含：
                - 剧本名字
                - 场景信息
                - 当前说话角色
                - 所有角色信息
                - 对话信息
                - 原始轮次
                
        Returns:
            str: 构建的prompt文本
        """
        prompt_parts = []
        
        # 1. 添加核心约束
        prompt_parts.append("请生成一个京剧表演视频，要求如下：")
        prompt_parts.append("1. 演员直接进行京剧唱腔表演，不需要进场动画，也不要出现除说话角色以外的角色，不要出现其他无关内容")
        prompt_parts.append("2. 严格按照提供的台词内容表演，不要自行添加或修改台词")
        prompt_parts.append("3. 京剧唱腔、动作、服装、妆容需符合传统京剧特色")
        prompt_parts.append("4. 表演需要基于对话历史的上下文，保持连贯性")
        
        # 2. 剧本和场景信息
        script_name = prompt_info.get("剧本名字", "")
        if script_name:
            prompt_parts.append(f"\n【剧本】《{script_name}》")
        
        scene_info = prompt_info.get("场景信息", {})
        if scene_info:
            scene_name = scene_info.get("场景名称", "")
            scene_desc = scene_info.get("场景描述", "")
            
            if scene_name or scene_desc:
                prompt_parts.append("\n【场景设定】")
                if scene_name:
                    prompt_parts.append(f"场景名称：{scene_name}")
                if scene_desc:
                    prompt_parts.append(f"场景描述：{scene_desc}")
        
        # 3. 角色信息（重点强调装扮）
        all_characters = prompt_info.get("所有角色信息", {})
        current_speaker = prompt_info.get("当前说话角色", "")
        
        if all_characters:
            prompt_parts.append("\n【角色装扮】")
            
            for char_name, char_info in all_characters.items():
                is_current = (char_name == current_speaker)
                char_desc_parts = []
                
                # 角色类型
                char_type = char_info.get("角色类型", "")
                if char_type:
                    char_desc_parts.append(f"行当：{char_type}")
                
                # 脸谱
                face_paint = char_info.get("脸谱", "")
                if face_paint:
                    char_desc_parts.append(f"脸谱：{face_paint}")
                
                # 妆容
                makeup = char_info.get("妆容", "")
                if makeup:
                    char_desc_parts.append(f"妆容：{makeup}")
                
                # 服装
                costume = char_info.get("服装", "")
                if costume:
                    char_desc_parts.append(f"服装：{costume}")
                
                # 配饰
                accessories = char_info.get("配饰", "")
                if accessories:
                    char_desc_parts.append(f"配饰：{accessories}")
                
                # 整体风格
                style = char_info.get("整体风格", "")
                if style:
                    char_desc_parts.append(f"风格：{style}")
                
                # 组合角色描述
                if char_desc_parts:
                    marker = "★" if is_current else "·"
                    prompt_parts.append(f"{marker} {char_name}：{' | '.join(char_desc_parts)}")
            
            # 标注当前说话角色
            if current_speaker:
                prompt_parts.append(f"\n注：本场景由【{current_speaker}】主要表演（标记★）")
        
        # 4. 表演内容（核心部分）
        dialogue_info = prompt_info.get("对话信息", {})
        if dialogue_info:
            prompt_parts.append("\n【表演内容】")
            
            # 动作指导
            action = dialogue_info.get("动作", "")
            if action:
                prompt_parts.append(f"动作：{action}")
            
            # 台词/唱词（最重要）
            dialogue = dialogue_info.get("对话", "")
            if dialogue:
                prompt_parts.append(f"唱词：{dialogue}")
                prompt_parts.append("（演员需完整演唱以上唱词，不得省略或添加）")
        
        # 5. 音乐伴奏要求
        prompt_parts.append("\n【音乐伴奏】")
        prompt_parts.append("配乐需包含传统京剧伴奏（胡琴、锣鼓等），与唱腔、动作精准配合")
        
        # 6. 最终强调
        prompt_parts.append("\n【重要提示】")
        prompt_parts.append("视频中只展示京剧表演本身，演员直接唱戏，不要出现准备、调整或其他无关画面")
        
        # 组合成最终prompt
        final_prompt = "\n".join(prompt_parts)
        
        return final_prompt
    
    def build_simple_prompt(self, prompt_info: Dict[str, Any]) -> str:
        """
        构建简化版prompt（用于快速测试）
        
        Args:
            prompt_info: 提取的prompt信息
            
        Returns:
            str: 简化的prompt文本
        """
        parts = []
        
        # 基本要求
        parts.append("生成京剧表演视频：演员直接唱戏，不要其他内容。")
        
        # 角色和台词
        current_speaker = prompt_info.get("当前说话角色", "")
        dialogue_info = prompt_info.get("对话信息", {})
        
        if current_speaker:
            parts.append(f"表演者：{current_speaker}")
        
        if dialogue_info:
            dialogue = dialogue_info.get("对话", "")
            if dialogue:
                parts.append(f"唱词：{dialogue}")
        
        # 装扮要求
        all_characters = prompt_info.get("所有角色信息", {})
        if current_speaker and current_speaker in all_characters:
            char_info = all_characters[current_speaker]
            costume = char_info.get("服装", "")
            if costume:
                parts.append(f"服装：{costume}")
        
        return " ".join(parts)
    
    def extract_key_elements(self, prompt_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取prompt的关键要素
        
        Args:
            prompt_info: prompt信息
            
        Returns:
            dict: 关键要素字典
        """
        elements = {
            "script_name": prompt_info.get("剧本名字", ""),
            "scene_name": prompt_info.get("场景信息", {}).get("场景名称", ""),
            "current_speaker": prompt_info.get("当前说话角色", ""),
            "dialogue": prompt_info.get("对话信息", {}).get("对话", ""),
            "action": prompt_info.get("对话信息", {}).get("动作", ""),
            "round": prompt_info.get("原始轮次", 0)
        }
        
        return elements
