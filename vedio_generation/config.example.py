"""
配置文件示例
复制此文件为 config.py 并填入你的配置
"""

# API配置
OPENAI_API_KEY = "your-openai-api-key-here"
GEMINI_API_KEY = "your-gemini-api-key-here"

# 路径配置
SCRIPT_FOLDER = "generated_scripts"
OUTPUT_FOLDER = "generated_videos/output"

# 生成配置
MAX_ITERATIONS = 5  # 每个视频最大迭代次数
VIDEO_DURATION = 12  # 视频时长（秒）
VIDEO_RESOLUTION = "1280x720"  # 视频分辨率

# 评估配置
PASS_THRESHOLD = 7.0  # 导演评估通过阈值
EVALUATION_DIMENSIONS = [
    "costume_accuracy",    # 装扮准确性
    "action_quality",      # 动作质量
    "dialogue_delivery",   # 对话表达
    "scene_consistency",   # 场景一致性
    "overall_impression"   # 整体印象
]

# 日志配置
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "video_pipeline.log"

# Sora2 API配置
SORA2_API_BASE = "https://api.openai.com/v1"
SORA2_MODEL = "sora-1.0-turbo"
SORA2_POLL_INTERVAL = 5  # 轮询间隔（秒）
SORA2_MAX_POLL_ATTEMPTS = 120  # 最大轮询次数（10分钟）

# Gemini配置
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 2048
