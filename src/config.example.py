"""
配置文件模板 - 复制此文件为 config.py 并填入真实配置
Copy this file to config.py and fill in your actual API credentials.
"""
import os

class Config:
    """项目配置类"""
    
    # API配置（请替换为你的真实 API Key）
    API_KEY = "sk-your_api_key_here"
    BASE_URL = "https://api.openai.com/v1/"   # 或其他兼容接口地址
    MODEL_NAME = "gpt-4o"                      # 或 gpt-4-turbo, deepseek-chat 等
    
    # 温度参数
    EXTRACT_TEMPERATURE = 0.1
    JUDGE_TEMPERATURE = 0.0
    
    # Token限制
    MAX_TOKENS = 5000
    
    # 路径配置
    JINGJU_ROOT = "."
    ENHANCED_SCRIPT_PATH = "./enhanced_script"
    CHARACTER_PATH = "./character"
    CHARACTER_DATA_PATH = "./character_data"
    ERROR_JSON_DIR = "./error_json"
    
    # 角色ID文件
    CHARACTER_ID_FILE = "character_id.txt"
    
    # 提取内容长度限制
    SCRIPT_CONTENT_LIMIT = 5000
    MIN_PERFORMANCE_LENGTH = 30
    MIN_DIALOGUE_GROUP_SIZE = 2
    
    @classmethod
    def get_character_id_path(cls):
        """获取角色ID文件的完整路径"""
        return os.path.join(cls.JINGJU_ROOT, cls.CHARACTER_ID_FILE)
    
    @classmethod
    def validate_api_key(cls):
        """验证API Key格式"""
        if not cls.API_KEY.startswith("sk-"):
            raise ValueError("API Key格式错误！需以'sk-'开头")
        return True