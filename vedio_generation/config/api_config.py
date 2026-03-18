"""
API配置文件
统一管理所有API相关配置
"""

# API基础配置 - 用于评估等功能
API_BASE_URL = "https://api.shubiaobiao.cn/v1"
API_KEY = "sk-uNTaHplU891bjK5tF67eBf24285f4b8689F23c734dF9C9Ea"

# 视频生成专用API配置
VIDEO_API_BASE_URL = "https://api.zyai.online/v1"
VIDEO_API_KEY = "sk-UteD2utX3AclJFzG25F97f83520f47249e57F0E3B0B31e85"

# 模型配置
MODELS = {
    # 视频生成模型
    "video_generation": "sora-2",
    
    # 评估和其他任务使用的模型
    "evaluation": "gemini-2.5-pro",
    
    # 备用模型
    "fallback": "gpt-4o"
}

# 超时设置（秒）
TIMEOUT = {
    "video_generation": 300,  # 5分钟
    "evaluation": 60,         # 1分钟
    "default": 30
}

# 重试配置
RETRY = {
    "max_attempts": 3,
    "delay": 2  # 秒
}
