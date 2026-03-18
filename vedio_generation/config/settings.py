#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置文件
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class Settings:
    """项目配置类"""
    
    # ==================== 路径配置 ====================
    # 项目根目录
    PROJECT_ROOT = PROJECT_ROOT
    
    # API配置文件路径
    API_CONFIG_FILE = PROJECT_ROOT / "config" / "api_config.txt"
    
    # ==================== 导演Agent配置 ====================
    # 质量评估通过阈值（1-10分）
    DIRECTOR_THRESHOLD = 7.0
    
    # 单个场景最大重试次数
    MAX_RETRIES = 2
    
    # 是否启用自动重试
    AUTO_RETRY = True
    
    # ==================== 视频生成配置 ====================
    # 视频时长（秒）
    VIDEO_DURATION = 10
    
    # 视频尺寸
    VIDEO_SIZE = "1792x1024"
    
    # Sora模型版本
    SORA_MODEL = "sora-2"
    
    # 是否添加水印
    WATERMARK = False
    
    # 是否私有
    PRIVATE = False
    
    # ==================== 评估配置 ====================
    # 评估模型
    EVALUATION_MODEL = "gemini-2.5-pro"
    
    # 评估维度权重
    EVALUATION_WEIGHTS = {
        "music_quality": 0.30,          # 音乐质量
        "content_consistency": 0.30,     # 内容一致性
        "opera_authenticity": 0.25,      # 京剧特色
        "technical_quality": 0.15        # 技术质量
    }
    
    # 各维度通过分数线
    DIMENSION_THRESHOLDS = {
        "music_quality": 6.0,
        "content_consistency": 7.0,
        "opera_authenticity": 6.0,
        "technical_quality": 6.0
    }
    
    # ==================== API配置 ====================
    # API查询配置
    MAX_STATUS_CHECKS = 60      # 最大查询次数
    STATUS_CHECK_INTERVAL = 10  # 查询间隔（秒）
    MAX_QUERY_ATTEMPTS = 60     # 最大查询次数（别名）
    QUERY_INTERVAL = 10         # 查询间隔（秒，别名）
    RETRY_INTERVAL = 10         # 重试间隔（秒）
    
    # API超时配置
    API_TIMEOUT = 30            # API请求超时（秒）
    
    # ==================== 目录配置 ====================
    # 数据目录
    DATA_DIR = PROJECT_ROOT / "data"
    SCRIPTS_DIR = DATA_DIR / "scripts"
    PROMPTS_DIR = DATA_DIR / "prompts"
    
    # 结果目录
    RESULTS_DIR = PROJECT_ROOT / "results"
    VIDEOS_DIR = RESULTS_DIR / "videos"
    APPROVED_DIR = VIDEOS_DIR / "approved"
    REJECTED_DIR = VIDEOS_DIR / "rejected"
    REPORTS_DIR = RESULTS_DIR / "reports"
    MERGED_DIR = RESULTS_DIR / "merged"
    
    # 文档目录
    DOCS_DIR = PROJECT_ROOT / "docs"
    
    # ==================== 日志配置 ====================
    # 日志文件路径
    LOG_FILE = PROJECT_ROOT / "pipeline.log"
    
    # 日志级别
    LOG_LEVEL = "INFO"
    
    # 日志格式
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==================== Prompt配置 ====================
    # Prompt模板强调项
    PROMPT_CONSTRAINTS = [
        "需要根据以下信息生成一个符合京剧特色的视频",
        "京剧的腔调需要符合传统",
        "台词严格按照给出的内容进行表演，不要自己添加台词",
        "人物形象参考提供的装扮设计和参考图片，不要偏离角色设定",
        "直接进行京剧表演，不要出现其他无关内容",
        "表演需要基于对话历史的上下文"
    ]
    
    # ==================== 视频合并配置 ====================
    # 是否默认启用视频合并
    AUTO_MERGE = False
    
    # 合并视频的编码器
    MERGE_CODEC = "libx264"
    
    # 合并视频的比特率
    MERGE_BITRATE = "5000k"
    
    @classmethod
    def ensure_directories(cls):
        """确保所有必要的目录存在"""
        directories = [
            cls.DATA_DIR,
            cls.SCRIPTS_DIR,
            cls.PROMPTS_DIR,
            cls.RESULTS_DIR,
            cls.VIDEOS_DIR,
            cls.APPROVED_DIR,
            cls.REJECTED_DIR,
            cls.REPORTS_DIR,
            cls.MERGED_DIR,
            cls.DOCS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_api_config(cls) -> tuple[str, str]:
        """
        读取API配置
        
        Returns:
            tuple: (api_key, api_base)
        """
        if not cls.API_CONFIG_FILE.exists():
            raise FileNotFoundError(f"API配置文件不存在: {cls.API_CONFIG_FILE}")
        
        with open(cls.API_CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        api_key = None
        api_base = None
        
        for line in content.strip().split('\n'):
            line = line.strip()
            if line.startswith('OPENAI_API_KEY'):
                api_key = line.split('=', 1)[1].strip().strip('"\'')
            elif line.startswith('OPENAI_API_BASE'):
                api_base = line.split('=', 1)[1].strip().strip('"\'')
        
        if not api_key or not api_base:
            raise ValueError("API配置不完整，请检查api_config.txt文件")
        
        return api_key, api_base


# 创建默认配置实例
settings = Settings()
