#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sora2 视频生成器模块
提供视频生成的核心功能
"""

import json
import requests
import time
import os
from typing import Dict, Any, Optional, Tuple

from config.settings import Settings
from src.utils.logger import get_logger
from src.utils.file_manager import FileManager
from src.generator.prompt_builder import PromptBuilder


class SoraGenerator:
    """Sora2 视频生成器类"""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化视频生成器
        
        Args:
            settings: 配置对象，如果为None则使用默认配置
        """
        self.settings = settings or Settings()
        self.logger = get_logger(__name__)
        self.file_manager = FileManager()
        self.prompt_builder = PromptBuilder()
        
        # 读取API配置
        self.api_key, self.api_base = self._load_api_config()
        
        self.logger.info("🎬 Sora2视频生成器初始化完成")
        self.logger.info(f"📋 配置: 最大重试{self.settings.MAX_RETRIES}次，查询间隔{self.settings.RETRY_INTERVAL}秒")
    
    def _load_api_config(self) -> Tuple[str, str]:
        """
        加载API配置
        
        Returns:
            tuple: (api_key, api_base)
        """
        try:
            # get_api_config() 直接返回 (api_key, api_base) 元组
            api_key, api_base = self.settings.get_api_config()
            
            if not api_key or not api_base:
                raise ValueError("API配置不完整")
            
            self.logger.info(f"✓ API配置加载成功")
            self.logger.info(f"  - API Base: {api_base}")
            self.logger.info(f"  - API Key: {api_key[:20]}...")
            
            return api_key, api_base
            
        except Exception as e:
            self.logger.error(f"❌ 加载API配置失败: {str(e)}")
            raise
    
    def create_video_task(self, prompt: str, **kwargs) -> Optional[str]:
        """
        创建视频生成任务
        
        Args:
            prompt: 视频生成的prompt文本
            **kwargs: 其他可选参数
                - seconds: 视频时长，默认从配置读取
                - size: 视频尺寸，默认从配置读取
                - watermark: 是否添加水印，默认false
                - private: 是否私有，默认false
                
        Returns:
            str: 视频任务ID，失败返回None
        """
        url = f"{self.api_base}videos"
        
        # 构建请求参数
        payload = {
            'model': 'sora-2',
            'prompt': prompt,
            'seconds': str(kwargs.get('seconds', self.settings.VIDEO_DURATION)),
            'input_reference': None,
            'size': kwargs.get('size', self.settings.VIDEO_SIZE),
            'watermark': kwargs.get('watermark', 'false'),
            'private': kwargs.get('private', 'false'),
            'character_url': None,
            'character_timestamps': None
        }
        
        # 过滤None值
        filtered_payload = {k: v for k, v in payload.items() if v is not None}
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        self.logger.info("\n🚀 创建视频任务...")
        self.logger.debug(f"请求URL: {url}")
        self.logger.debug(f"请求参数: {filtered_payload}")
        
        try:
            response = requests.post(url, headers=headers, data=filtered_payload)
            
            self.logger.debug(f"响应状态码: {response.status_code}")
            self.logger.debug(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')
                if video_id:
                    self.logger.info(f"✓ 视频任务创建成功，ID: {video_id}")
                    return video_id
                else:
                    self.logger.error("❌ 响应中未找到视频ID")
                    return None
            else:
                self.logger.error(f"❌ 创建视频任务失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 创建视频任务异常: {str(e)}")
            return None
    
    def check_video_status(self, video_id: str) -> Optional[str]:
        """
        查询视频生成状态
        
        Args:
            video_id: 视频任务ID
            
        Returns:
            str: 视频URL（如果完成），失败或超时返回None
        """
        url = f"{self.api_base}videos/{video_id}"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        self.logger.info(f"\n🔍 开始查询视频状态（最多查询{self.settings.MAX_QUERY_ATTEMPTS}次，每{self.settings.QUERY_INTERVAL}秒查询一次）...")
        
        for attempt in range(1, self.settings.MAX_QUERY_ATTEMPTS + 1):
            self.logger.info(f"\n第 {attempt}/{self.settings.MAX_QUERY_ATTEMPTS} 次查询...")
            
            try:
                response = requests.get(url, headers=headers)
                
                self.logger.debug(f"响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', 'unknown')
                    
                    self.logger.info(f"当前状态: {status}")
                    
                    if status == 'completed':
                        video_url = result.get('url')
                        self.logger.info(f"\n✓ 视频生成成功！")
                        self.logger.info(f"视频URL: {video_url}")
                        return video_url
                    elif status == 'failed':
                        error_msg = result.get('error', '未知错误')
                        self.logger.error(f"\n❌ 视频生成失败")
                        self.logger.error(f"错误信息: {error_msg}")
                        return None
                    else:
                        # 继续等待
                        if attempt < self.settings.MAX_QUERY_ATTEMPTS:
                            self.logger.info(f"等待 {self.settings.QUERY_INTERVAL} 秒后继续查询...")
                            time.sleep(self.settings.QUERY_INTERVAL)
                else:
                    self.logger.warning(f"查询请求失败: {response.status_code} - {response.text}")
                    if attempt < self.settings.MAX_QUERY_ATTEMPTS:
                        self.logger.info(f"等待 {self.settings.QUERY_INTERVAL} 秒后重试...")
                        time.sleep(self.settings.QUERY_INTERVAL)
                        
            except Exception as e:
                self.logger.error(f"查询异常: {str(e)}")
                if attempt < self.settings.MAX_QUERY_ATTEMPTS:
                    self.logger.info(f"等待 {self.settings.QUERY_INTERVAL} 秒后重试...")
                    time.sleep(self.settings.QUERY_INTERVAL)
        
        # 达到最大查询次数
        self.logger.warning(f"\n⏰ 已达到最大查询次数（{self.settings.MAX_QUERY_ATTEMPTS}次），视频可能仍在生成中")
        self.logger.warning("请稍后手动查询视频状态")
        return None
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        下载视频文件
        
        Args:
            video_url: 视频下载URL
            output_path: 保存的文件路径
            
        Returns:
            bool: 下载是否成功
        """
        self.logger.info(f"\n📥 开始下载视频...")
        self.logger.info(f"视频URL: {video_url}")
        self.logger.info(f"保存路径: {output_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            response = requests.get(video_url, stream=True)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # 显示下载进度
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                if downloaded_size % (1024 * 1024) == 0:  # 每MB记录一次
                                    self.logger.debug(f"下载进度: {progress:.1f}% ({downloaded_size}/{total_size} bytes)")
                
                self.logger.info(f"✓ 视频下载成功: {output_path}")
                return True
            else:
                self.logger.error(f"❌ 下载失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 下载异常: {str(e)}")
            return False
    
    def generate_video(self, prompt_data: Dict[str, Any], 
                      scene_index: int,
                      output_dir: Optional[str] = None) -> Optional[str]:
        """
        生成单个视频
        
        Args:
            prompt_data: prompt数据字典
            scene_index: 场景索引
            output_dir: 输出目录，如果为None则使用默认配置
            
        Returns:
            str: 生成的视频文件路径，失败返回None
        """
        self.logger.info("=" * 60)
        self.logger.info(f"🎬 开始生成场景 {scene_index + 1} 的视频")
        self.logger.info("=" * 60)
        
        # 使用PromptBuilder构建prompt
        prompt_text = self.prompt_builder.build_prompt(prompt_data)
        
        # 创建视频任务
        self.logger.info("\n📖 步骤1: 创建视频任务...")
        video_id = self.create_video_task(prompt_text)
        
        if not video_id:
            self.logger.error("❌ 无法创建视频任务")
            return None
        
        # 查询视频状态
        self.logger.info("\n📖 步骤2: 查询视频状态...")
        video_url = self.check_video_status(video_id)
        
        if not video_url:
            self.logger.error("❌ 无法获取视频URL")
            return None
        
        # 下载视频
        self.logger.info("\n📖 步骤3: 下载视频...")
        
        # 确定输出目录
        if output_dir is None:
            output_dir = str(self.settings.VIDEOS_DIR)
        
        # 生成文件名
        script_name = prompt_data.get('剧本名字', 'unknown')
        filename = f"{output_dir}/{script_name}_场景{scene_index + 1}.mp4"
        
        success = self.download_video(video_url, filename)
        
        if success:
            self.logger.info("\n🎉 视频生成完成！")
            self.logger.info(f"✓ 视频已保存到: {filename}")
            return filename
        else:
            self.logger.error("\n❌ 视频下载失败")
            return None
    
    def generate_videos_batch(self, prompts_file: str, 
                             output_dir: Optional[str] = None) -> list:
        """
        批量生成视频
        
        Args:
            prompts_file: prompts文件路径
            output_dir: 输出目录
            
        Returns:
            list: 成功生成的视频文件路径列表
        """
        self.logger.info("=" * 60)
        self.logger.info("🎬 开始批量视频生成")
        self.logger.info("=" * 60)
        
        # 读取prompts数据
        try:
            prompts_data = self.file_manager.read_json(prompts_file)
            self.logger.info(f"✓ 成功读取 {len(prompts_data)} 个prompt")
        except Exception as e:
            self.logger.error(f"❌ 读取prompts文件失败: {str(e)}")
            return []
        
        # 生成视频
        generated_videos = []
        
        for i, prompt_data in enumerate(prompts_data):
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"处理第 {i + 1}/{len(prompts_data)} 个场景")
            self.logger.info(f"{'=' * 60}")
            
            video_path = self.generate_video(prompt_data, i, output_dir)
            
            if video_path:
                generated_videos.append(video_path)
                self.logger.info(f"✓ 场景 {i + 1} 生成成功")
            else:
                self.logger.warning(f"⚠ 场景 {i + 1} 生成失败")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"批量生成完成: {len(generated_videos)}/{len(prompts_data)} 个视频成功")
        self.logger.info("=" * 60)
        
        return generated_videos


if __name__ == "__main__":
    # 测试代码
    generator = SoraGenerator()
    
    # 测试单个视频生成
    test_prompt_file = "generated_scripts/煮酒论英雄_prompts.json"
    
    if os.path.exists(test_prompt_file):
        result = generator.generate
