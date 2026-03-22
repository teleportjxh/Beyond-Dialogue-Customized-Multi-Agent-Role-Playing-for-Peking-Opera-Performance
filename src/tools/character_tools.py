"""
角色数据工具 - 封装角色档案和数据加载为 CrewAI Tool
"""
import json
import os
from typing import Any, Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from src.config import Config


class CharacterNameInput(BaseModel):
    """角色名称输入"""
    character_name: str = Field(..., description="角色名称，如'诸葛亮'、'孙悟空'")


class LoadCharacterProfileTool(BaseTool):
    """加载角色档案工具 - 获取角色基本信息"""
    name: str = "load_character_profile"
    description: str = (
        "加载角色的基本档案信息，包括性别、年龄、性格、职业、描述、"
        "历史脸谱、妆容、服装等。输入角色名称即可。"
    )
    args_schema: Type[BaseModel] = CharacterNameInput
    
    def _run(self, character_name: str) -> str:
        """加载角色档案"""
        profile_path = os.path.join(
            Config.CHARACTER_PATH,
            character_name,
            "profile.json"
        )
        
        if not os.path.exists(profile_path):
            return json.dumps(
                {"error": f"角色档案不存在: {character_name}"},
                ensure_ascii=False
            )
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # 提取关键信息
            data = profile.get('data', {})
            result = {
                'character': character_name,
                'gender': data.get('gender', '未知'),
            }
            
            if data.get('script_data'):
                first_script = data['script_data'][0]
                result.update({
                    'age': first_script.get('age', '未知'),
                    'personality': first_script.get('personality', '未知'),
                    'profession': first_script.get('profession', '未知'),
                    'description': first_script.get('description', '未知'),
                    'face': first_script.get('face', ''),
                    'makeup': first_script.get('makeup', ''),
                    'cloth': first_script.get('cloth', ''),
                })
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps(
                {"error": f"加载角色档案失败: {str(e)}"},
                ensure_ascii=False
            )


class LoadCharacterDataTool(BaseTool):
    """加载角色数据工具 - 获取角色口头禅、禁忌等"""
    name: str = "load_character_data"
    description: str = (
        "加载角色的详细数据，包括口头禅、行为禁忌等。"
        "这些信息对于演员扮演角色时保持一致性非常重要。"
    )
    args_schema: Type[BaseModel] = CharacterNameInput
    
    def _run(self, character_name: str) -> str:
        """加载角色数据"""
        data_path = os.path.join(
            Config.CHARACTER_DATA_PATH,
            character_name,
            "data.json"
        )
        
        if not os.path.exists(data_path):
            return json.dumps(
                {"error": f"角色数据不存在: {character_name}"},
                ensure_ascii=False
            )
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = {
                'character': character_name,
                'catchphrases': data.get('catchphrases', [])[:10],
                'forbidden': data.get('forbidden', [])[:10],
                'speaking_style': data.get('speaking_style', ''),
                'behavior_patterns': data.get('behavior_patterns', [])[:5],
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps(
                {"error": f"加载角色数据失败: {str(e)}"},
                ensure_ascii=False
            )


class UserRequestInput(BaseModel):
    """用户请求输入"""
    user_request: str = Field(..., description="用户的剧本需求描述")


class ExtractCharactersTool(BaseTool):
    """从用户需求中提取角色名称"""
    name: str = "extract_characters"
    description: str = (
        "从用户的剧本需求描述中识别涉及的角色名称。"
        "会与系统中已有的角色库进行匹配。"
    )
    args_schema: Type[BaseModel] = UserRequestInput
    
    def _run(self, user_request: str) -> str:
        """提取角色名称"""
        characters = []
        
        if os.path.exists(Config.CHARACTER_PATH):
            available_characters = [
                d for d in os.listdir(Config.CHARACTER_PATH)
                if os.path.isdir(os.path.join(Config.CHARACTER_PATH, d))
            ]
            
            for char in available_characters:
                if char in user_request:
                    characters.append(char)
        
        return json.dumps({
            'characters': characters,
            'count': len(characters)
        }, ensure_ascii=False, indent=2)
