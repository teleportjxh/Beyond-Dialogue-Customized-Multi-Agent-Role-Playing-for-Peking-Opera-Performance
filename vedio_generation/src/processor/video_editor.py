"""
视频编辑器模块
提供视频处理功能，包括帧提取、视频信息获取、裁剪等
"""

import cv2
import numpy as np
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
import os
from typing import Dict, Optional, Tuple
from pathlib import Path

from ..utils.logger import get_logger
from config.settings import Settings

logger = get_logger(__name__)


class VideoEditor:
    """视频编辑器类，提供视频处理功能"""
    
    def __init__(self):
        """初始化视频编辑器"""
        self.settings = Settings()
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        logger.info("VideoEditor 初始化完成")
    
    def validate_video_file(self, video_path: str) -> bool:
        """
        验证视频文件是否存在且格式支持
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            bool: 文件是否有效
        """
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        _, ext = os.path.splitext(video_path)
        if ext.lower() not in self.supported_formats:
            logger.error(f"不支持的视频格式: {ext}")
            return False
        
        return True
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict: 包含视频信息的字典
        """
        if not self.validate_video_file(video_path):
            return {}
        
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': clip.size,
                'width': clip.w,
                'height': clip.h,
                'path': video_path,
                'filename': os.path.basename(video_path)
            }
            clip.close()
            logger.info(f"成功获取视频信息: {video_path}")
            return info
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {}
    
    def capture_last_frame(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        截取视频的最后一帧并保存为图片
        
        Args:
            video_path: 视频文件路径
            output_path: 输出图片路径，如果为None则自动生成
            
        Returns:
            str: 保存的图片路径
        """
        if not self.validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")
        
        try:
            # 使用OpenCV读取视频
            cap = cv2.VideoCapture(video_path)
            
            # 获取视频总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 跳转到最后一帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
            
            # 读取最后一帧
            ret, frame = cap.read()
            
            if not ret:
                raise ValueError("无法读取视频的最后一帧")
            
            # 生成输出路径
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_dir = self.settings.RESULTS_DIR / "frames"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{base_name}_last_frame.jpg")
            
            # 保存图片
            cv2.imwrite(output_path, frame)
            cap.release()
            
            logger.info(f"成功截取最后一帧: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"截取最后一帧失败: {e}")
            raise
    
    def capture_frame_at_time(self, video_path: str, time_seconds: float, 
                             output_path: Optional[str] = None) -> str:
        """
        截取视频指定时间的帧
        
        Args:
            video_path: 视频文件路径
            time_seconds: 指定时间（秒）
            output_path: 输出图片路径
            
        Returns:
            str: 保存的图片路径
        """
        if not self.validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")
        
        try:
            clip = VideoFileClip(video_path)
            
            # 确保时间在视频范围内
            if time_seconds > clip.duration:
                time_seconds = clip.duration - 0.1
            
            # 生成输出路径
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_dir = self.settings.RESULTS_DIR / "frames"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{base_name}_frame_{time_seconds:.1f}s.jpg")
            
            # 截取帧并保存
            frame = clip.get_frame(time_seconds)
            
            # 转换颜色格式 (RGB to BGR for OpenCV)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, frame_bgr)
            
            clip.close()
            logger.info(f"成功截取 {time_seconds}s 处的帧: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"截取指定时间帧失败: {e}")
            raise
    
    def resize_video(self, video_path: str, size: Tuple[int, int], 
                    output_path: Optional[str] = None) -> str:
        """
        调整视频尺寸
        
        Args:
            video_path: 输入视频路径
            size: 目标尺寸 (width, height)
            output_path: 输出视频路径
            
        Returns:
            str: 输出视频路径
        """
        if not self.validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")
        
        try:
            clip = VideoFileClip(video_path)
            resized_clip = clip.resize(size)
            
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_dir = self.settings.RESULTS_DIR / "processed"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{base_name}_resized_{size[0]}x{size[1]}.mp4")
            
            resized_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            clip.close()
            resized_clip.close()
            
            logger.info(f"成功调整视频尺寸: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"调整视频尺寸失败: {e}")
            raise
    
    def trim_video(self, video_path: str, start_time: float, end_time: float, 
                  output_path: Optional[str] = None) -> str:
        """
        裁剪视频
        
        Args:
            video_path: 输入视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_path: 输出视频路径
            
        Returns:
            str: 输出视频路径
        """
        if not self.validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")
        
        try:
            clip = VideoFileClip(video_path)
            
            # 确保时间范围有效
            if start_time < 0:
                start_time = 0
            if end_time > clip.duration:
                end_time = clip.duration
            if start_time >= end_time:
                raise ValueError("开始时间必须小于结束时间")
            
            trimmed_clip = clip.subclip(start_time, end_time)
            
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_dir = self.settings.RESULTS_DIR / "processed"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{base_name}_trimmed_{start_time:.1f}_{end_time:.1f}.mp4")
            
            trimmed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            clip.close()
            trimmed_clip.close()
            
            logger.info(f"成功裁剪视频: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"裁剪视频失败: {e}")
            raise
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径
            
        Returns:
            str: 输出音频路径
        """
        if not self.validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")
        
        try:
            clip = VideoFileClip(video_path)
            
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_dir = self.settings.RESULTS_DIR / "audio"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{base_name}_audio.mp3")
            
            # 提取音频
            audio = clip.audio
            if audio is None:
                raise ValueError("视频没有音频轨道")
            
            audio.write_audiofile(output_path)
            
            clip.close()
            logger.info(f"成功提取音频: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"提取音频失败: {e}")
            raise
