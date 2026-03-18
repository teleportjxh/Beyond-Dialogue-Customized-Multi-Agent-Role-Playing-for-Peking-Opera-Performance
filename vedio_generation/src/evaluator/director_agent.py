"""
导演Agent - 视频质量监督者和指导者
负责评估视频质量并提供改进指导
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from pathlib import Path
import requests
import tempfile

logger = logging.getLogger(__name__)


class DirectorAgent:
    """
    导演Agent - 质量监督者和指导者
    
    核心职责：
    1. 评估生成的视频质量（多维度打分）
    2. 分析问题并给出具体改进建议
    3. 指导prompt优化，直到视频达到要求
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, pass_threshold: float = 7.0):
        """
        初始化导演Agent
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            pass_threshold: 通过阈值（默认7.0分）
        """
        # 尝试从config导入
        try:
            from config.api_config import API_KEY, API_BASE_URL, MODELS
            self.api_key = api_key or API_KEY
            self.base_url = base_url or API_BASE_URL
            self.model_name = MODELS.get('evaluation', 'gemini-2.5-pro')
        except ImportError:
            self.api_key = api_key
            self.base_url = base_url or "https://api.openai.com/v1"
            self.model_name = 'gemini-2.5-pro'
        
        if not self.api_key:
            raise ValueError("未提供API密钥")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.pass_threshold = pass_threshold
        
        logger.info(f"DirectorAgent初始化成功，使用模型: {self.model_name}")
        
        # 评估维度
        self.evaluation_dimensions = {
            'costume_accuracy': '装扮准确性',
            'action_quality': '动作质量',
            'dialogue_delivery': '对话表达',
            'scene_consistency': '场景一致性',
            'overall_impression': '整体印象'
        }
    
    def evaluate_video(
        self,
        video_url: str,
        original_prompt: str,
        expected_content: Dict,
        video_path: str = None
    ) -> Dict:
        """
        评估视频质量
        
        Args:
            video_url: 视频URL（直接传递给模型）
            original_prompt: 原始prompt
            expected_content: 期望的内容（包含角色、装扮、动作等信息）
            video_path: 视频文件路径（未使用，保留接口兼容性）
            
        Returns:
            评估结果字典：
            {
                'passed': bool,
                'overall_score': float,
                'dimension_scores': dict,
                'analysis': str,
                'improvement_suggestions': list,
                'detailed_feedback': dict
            }
        """
        try:
            # 构建评估prompt
            eval_prompt = self._build_evaluation_prompt(
                original_prompt,
                expected_content
            )
            
            logger.info(f"使用视频URL进行评估: {video_url}")
            
            # 使用OpenAI兼容的API和视频URL进行评估
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": eval_prompt},
                            {
                                "type": "vedio_url", # 注意：即使是视频，类型也可能是image_url
                                "vedio_url": {"url": video_url},
                            },
                        ],
                    }
                ],
                max_tokens=1500,
            )
            
            logger.info("✓ 视频评估完成")
            
            # 解析评估结果
            evaluation = self._parse_evaluation_response(response.choices[0].message.content)
            
            # 判断是否通过
            overall_score = evaluation.get('overall_score', 0)
            evaluation['passed'] = overall_score >= self.pass_threshold
            
            logger.info(
                f"评估完成 - 总分: {overall_score:.2f}, "
                f"通过: {evaluation['passed']}"
            )
            
            return evaluation
            
        except Exception as e:
            logger.error(f"视频评估失败: {e}")
            return {
                'passed': False,
                'overall_score': 0,
                'error': str(e)
            }
    
    
    def _build_evaluation_prompt(
        self,
        original_prompt: str,
        expected_content: Dict
    ) -> str:
        """构建评估prompt"""
        
        character = expected_content.get('character', '')
        emotion = expected_content.get('emotion', '')
        content_type = expected_content.get('content_type', '')
        content_text = expected_content.get('content_text', '')
        
        prompt = f"""你是一位专业的视频导演，负责评估生成的视频质量。

原始生成Prompt:
{original_prompt}

期望内容:
- 角色: {character}
- 情感: {emotion}
- 内容类型: {content_type}
- 具体内容: {content_text}

请从以下维度评估这个视频（每个维度0-10分）：

1. **装扮准确性** (costume_accuracy)
   - 角色的装扮是否符合要求？
   - 脸谱、服装、配饰是否准确？

2. **动作质量** (action_quality)
   - 动作是否流畅自然？
   - 是否符合角色特点？
   - 是否表达了要求的内容？

3. **对话表达** (dialogue_delivery)
   - 如果有对话/唱段，表达是否清晰？
   - 情感是否到位？

4. **场景一致性** (scene_consistency)
   - 场景设置是否合理？
   - 是否有不相关的元素出现？

5. **整体印象** (overall_impression)
   - 视频整体质量如何？
   - 是否达到专业水准？

请以JSON格式返回评估结果：
{{
    "dimension_scores": {{
        "costume_accuracy": 分数,
        "action_quality": 分数,
        "dialogue_delivery": 分数,
        "scene_consistency": 分数,
        "overall_impression": 分数
    }},
    "overall_score": 总分（5个维度的平均分）,
    "analysis": "详细分析文字",
    "problems": [
        "问题1描述",
        "问题2描述"
    ],
    "improvement_suggestions": [
        {{
            "dimension": "维度名称",
            "problem": "具体问题",
            "suggestion": "改进建议"
        }}
    ]
}}

注意：
- 评分要客观严格，7分以上才算通过
- 问题描述要具体，不要泛泛而谈
- 改进建议要可操作，能直接用于优化prompt
"""
        
        return prompt
    
    def _parse_evaluation_response(self, response_text: str) -> Dict:
        """解析评估响应"""
        try:
            # 提取JSON部分
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("响应中未找到JSON格式")
            
            json_str = response_text[start_idx:end_idx]
            evaluation = json.loads(json_str)
            
            # 确保包含所有必需字段
            if 'dimension_scores' not in evaluation:
                evaluation['dimension_scores'] = {}
            
            if 'overall_score' not in evaluation:
                scores = evaluation['dimension_scores'].values()
                evaluation['overall_score'] = sum(scores) / len(scores) if scores else 0
            
            if 'improvement_suggestions' not in evaluation:
                evaluation['improvement_suggestions'] = []
            
            return evaluation
            
        except Exception as e:
            logger.error(f"解析评估响应失败: {e}")
            return {
                'dimension_scores': {},
                'overall_score': 0,
                'analysis': response_text,
                'improvement_suggestions': []
            }
    
    def generate_improved_prompt(
        self,
        original_prompt: str,
        evaluation: Dict,
        expected_content: Dict,
        scene_desc: str = "",
        costume_desc: str = ""
    ) -> str:
        """
        根据评估结果生成改进的prompt
        
        关键改进：保留场景和装扮信息，仅应用改进建议到表演部分
        
        Args:
            original_prompt: 原始prompt
            evaluation: 评估结果
            expected_content: 期望内容
            scene_desc: 场景描述（保持不变）
            costume_desc: 装扮描述（保持不变）
            
        Returns:
            改进后的prompt
        """
        try:
            from ..extractor.simple_prompt_extractor import _build_complete_prompt
            
            # 提取改进建议
            improvements = evaluation.get('improvement_suggestions', [])
            
            # 基于原始结构化数据重建prompt，应用改进建议
            improved_prompt = _build_complete_prompt(
                character=expected_content.get('character', ''),
                emotion=expected_content.get('emotion', ''),
                content_text=expected_content.get('content_text', ''),
                scene_desc=scene_desc,      # 保留原始场景
                costume_desc=costume_desc,  # 保留原始装扮
                improvements=improvements    # 应用改进建议
            )
            
            logger.info("生成改进prompt成功（保留场景和装扮信息）")
            return improved_prompt
            
        except Exception as e:
            logger.error(f"生成改进prompt失败: {e}")
            return original_prompt
    
    def _build_improvement_prompt(
        self,
        original_prompt: str,
        evaluation: Dict,
        expected_content: Dict
    ) -> str:
        """构建prompt改进指令"""
        
        problems = evaluation.get('problems', [])
        suggestions = evaluation.get('improvement_suggestions', [])
        dimension_scores = evaluation.get('dimension_scores', {})
        
        # 找出得分最低的维度
        low_score_dimensions = [
            (dim, score) for dim, score in dimension_scores.items()
            if score < self.pass_threshold
        ]
        low_score_dimensions.sort(key=lambda x: x[1])
        
        prompt = f"""你是一位专业的视频prompt优化专家。

原始Prompt:
{original_prompt}

期望内容:
- 角色: {expected_content.get('character', '')}
- 情感: {expected_content.get('emotion', '')}
- 内容类型: {expected_content.get('content_type', '')}
- 具体内容: {expected_content.get('content_text', '')}

评估结果:
总分: {evaluation.get('overall_score', 0):.2f}/10

得分较低的维度:
"""
        
        for dim, score in low_score_dimensions[:3]:  # 最多显示3个
            dim_name = self.evaluation_dimensions.get(dim, dim)
            prompt += f"- {dim_name}: {score:.2f}/10\n"
        
        if problems:
            prompt += f"\n发现的问题:\n"
            for i, problem in enumerate(problems, 1):
                prompt += f"{i}. {problem}\n"
        
        if suggestions:
            prompt += f"\n改进建议:\n"
            for i, sug in enumerate(suggestions, 1):
                prompt += f"{i}. [{sug.get('dimension', '')}] {sug.get('suggestion', '')}\n"
        
        prompt += f"""

请根据以上评估结果和改进建议，优化原始prompt。

优化要求:
1. 保持视频时长10-15秒
2. 聚焦于单个角色的单次表演
3. 针对性地改进得分低的维度
4. 使描述更加具体和明确
5. 确保符合期望内容的要求

请直接输出优化后的prompt，不要有其他解释文字。
"""
        
        return prompt
    
    def analyze_and_improve(
        self,
        video_url: str,
        original_prompt: str,
        expected_content: Dict,
        video_path: str = None,
        scene_desc: str = "",
        costume_desc: str = ""
    ) -> Tuple[bool, Dict, Optional[str]]:
        """
        分析视频并生成改进建议
        
        Args:
            video_url: 视频URL
            original_prompt: 原始prompt
            expected_content: 期望内容
            video_path: 视频本地路径（可选，作为降级方案）
            scene_desc: 场景描述（用于重建prompt）
            costume_desc: 装扮描述（用于重建prompt）
            
        Returns:
            (是否通过, 评估结果, 改进后的prompt)
        """
        # 评估视频
        evaluation = self.evaluate_video(
            video_url,
            original_prompt,
            expected_content,
            video_path
        )
        
        passed = evaluation.get('passed', False)
        
        if passed:
            logger.info("视频通过评估，无需改进")
            return True, evaluation, None
        
        # 生成改进的prompt（保留场景和装扮）
        improved_prompt = self.generate_improved_prompt(
            original_prompt,
            evaluation,
            expected_content,
            scene_desc,
            costume_desc
        )
        
        return False, evaluation, improved_prompt
    
    def get_evaluation_summary(self, evaluation: Dict) -> str:
        """获取评估摘要文本"""
        summary_parts = []
        
        overall_score = evaluation.get('overall_score', 0)
        passed = evaluation.get('passed', False)
        
        summary_parts.append(f"总分: {overall_score:.2f}/10")
        summary_parts.append(f"状态: {'✓ 通过' if passed else '✗ 未通过'}")
        
        dimension_scores = evaluation.get('dimension_scores', {})
        if dimension_scores:
            summary_parts.append("\n各维度得分:")
            for dim, score in dimension_scores.items():
                dim_name = self.evaluation_dimensions.get(dim, dim)
                summary_parts.append(f"  - {dim_name}: {score:.2f}/10")
        
        analysis = evaluation.get('analysis', '')
        if analysis:
            summary_parts.append(f"\n分析:\n{analysis}")
        
        return "\n".join(summary_parts)
