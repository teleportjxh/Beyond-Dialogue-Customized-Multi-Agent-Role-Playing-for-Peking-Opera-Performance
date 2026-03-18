"""
智能视频生成流水线
实现导演Agent指导的迭代生成机制
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..extractor.simple_prompt_extractor import extract_prompts_simple
from ..evaluator.director_agent import DirectorAgent
from ..generator.sora2_generator import Sora2Generator

logger = logging.getLogger(__name__)


class IntelligentPipeline:
    """
    智能视频生成流水线
    
    核心流程：
    1. 从generated_scripts提取prompt
    2. 生成视频
    3. 导演评估
    4. 如果不通过，根据反馈改进prompt并重新生成
    5. 重复3-4直到导演满意
    """
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        script_folder: str = "generated_scripts",
        output_folder: str = "generated_videos/output",
        max_iterations: int = 5
    ):
        """
        初始化流水线
        
        Args:
            api_key: API密钥（如果不提供，将从config读取）
            base_url: API基础URL（如果不提供，将从config读取）
            script_folder: 剧本文件夹路径
            output_folder: 输出文件夹路径
            max_iterations: 最大迭代次数（防止无限循环）
        """
        # 尝试从config导入
        try:
            from config.api_config import API_KEY, API_BASE_URL, VIDEO_API_KEY, VIDEO_API_BASE_URL
            self.api_key = api_key or API_KEY
            self.base_url = base_url or API_BASE_URL
            self.video_api_key = VIDEO_API_KEY
            self.video_api_base_url = VIDEO_API_BASE_URL
        except ImportError:
            self.api_key = api_key
            self.base_url = base_url
            self.video_api_key = api_key
            self.video_api_base_url = base_url
        
        if not self.api_key:
            raise ValueError("未提供API密钥")
        
        # 初始化各个组件
        # 评估和提取使用原API，视频生成使用专用视频API
        self.script_folder = script_folder
        self.director = DirectorAgent(api_key=self.api_key, base_url=self.base_url)
        self.generator = Sora2Generator(
            api_key=self.video_api_key,
            base_url=self.video_api_base_url
        )
        
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        self.max_iterations = max_iterations
        
        # 统计信息
        self.stats = {
            'total_videos': 0,
            'passed_videos': 0,
            'failed_videos': 0,
            'total_iterations': 0
        }
    
    def run(self, script_name: str) -> Dict:
        """
        运行完整流水线
        
        Args:
            script_name: 剧本名称（如"煮酒论英雄"）
            
        Returns:
            运行结果报告
        """
        logger.info(f"=" * 60)
        logger.info(f"开始处理剧本: {script_name}")
        logger.info(f"=" * 60)
        
        # 1. 使用简化提取器直接从JSON提取prompts（不使用大模型）
        try:
            video_prompts = extract_prompts_simple(script_name)
        except Exception as e:
            logger.error(f"提取prompts失败: {e}")
            return {
                'success': False,
                'error': f'提取prompts失败: {e}'
            }
        
        if not video_prompts:
            return {
                'success': False,
                'error': '未提取到任何视频prompt'
            }
        
        logger.info(f"提取到 {len(video_prompts)} 个视频prompt")
        
        # 3. 逐个生成视频
        results = []
        
        for i, prompt_data in enumerate(video_prompts, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"处理视频 {i}/{len(video_prompts)}")
            logger.info(f"Turn: {prompt_data['turn']}, 角色: {prompt_data['character']}")
            logger.info(f"{'=' * 60}")
            
            result = self._generate_video_with_director_guidance(
                prompt_data,
                script_name,
                i
            )
            
            results.append(result)
            
            # 更新统计
            self.stats['total_videos'] += 1
            if result['success']:
                self.stats['passed_videos'] += 1
            else:
                self.stats['failed_videos'] += 1
        
        # 4. 生成报告
        report = self._generate_report(script_name, results)
        
        # 5. 保存报告
        report_path = self.output_folder / f"{script_name}_pipeline_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"流水线完成")
        logger.info(f"总视频数: {self.stats['total_videos']}")
        logger.info(f"通过: {self.stats['passed_videos']}")
        logger.info(f"失败: {self.stats['failed_videos']}")
        logger.info(f"总迭代次数: {self.stats['total_iterations']}")
        logger.info(f"报告已保存: {report_path}")
        logger.info(f"{'=' * 60}")
        
        return report
    
    def _generate_video_with_director_guidance(
        self,
        prompt_data: Dict,
        script_name: str,
        video_index: int
    ) -> Dict:
        """
        使用导演指导生成视频
        
        核心逻辑：
        1. 使用初始prompt生成视频
        2. 导演评估
        3. 如果不通过，根据反馈改进prompt（保留场景和装扮）
        4. 重新生成
        5. 重复2-4直到通过或达到最大迭代次数
        
        Args:
            prompt_data: prompt数据
            script_name: 剧本名称
            video_index: 视频索引
            
        Returns:
            生成结果
        """
        turn = prompt_data['turn']
        character = prompt_data['character']
        current_prompt = prompt_data['prompt']
        
        # 提取并保存基础信息（场景和装扮在迭代中保持不变）
        scene_desc = prompt_data.get('scene_desc', '')
        costume_desc = prompt_data.get('costume_desc', '')
        
        # 期望内容（用于导演评估）
        expected_content = {
            'character': character,
            'emotion': prompt_data.get('emotion', ''),
            'content_type': prompt_data.get('content_type', ''),
            'content_text': prompt_data.get('content_text', '')
        }
        
        iteration_history = []
        
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\n--- 迭代 {iteration}/{self.max_iterations} ---")
            logger.info(f"当前Prompt: {current_prompt[:200]}...")
            
            # 生成视频
            output_filename = f"{script_name}_turn{turn}_iter{iteration}.mp4"
            output_path = str(self.output_folder / output_filename)
            
            logger.info("生成视频中...")
            gen_result = self.generator.generate_video(
                prompt=current_prompt,
                output_path=output_path,
                duration=12,  # 10-15秒，取中间值
                download=True,  # 下载到本地作为备份
                enhance_prompt=False  # 禁用prompt增强，保持简洁
            )
            
            if not gen_result.get('success'):
                logger.error(f"视频生成失败: {gen_result.get('error')}")
                iteration_history.append({
                    'iteration': iteration,
                    'prompt': current_prompt,
                    'generation_result': gen_result,
                    'evaluation': None
                })
                continue
            
            # 提取视频URL和本地路径
            video_url = gen_result.get('video_url')
            video_path = gen_result.get('output_path')
            
            logger.info(f"视频生成成功")
            logger.info(f"视频URL: {video_url}")
            if video_path:
                logger.info(f"本地路径: {video_path}")
            
            # 导演评估（优先使用URL，本地路径作为降级方案）
            logger.info("导演评估中（使用视频URL）...")
            passed, evaluation, improved_prompt = self.director.analyze_and_improve(
                video_url=video_url,
                original_prompt=current_prompt,
                expected_content=expected_content,
                video_path=video_path,      # 作为降级方案
                scene_desc=scene_desc,      # 传递场景信息
                costume_desc=costume_desc   # 传递装扮信息
            )
            
            # 记录本次迭代
            iteration_history.append({
                'iteration': iteration,
                'prompt': current_prompt,
                'generation_result': gen_result,
                'evaluation': evaluation,
                'improved_prompt': improved_prompt
            })
            
            self.stats['total_iterations'] += 1
            
            # 打印评估摘要
            logger.info("\n" + self.director.get_evaluation_summary(evaluation))
            
            if passed:
                logger.info(f"\n✓ 视频通过导演审核！(迭代{iteration}次)")
                return {
                    'success': True,
                    'turn': turn,
                    'character': character,
                    'final_video': video_path or video_url,
                    'video_url': video_url,
                    'iterations': iteration,
                    'iteration_history': iteration_history,
                    'final_evaluation': evaluation
                }
            
            # 未通过，准备下一次迭代
            if iteration < self.max_iterations:
                logger.info(f"\n✗ 视频未通过，准备改进prompt...")
                
                if improved_prompt:
                    current_prompt = improved_prompt
                    logger.info(f"改进后的Prompt: {current_prompt[:200]}...")
                else:
                    logger.warning("未能生成改进prompt，使用原prompt重试")
            else:
                logger.warning(f"\n✗ 达到最大迭代次数({self.max_iterations})，视频仍未通过")
        
        # 所有迭代都失败
        return {
            'success': False,
            'turn': turn,
            'character': character,
            'error': f'达到最大迭代次数({self.max_iterations})仍未通过',
            'iterations': self.max_iterations,
            'iteration_history': iteration_history
        }
    
    def _generate_report(self, script_name: str, results: List[Dict]) -> Dict:
        """生成流水线报告"""
        
        passed_results = [r for r in results if r.get('success')]
        failed_results = [r for r in results if not r.get('success')]
        
        total_iterations = sum(r.get('iterations', 0) for r in results)
        avg_iterations = total_iterations / len(results) if results else 0
        
        report = {
            'script_name': script_name,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_videos': len(results),
                'passed': len(passed_results),
                'failed': len(failed_results),
                'pass_rate': len(passed_results) / len(results) if results else 0,
                'total_iterations': total_iterations,
                'avg_iterations_per_video': avg_iterations
            },
            'passed_videos': [
                {
                    'turn': r['turn'],
                    'character': r['character'],
                    'video_path': r['final_video'],
                    'iterations': r['iterations'],
                    'final_score': r['final_evaluation'].get('overall_score', 0)
                }
                for r in passed_results
            ],
            'failed_videos': [
                {
                    'turn': r['turn'],
                    'character': r['character'],
                    'error': r.get('error', '未知错误'),
                    'iterations': r['iterations']
                }
                for r in failed_results
            ],
            'detailed_results': results
        }
        
        return report
    
    def generate_single_video(
        self,
        script_name: str,
        turn_number: int
    ) -> Dict:
        """
        生成单个视频（用于测试或重新生成）
        
        Args:
            script_name: 剧本名称
            turn_number: turn编号
            
        Returns:
            生成结果
        """
        # 使用简化提取器提取prompts
        try:
            video_prompts = extract_prompts_simple(script_name)
        except Exception as e:
            return {
                'success': False,
                'error': f'提取prompts失败: {e}'
            }
        
        # 查找指定turn的prompt
        prompt_data = None
        for p in video_prompts:
            if p['turn'] == turn_number:
                prompt_data = p
                break
        
        if not prompt_data:
            return {
                'success': False,
                'error': f'未找到turn {turn_number}的数据'
            }
        
        # 生成视频
        result = self._generate_video_with_director_guidance(
            prompt_data,
            script_name,
            turn_number
        )
        
        return result
