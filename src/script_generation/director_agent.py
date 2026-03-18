"""
导演Agent - 负责剧本质量评估和优化建议
评估生成的剧本是否符合京剧艺术标准，提供改进建议
"""

from typing import Dict, Any, List, Tuple
from .agent_base import AgentBase


class DirectorAgent(AgentBase):
    """导演Agent，负责剧本质量评估"""
    
    def __init__(self, context: str):
        """
        初始化导演Agent
        
        Args:
            context: 包含剧本信息和评估标准的上下文
        """
        system_prompt = self._build_system_prompt()
        super().__init__(
            name="导演",
            role="director",
            system_prompt=system_prompt,
            temperature=0.3
        )
        self.context = context
    
    def _build_system_prompt(self) -> str:
        """构建导演的系统提示"""
        return """你是一位资深的京剧导演，精通京剧艺术的各个方面。

你的职责：
1. 评估剧本的整体质量和艺术水平
2. 检查是否符合京剧的"唱念做打"四功要求
3. 评估角色塑造是否生动、性格是否鲜明
4. 检查对话是否符合京剧的文言文风格
5. 评估场景设置和情节发展是否合理
6. 提供具体的改进建议

评估标准：
1. 京剧特色（30分）
   - 唱念做打的运用
   - 文言文表达
   - 程式化动作描述
   - 情感标注【情】

2. 角色塑造（25分）
   - 性格鲜明度
   - 语言风格一致性
   - 行为符合身份
   - 情感表达真实

3. 剧情结构（25分）
   - 情节连贯性
   - 冲突设置合理
   - 高潮设计精彩
   - 结局处理得当

4. 艺术表现（20分）
   - 语言优美度
   - 意境营造
   - 文化内涵
   - 创新性

输出要求：
请以JSON格式输出评估结果，包含：
- overall_score: 总分（0-100）
- scores: 各项得分
  - peking_opera_style: 京剧特色得分
  - character_portrayal: 角色塑造得分
  - plot_structure: 剧情结构得分
  - artistic_expression: 艺术表现得分
- strengths: 优点列表
- weaknesses: 不足列表
- suggestions: 改进建议列表
- need_revision: 是否需要修改（true/false）
- revision_priority: 修改优先级（high/medium/low）

示例输出：
{
  "overall_score": 75,
  "scores": {
    "peking_opera_style": 22,
    "character_portrayal": 20,
    "plot_structure": 18,
    "artistic_expression": 15
  },
  "strengths": [
    "角色性格鲜明，诸葛亮的智慧和孙悟空的豪爽对比强烈",
    "对话运用了文言文，符合京剧风格"
  ],
  "weaknesses": [
    "唱段较少，未充分展现京剧的唱功",
    "部分对话过于现代化，缺乏古典韵味"
  ],
  "suggestions": [
    "在关键情节处增加唱段，如论英雄时可用【西皮】或【二黄】",
    "将现代词汇改为文言表达，如'很厉害'改为'甚是了得'",
    "增加程式化动作描述，如'拱手作揖'、'捋须沉思'等"
  ],
  "need_revision": true,
  "revision_priority": "medium"
}

请客观公正地评估，既要指出优点，也要指出不足，并提供可操作的改进建议。"""
    
    def evaluate_script(
        self,
        outline: Dict[str, Any],
        dialogue_history: List[Dict[str, Any]],
        costumes: Dict[str, Dict[str, Any]],
        rag_references: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        评估完整剧本
        
        Args:
            outline: 剧本大纲
            dialogue_history: 对话历史
            costumes: 角色装扮设计
            rag_references: RAG检索的优秀场景参考
            
        Returns:
            评估结果
        """
        # 构建评估提示
        prompt_parts = [
            f"# 剧本质量评估任务",
            f"\n## 剧本基本信息",
            f"剧名：{outline.get('title', '未命名')}",
            f"主题：{outline.get('theme', '未知')}",
            f"场景数：{len(outline.get('scenes', []))}",
            f"对话轮数：{len(dialogue_history)}",
        ]
        
        # 添加角色装扮信息
        if costumes:
            prompt_parts.append(f"\n## 角色装扮")
            for char_name, costume in costumes.items():
                prompt_parts.append(f"\n### {char_name}")
                prompt_parts.append(f"行当：{costume.get('role_type', '未知')}")
                prompt_parts.append(f"风格：{costume.get('overall_style', '未知')}")
        
        # 添加剧本大纲
        if outline.get('scenes'):
            prompt_parts.append(f"\n## 剧本大纲")
            for i, scene in enumerate(outline['scenes'], 1):
                prompt_parts.append(f"\n第{i}场：{scene.get('title', '未命名')}")
                prompt_parts.append(f"描述：{scene.get('description', '无')}")
        
        # 添加对话内容（精选部分）
        if dialogue_history:
            prompt_parts.append(f"\n## 剧本对话（精选）")
            # 选择前5轮和后5轮对话
            selected_dialogues = dialogue_history[:5] + dialogue_history[-5:]
            for dialogue in selected_dialogues:
                speaker = dialogue.get('speaker', '未知')
                content = dialogue.get('content', '')
                emotion = dialogue.get('emotion', '')
                prompt_parts.append(f"\n{speaker}【{emotion}】：")
                prompt_parts.append(content[:200])  # 限制长度
        
        # 添加优秀场景参考
        if rag_references:
            prompt_parts.append(f"\n## 优秀场景参考（评估标准）")
            for i, ref in enumerate(rag_references[:2], 1):
                prompt_parts.append(f"\n### 参考{i}：{ref.get('title', '未知')}")
                prompt_parts.append(f"相似度：{ref.get('similarity_score', 0):.2f}")
                text = ref.get('text', '')[:400]
                prompt_parts.append(text)
        
        prompt_parts.append(f"\n## 评估要求")
        prompt_parts.append(f"请根据以上信息，全面评估这个剧本的质量。")
        prompt_parts.append(f"参考优秀场景的标准，指出本剧本的优点和不足。")
        prompt_parts.append(f"提供具体可操作的改进建议。")
        prompt_parts.append(f"\n请直接输出JSON格式的评估结果，不要有其他说明文字。")
        
        prompt = "\n".join(prompt_parts)
        
        # 调用LLM进行评估
        response = self.generate_response(prompt)
        
        # 解析JSON响应
        import json
        import re
        
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                # 构建默认评估结果
                evaluation = self._create_default_evaluation(response)
        except json.JSONDecodeError:
            evaluation = self._create_default_evaluation(response)
        
        return evaluation
    
    def _create_default_evaluation(self, response: str) -> Dict[str, Any]:
        """创建默认评估结果"""
        return {
            "overall_score": 70,
            "scores": {
                "peking_opera_style": 20,
                "character_portrayal": 18,
                "plot_structure": 17,
                "artistic_expression": 15
            },
            "strengths": ["剧本已生成"],
            "weaknesses": ["评估解析失败"],
            "suggestions": [response[:200] if response else "建议人工审核"],
            "need_revision": False,
            "revision_priority": "low"
        }
    
    def evaluate_scene(
        self,
        scene_outline: Dict[str, Any],
        scene_dialogues: List[Dict[str, Any]],
        rag_references: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        评估单个场景
        
        Args:
            scene_outline: 场景大纲
            scene_dialogues: 场景对话
            rag_references: RAG参考
            
        Returns:
            场景评估结果
        """
        prompt_parts = [
            f"# 场景评估",
            f"\n## 场景信息",
            f"场景名：{scene_outline.get('title', '未命名')}",
            f"描述：{scene_outline.get('description', '无')}",
            f"对话数：{len(scene_dialogues)}",
        ]
        
        # 添加对话内容
        if scene_dialogues:
            prompt_parts.append(f"\n## 场景对话")
            for dialogue in scene_dialogues:
                speaker = dialogue.get('speaker', '未知')
                content = dialogue.get('content', '')
                emotion = dialogue.get('emotion', '')
                prompt_parts.append(f"\n{speaker}【{emotion}】：{content[:150]}")
        
        # 添加参考
        if rag_references:
            prompt_parts.append(f"\n## 参考场景")
            for ref in rag_references[:1]:
                prompt_parts.append(ref.get('text', '')[:300])
        
        prompt_parts.append(f"\n请评估这个场景的质量，输出JSON格式结果。")
        
        prompt = "\n".join(prompt_parts)
        response = self.generate_response(prompt)
        
        # 简化的场景评估
        import json
        import re
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "scene_score": 70,
            "strengths": ["场景完整"],
            "suggestions": ["可进一步优化"]
        }
    
    def provide_revision_guidance(
        self,
        evaluation: Dict[str, Any],
        focus_areas: List[str] = None
    ) -> str:
        """
        根据评估结果提供修改指导
        
        Args:
            evaluation: 评估结果
            focus_areas: 重点关注的方面
            
        Returns:
            修改指导文本
        """
        guidance_parts = [
            "# 剧本修改指导",
            f"\n## 总体评分：{evaluation.get('overall_score', 0)}/100",
        ]
        
        # 添加优点
        strengths = evaluation.get('strengths', [])
        if strengths:
            guidance_parts.append("\n## 优点")
            for strength in strengths:
                guidance_parts.append(f"✓ {strength}")
        
        # 添加不足
        weaknesses = evaluation.get('weaknesses', [])
        if weaknesses:
            guidance_parts.append("\n## 需要改进")
            for weakness in weaknesses:
                guidance_parts.append(f"✗ {weakness}")
        
        # 添加建议
        suggestions = evaluation.get('suggestions', [])
        if suggestions:
            guidance_parts.append("\n## 具体建议")
            for i, suggestion in enumerate(suggestions, 1):
                guidance_parts.append(f"{i}. {suggestion}")
        
        # 添加优先级
        priority = evaluation.get('revision_priority', 'low')
        priority_text = {
            'high': '高优先级 - 建议立即修改',
            'medium': '中优先级 - 建议适当优化',
            'low': '低优先级 - 可选择性改进'
        }
        guidance_parts.append(f"\n## 修改优先级")
        guidance_parts.append(priority_text.get(priority, '待定'))
        
        return "\n".join(guidance_parts)
