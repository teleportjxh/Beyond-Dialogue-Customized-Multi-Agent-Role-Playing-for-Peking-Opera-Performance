"""
对话管理器 - 管理多Agent之间的消息传递和同步
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class DialogueManager:
    """对话管理器，负责Agent间的消息传递和历史记录"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.dialogue_history: List[Dict[str, Any]] = []
        self.current_scene: Optional[str] = None
        self.turn_count = 0
    
    def start_scene(self, scene_name: str, scene_description: str):
        """
        开始新场景
        
        Args:
            scene_name: 场景名称
            scene_description: 场景描述
        """
        self.current_scene = scene_name
        self.add_system_message(
            f"【场景开始】{scene_name}",
            {"description": scene_description}
        )
    
    def add_dialogue(
        self,
        character: str,
        content: str,
        parsed_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        添加对话到历史
        
        Args:
            character: 角色名称
            content: 对话内容
            parsed_data: 解析后的结构化数据
            metadata: 额外的元数据
        """
        self.turn_count += 1
        
        dialogue_entry = {
            "turn": self.turn_count,
            "scene": self.current_scene,
            "character": character,
            "content": content,
            "parsed": parsed_data or {},
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.dialogue_history.append(dialogue_entry)
    
    def add_system_message(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加系统消息
        
        Args:
            message: 系统消息
            metadata: 元数据
        """
        system_entry = {
            "turn": self.turn_count,
            "scene": self.current_scene,
            "character": "系统",
            "content": message,
            "parsed": {},
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.dialogue_history.append(system_entry)
    
    def get_recent_dialogues(
        self,
        count: int = 5,
        exclude_character: Optional[str] = None
    ) -> str:
        """
        获取最近的对话
        
        Args:
            count: 获取数量
            exclude_character: 排除的角色
            
        Returns:
            格式化的对话字符串
        """
        recent = []
        
        for entry in reversed(self.dialogue_history):
            if entry['character'] == '系统':
                continue
            
            if exclude_character and entry['character'] == exclude_character:
                continue
            
            recent.append(entry)
            
            if len(recent) >= count:
                break
        
        # 反转回正序
        recent.reverse()
        
        # 格式化
        formatted = []
        for entry in recent:
            formatted.append(f"{entry['character']}：{entry['content']}")
        
        return "\n".join(formatted)
    
    def get_scene_dialogues(self, scene_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取特定场景的所有对话
        
        Args:
            scene_name: 场景名称，None表示当前场景
            
        Returns:
            对话列表
        """
        target_scene = scene_name or self.current_scene
        
        return [
            entry for entry in self.dialogue_history
            if entry['scene'] == target_scene
        ]
    
    def get_character_dialogues(self, character: str) -> List[Dict[str, Any]]:
        """
        获取特定角色的所有对话
        
        Args:
            character: 角色名称
            
        Returns:
            对话列表
        """
        return [
            entry for entry in self.dialogue_history
            if entry['character'] == character
        ]
    
    def get_last_speaker(self) -> Optional[str]:
        """
        获取最后说话的角色
        
        Returns:
            角色名称，如果没有则返回None
        """
        for entry in reversed(self.dialogue_history):
            if entry['character'] != '系统':
                return entry['character']
        return None
    
    def get_dialogue_count(self, character: Optional[str] = None) -> int:
        """
        获取对话数量
        
        Args:
            character: 角色名称，None表示所有对话
            
        Returns:
            对话数量
        """
        if character is None:
            return len([e for e in self.dialogue_history if e['character'] != '系统'])
        else:
            return len(self.get_character_dialogues(character))
    
    def format_for_display(
        self,
        include_metadata: bool = False,
        scene_name: Optional[str] = None
    ) -> str:
        """
        格式化对话用于显示
        
        Args:
            include_metadata: 是否包含元数据
            scene_name: 场景名称，None表示所有场景
            
        Returns:
            格式化的字符串
        """
        dialogues = self.dialogue_history
        
        if scene_name:
            dialogues = [d for d in dialogues if d['scene'] == scene_name]
        
        lines = []
        current_scene = None
        
        for entry in dialogues:
            # 场景标记
            if entry['scene'] != current_scene:
                current_scene = entry['scene']
                lines.append(f"\n{'='*50}")
                lines.append(f"【{current_scene}】")
                lines.append(f"{'='*50}\n")
            
            # 对话内容
            if entry['character'] == '系统':
                lines.append(f"[{entry['content']}]")
            else:
                lines.append(f"\n{entry['character']}（第{entry['turn']}轮）：")
                lines.append(entry['content'])
                
                # 元数据
                if include_metadata and entry['parsed']:
                    parsed = entry['parsed']
                    if parsed.get('emotion'):
                        lines.append(f"  情感：{parsed['emotion']}")
                    if parsed.get('type'):
                        lines.append(f"  类型：{parsed['type']}")
        
        return "\n".join(lines)
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        导出为字典格式
        
        Returns:
            包含所有对话历史的字典
        """
        return {
            "total_turns": self.turn_count,
            "current_scene": self.current_scene,
            "dialogue_history": self.dialogue_history,
            "statistics": {
                "total_dialogues": len([e for e in self.dialogue_history if e['character'] != '系统']),
                "total_scenes": len(set(e['scene'] for e in self.dialogue_history if e['scene'])),
                "characters": list(set(e['character'] for e in self.dialogue_history if e['character'] != '系统'))
            }
        }
    
    def clear(self):
        """清空对话历史"""
        self.dialogue_history = []
        self.current_scene = None
        self.turn_count = 0
