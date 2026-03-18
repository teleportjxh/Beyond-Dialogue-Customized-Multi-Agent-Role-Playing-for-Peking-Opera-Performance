"""
Sora2视频生成器
"""
import requests
import time
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Sora2Generator:
    """Sora2 API视频生成器"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化生成器
        
        Args:
            api_key: API密钥，如果不提供则从config读取
            base_url: API基础URL，如果不提供则从config读取
        """
        # 尝试从config导入视频生成专用配置
        try:
            from config.api_config import VIDEO_API_KEY, VIDEO_API_BASE_URL
            self.api_key = api_key or VIDEO_API_KEY
            self.base_url = base_url or VIDEO_API_BASE_URL
        except ImportError:
            self.api_key = api_key
            self.base_url = base_url or "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("未提供API密钥")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"Sora2Generator初始化成功，使用视频API: {self.base_url}")
    
    def generate_video(
        self,
        prompt: str,
        output_path: str,
        duration: int = 10,
        resolution: str = "1280x720",
        download: bool = True,
        enhance_prompt: bool = True
    ) -> Dict:
        """
        生成视频
        
        Args:
            prompt: 视频生成prompt
            output_path: 输出路径
            duration: 视频时长（秒）
            resolution: 分辨率
            download: 是否下载视频到本地（默认True）
            enhance_prompt: 是否增强prompt（默认True）
            
        Returns:
            生成结果字典
        """
        try:
            # 增强prompt
            if enhance_prompt:
                enhanced_prompt = self._enhance_prompt(prompt)
                logger.info(f"原始prompt: {prompt[:100]}...")
                logger.info(f"增强prompt: {enhanced_prompt[:100]}...")
            else:
                enhanced_prompt = prompt
            
            logger.info(f"开始生成视频...")
            
            # 创建生成任务
            task_id = self._create_generation_task(enhanced_prompt, duration, resolution)
            
            if not task_id:
                return {
                    'success': False,
                    'error': '创建生成任务失败'
                }
            
            # 轮询任务状态
            video_url = self._poll_task_status(task_id)
            
            if not video_url:
                return {
                    'success': False,
                    'error': '视频生成失败或超时'
                }
            
            # 根据参数决定是否下载
            if download:
                success = self._download_video(video_url, output_path)
                
                if success:
                    logger.info(f"视频生成并下载成功: {output_path}")
                    return {
                        'success': True,
                        'output_path': output_path,
                        'video_url': video_url
                    }
                else:
                    logger.warning(f"视频生成成功但下载失败，返回URL")
                    return {
                        'success': True,
                        'output_path': None,
                        'video_url': video_url,
                        'warning': '下载失败但视频URL可用'
                    }
            else:
                logger.info(f"视频生成成功（未下载）: {video_url}")
                return {
                    'success': True,
                    'output_path': None,
                    'video_url': video_url
                }
                
        except Exception as e:
            logger.error(f"视频生成异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_generation_task(
        self,
        prompt: str,
        duration: int,
        resolution: str
    ) -> Optional[str]:
        """创建视频生成任务"""
        try:
            url = f"{self.base_url}/videos"
            
            # 根据API测试结果，不使用duration参数，使用size代替resolution
            payload = {
                "model": "sora-2",
                "prompt": prompt,
                "size": resolution  # API使用size而不是resolution
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('id')
                logger.info(f"创建任务成功: {task_id}")
                return task_id
            else:
                logger.error(f"创建任务失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"创建任务异常: {e}")
            return None
    
    def _poll_task_status(
        self,
        task_id: str,
        max_wait_time: int = 1800,
        poll_interval: int = 10
    ) -> Optional[str]:
        """轮询任务状态（超时时间30分钟）"""
        try:
            url = f"{self.base_url}/videos/{task_id}"
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    logger.info(f"任务状态: {status}")
                    logger.debug(f"完整响应: {data}")
                    
                    if status == 'completed':
                        logger.info("检测到completed状态，开始提取视频URL...")
                        
                        # 尝试多种可能的URL位置
                        video_url = None
                        
                        # 1. 检查output字段
                        if 'output' in data:
                            logger.debug(f"找到output字段，类型: {type(data['output'])}")
                            if isinstance(data['output'], dict):
                                video_url = data['output'].get('url') or data['output'].get('video_url')
                                logger.debug(f"从output字典提取: {video_url}")
                            elif isinstance(data['output'], str):
                                video_url = data['output']
                                logger.debug(f"output是字符串: {video_url}")
                            elif isinstance(data['output'], list) and len(data['output']) > 0:
                                # 可能是数组格式
                                first_item = data['output'][0]
                                if isinstance(first_item, dict):
                                    video_url = first_item.get('url') or first_item.get('video_url')
                                elif isinstance(first_item, str):
                                    video_url = first_item
                                logger.debug(f"从output数组提取: {video_url}")
                        
                        # 2. 检查顶层字段
                        if not video_url:
                            logger.debug("output中未找到URL，检查顶层字段...")
                            video_url = (data.get('url') or 
                                       data.get('video_url') or 
                                       data.get('result_url') or
                                       data.get('download_url') or
                                       data.get('file_url'))
                            logger.debug(f"从顶层字段提取: {video_url}")
                        
                        # 3. 检查data字段
                        if not video_url and 'data' in data:
                            logger.debug("检查data字段...")
                            data_field = data['data']
                            if isinstance(data_field, dict):
                                video_url = data_field.get('url') or data_field.get('video_url')
                            elif isinstance(data_field, list) and len(data_field) > 0:
                                first_item = data_field[0]
                                if isinstance(first_item, dict):
                                    video_url = first_item.get('url') or first_item.get('video_url')
                            logger.debug(f"从data字段提取: {video_url}")
                        
                        if video_url:
                            logger.info(f"✓ 成功提取视频URL: {video_url}")
                            return video_url
                        else:
                            logger.error(f"✗ 任务已完成但未找到视频URL！")
                            logger.error(f"完整响应数据: {data}")
                            logger.error(f"响应中的所有键: {list(data.keys())}")
                            # 不返回None，而是继续等待一次，可能是API延迟
                            logger.warning("将继续轮询一次以防API延迟...")
                            
                    elif status == 'failed':
                        error = data.get('error', '未知错误')
                        logger.error(f"任务失败: {error}")
                        return None
                    elif status in ['queued', 'in_progress', 'processing']:
                        # 正常等待状态
                        pass
                    else:
                        logger.warning(f"未知状态: {status}")
                    
                    # 继续等待
                    time.sleep(poll_interval)
                else:
                    logger.error(f"查询任务失败: {response.status_code}")
                    return None
            
            logger.error("任务超时")
            return None
            
        except Exception as e:
            logger.error(f"轮询任务异常: {e}")
            return None
    
    def _enhance_prompt(self, base_prompt: str) -> str:
        """
        增强prompt以提高视频质量和添加音频要求
        
        Args:
            base_prompt: 基础prompt
            
        Returns:
            增强后的prompt
        """
        # 检查是否已经包含质量和音频要求
        has_quality = any(keyword in base_prompt.lower() for keyword in 
                         ['high quality', 'professional', 'cinematic', 'hd', '高质量'])
        has_audio = any(keyword in base_prompt.lower() for keyword in 
                       ['singing', 'music', 'audio', 'sound', 'vocal', '唱', '音乐', '声音'])
        
        enhanced_parts = []
        
        # 添加质量要求
        if not has_quality:
            enhanced_parts.append("High-quality professional video production.")
        
        # 添加基础prompt
        enhanced_parts.append(base_prompt)
        
        # 添加视觉质量要求
        if not has_quality:
            enhanced_parts.append(
                "Cinematic lighting with rich colors and textures. "
                "Smooth, fluid movements. Professional camera work."
            )
        
        # 添加音频要求
        if not has_audio:
            enhanced_parts.append(
                "With authentic traditional Chinese opera singing and musical accompaniment. "
                "Clear vocal delivery with proper operatic technique."
            )
        
        # 添加风格要求
        enhanced_parts.append(
            "Style: Traditional Chinese Peking Opera, theatrical, elegant, culturally authentic. "
            "High definition production value."
        )
        
        enhanced_prompt = " ".join(enhanced_parts)
        return enhanced_prompt
    
    def _download_video(self, video_url: str, output_path: str) -> bool:
        """下载视频"""
        try:
            logger.info(f"下载视频: {video_url}")
            
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(video_url, stream=True, timeout=300)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"视频下载完成: {output_path}")
                return True
            else:
                logger.error(f"下载失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"下载视频异常: {e}")
            return False
