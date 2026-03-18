"""
视频合并器模块
提供视频合并功能（可选功能）
"""

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.file_manager import FileManager
from config.settings import Settings

logger = get_logger(__name__)


class VideoMerger:
    """视频合并器类，提供视频拼接功能"""
    
    def __init__(self):
        """初始化视频合并器"""
        self.settings = Settings()
        self.file_manager = FileManager()
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        logger.info("VideoMerger 初始化完成")
    
    def validate_video_files(self, video_paths: List[str]) -> List[str]:
        """
        验证视频文件列表
        
        Args:
            video_paths: 视频文件路径列表
            
        Returns:
            List[str]: 有效的视频文件路径列表
        """
        valid_paths = []
        for path in video_paths:
            if not os.path.exists(path):
                logger.warning(f"视频文件不存在，跳过: {path}")
                continue
            
            _, ext = os.path.splitext(path)
            if ext.lower() not in self.supported_formats:
                logger.warning(f"不支持的视频格式，跳过: {path}")
                continue
            
            valid_paths.append(path)
        
        logger.info(f"验证完成，有效视频文件: {len(valid_paths)}/{len(video_paths)}")
        return valid_paths
    
    def merge_videos(self, video_paths: List[str], output_path: Optional[str] = None,
                    task_name: str = "merged") -> Dict:
        """
        合并多个视频
        
        Args:
            video_paths: 视频文件路径列表
            output_path: 输出视频路径，如果为None则自动生成
            task_name: 任务名称，用于生成输出文件名
            
        Returns:
            Dict: 包含合并结果的字典
        """
        if not video_paths:
            raise ValueError("视频路径列表不能为空")
        
        # 验证所有视频文件
        valid_paths = self.validate_video_files(video_paths)
        
        if not valid_paths:
            raise ValueError("没有有效的视频文件")
        
        if len(valid_paths) < 2:
            logger.warning("只有一个有效视频文件，无需合并")
            return {
                'success': False,
                'message': '只有一个有效视频文件，无需合并',
                'input_count': len(valid_paths),
                'output_path': None
            }
        
        try:
            logger.info(f"开始合并 {len(valid_paths)} 个视频...")
            
            # 加载所有视频片段
            clips = []
            for i, path in enumerate(valid_paths, 1):
                logger.info(f"加载视频 {i}/{len(valid_paths)}: {path}")
                clip = VideoFileClip(path)
                clips.append(clip)
            
            # 合并视频
            logger.info("正在合并视频...")
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # 生成输出路径
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = self.settings.MERGED_DIR
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"{task_name}_complete_{timestamp}.mp4")
            
            # 输出视频
            logger.info(f"正在写入合并后的视频: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # 获取输出视频信息
            output_info = {
                'duration': final_clip.duration,
                'fps': final_clip.fps,
                'size': final_clip.size,
                'width': final_clip.w,
                'height': final_clip.h
            }
            
            # 清理资源
            for clip in clips:
                clip.close()
            final_clip.close()
            
            # 生成合并报告
            merge_report = {
                'success': True,
                'task_name': task_name,
                'input_videos': [
                    {
                        'path': path,
                        'filename': os.path.basename(path)
                    }
                    for path in valid_paths
                ],
                'input_count': len(valid_paths),
                'output_path': output_path,
                'output_info': output_info,
                'timestamp': datetime.now().isoformat()
            }
            
            # 保存合并报告
            report_path = output_path.replace('.mp4', '_merge_report.json')
            self.file_manager.write_json(report_path, merge_report)
            
            logger.info(f"视频合并成功: {output_path}")
            logger.info(f"合并报告已保存: {report_path}")
            
            return merge_report
            
        except Exception as e:
            logger.error(f"合并视频失败: {e}")
            raise
    
    def merge_approved_videos(self, task_name: str, scene_numbers: Optional[List[int]] = None) -> Dict:
        """
        合并已通过评估的视频
        
        Args:
            task_name: 任务名称
            scene_numbers: 场景编号列表，如果为None则合并所有场景
            
        Returns:
            Dict: 包含合并结果的字典
        """
        approved_dir = self.settings.APPROVED_DIR
        
        if not approved_dir.exists():
            raise ValueError(f"已通过视频目录不存在: {approved_dir}")
        
        # 查找所有已通过的视频
        all_videos = list(approved_dir.glob(f"{task_name}_场景*.mp4"))
        
        if not all_videos:
            raise ValueError(f"未找到任务 '{task_name}' 的已通过视频")
        
        # 如果指定了场景编号，则筛选
        if scene_numbers:
            video_paths = []
            for scene_num in sorted(scene_numbers):
                matching_videos = [
                    str(v) for v in all_videos 
                    if f"场景{scene_num}" in v.name
                ]
                if matching_videos:
                    video_paths.append(matching_videos[0])
                else:
                    logger.warning(f"未找到场景 {scene_num} 的视频")
        else:
            # 按场景编号排序
            video_paths = sorted([str(v) for v in all_videos])
        
        if not video_paths:
            raise ValueError("没有找到要合并的视频")
        
        logger.info(f"找到 {len(video_paths)} 个已通过的视频待合并")
        
        # 合并视频
        return self.merge_videos(video_paths, task_name=task_name)
    
    def get_merge_preview(self, video_paths: List[str]) -> Dict:
        """
        获取合并预览信息（不实际合并）
        
        Args:
            video_paths: 视频文件路径列表
            
        Returns:
            Dict: 包含预览信息的字典
        """
        valid_paths = self.validate_video_files(video_paths)
        
        if not valid_paths:
            return {
                'valid': False,
                'message': '没有有效的视频文件'
            }
        
        try:
            total_duration = 0
            videos_info = []
            
            for path in valid_paths:
                clip = VideoFileClip(path)
                info = {
                    'path': path,
                    'filename': os.path.basename(path),
                    'duration': clip.duration,
                    'fps': clip.fps,
                    'size': clip.size
                }
                videos_info.append(info)
                total_duration += clip.duration
                clip.close()
            
            return {
                'valid': True,
                'video_count': len(valid_paths),
                'total_duration': total_duration,
                'videos': videos_info
            }
            
        except Exception as e:
            logger.error(f"获取合并预览失败: {e}")
            return {
                'valid': False,
                'message': f'获取预览失败: {str(e)}'
            }
