"""
数据模型 - 定义所有数据结构模板
"""
import copy

class DataTemplates:
    """数据模板类"""
    
    # 角色单剧本信息模板
    PERSON_SCRIPT_DATA_TEMPLATE = {
        "id": "",
        "title": "",
        "outline": "",
        "age": "",
        "personality": "",
        "description": "",
        "profession": "",
        "face": "",
        "makeup": "",
        "cloth": "",
        "knowledge": "",
        "expression": False
    }
    
    # 通用信息模板
    UNIVERSAL_INFO_TEMPLATE = {
        "gender": "",
        "catchphrases": [],
        "forbidden": []
    }
    
    # 角色完整信息模板
    PERSON_TEMPLATE = {
        "id": "",
        "name": "",
        "data": {
            "script_data": [],
            "gender": "",
            "catchphrases": [],
            "forbidden": []
        }
    }
    
    # 对话数据模板
    DIALOGUE_DATA_TEMPLATE = {
        "id": "",
        "title": "",
        "type": "dialogue",
        "role": {
            "bot": {
                "id": "",
                "name": "",
                "age": "",
                "gender": "",
                "personality": "",
                "catchphrases": [],
                "description": "",
                "forbidden": [],
                "knowledge": ""
            },
            "user": {
                "name": "",
                "description": ""
            }
        },
        "third_role": "",
        "scene": "",
        "tags": [],
        "relation": "",
        "messages": [],
        "source": "llm",
        "judgment": {
            "is_valid": True,
            "reason": ""
        }
    }
    
    # 表演数据模板
    PERFORMANCE_DATA_TEMPLATE = {
        "id": "",
        "title": "",
        "type": "performance",
        "role": {
            "bot": {
                "id": "",
                "name": "",
                "age": "",
                "gender": "",
                "personality": "",
                "catchphrases": [],
                "description": "",
                "forbidden": [],
                "knowledge": ""
            }
        },
        "scene": "",
        "tags": [],
        "relation": "",
        "messages": [],
        "source": "llm",
        "judgment": {
            "is_valid": True,
            "reason": ""
        }
    }
    
    @staticmethod
    def get_person_template():
        """获取角色模板的深拷贝"""
        return copy.deepcopy(DataTemplates.PERSON_TEMPLATE)
    
    @staticmethod
    def get_dialogue_template():
        """获取对话模板的深拷贝"""
        return copy.deepcopy(DataTemplates.DIALOGUE_DATA_TEMPLATE)
    
    @staticmethod
    def get_performance_template():
        """获取表演模板的深拷贝"""
        return copy.deepcopy(DataTemplates.PERFORMANCE_DATA_TEMPLATE)
    
    @staticmethod
    def get_universal_info_template():
        """获取通用信息模板的深拷贝"""
        return copy.deepcopy(DataTemplates.UNIVERSAL_INFO_TEMPLATE)
    
    @staticmethod
    def get_script_data_template():
        """获取单剧本数据模板的深拷贝"""
        return copy.deepcopy(DataTemplates.PERSON_SCRIPT_DATA_TEMPLATE)
