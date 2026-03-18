"""
编剧Agent - 生成剧本大纲和场景设计
"""
import json
from typing import Dict, Any, List
from .agent_base import AgentBase


class ScreenwriterAgent(AgentBase):
    """编剧Agent，负责剧本大纲和场景设计"""
    
    def __init__(self, temperature: float = 0.8):
        """
        初始化编剧Agent
        
        Args:
            temperature: 温度参数，较高以增加创意
        """
        system_prompt = self._build_system_prompt()
        
        super().__init__(
            name="编剧",
            role="screenwriter",
            system_prompt=system_prompt,
            temperature=temperature
        )
    
    def _build_system_prompt(self) -> str:
        """构建编剧Agent的系统提示"""
        prompt = """你是一位资深的京剧编剧，擅长创作富有戏剧张力和艺术价值的京剧剧本。

## 你的任务
根据用户需求和角色信息，创作京剧剧本大纲，包括：
1. 剧本标题和主题
2. 场景设定和氛围
3. 剧情发展脉络
4. 角色关系和冲突点
5. 高潮和结局设计

## 京剧创作原则
1. **戏剧冲突**：设计鲜明的矛盾冲突，推动剧情发展
2. **人物塑造**：充分展现角色性格，符合人物设定
3. **艺术特色**：体现京剧的唱念做打，注重程式美
4. **文化内涵**：融入传统文化元素，富有教育意义
5. **节奏把控**：起承转合，张弛有度

## 输出格式
请以JSON格式输出剧本大纲：

```json
{
    "title": "剧本标题",
    "theme": "主题思想",
    "setting": "场景设定（时间、地点、氛围）",
    "characters": ["角色1", "角色2"],
    "character_relations": "角色关系描述",
    "conflict": "主要矛盾冲突",
    "scenes": [
        {
            "name": "场景名称",
            "description": "场景描述",
            "key_points": ["要点1", "要点2"],
            "expected_length": "预计对话轮数"
        }
    ],
    "climax": "高潮设计",
    "ending": "结局设计",
    "artistic_features": ["艺术特色1", "艺术特色2"]
}
```

## 注意事项
- 充分利用提供的角色信息和历史场景参考
- 确保剧情符合角色性格和行为禁忌
- 设计适合京剧表演的场景和动作
- 预留足够的表演空间，让演员发挥
"""
        return prompt
    
    def generate_outline(
        self,
        user_request: str,
        context: str
    ) -> Dict[str, Any]:
        """
        生成剧本大纲
        
        Args:
            user_request: 用户需求
            context: 上下文信息（角色信息、RAG检索结果等）
            
        Returns:
            剧本大纲字典
        """
        # 构建输入
        user_input = f"""请根据以下信息创作京剧剧本大纲：

## 用户需求
{user_request}

## 背景信息
{context}

请创作一个富有戏剧性和艺术价值的京剧剧本大纲。
"""
        
        # 生成响应
        response = self.generate_response(user_input)
        
        # 解析JSON
        outline = self._parse_outline(response)
        
        return outline
    
    def _parse_outline(self, response: str) -> Dict[str, Any]:
        """
        解析大纲响应
        
        Args:
            response: Agent响应
            
        Returns:
            解析后的大纲字典
        """
        try:
            # 尝试提取JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                outline = json.loads(json_str)
                return outline
            else:
                # 如果没有找到JSON，返回基础结构
                return self._create_default_outline(response)
        
        except json.JSONDecodeError:
            # JSON解析失败，返回基础结构
            return self._create_default_outline(response)
    
    def _create_default_outline(self, response: str) -> Dict[str, Any]:
        """
        创建默认大纲结构
        
        Args:
            response: 原始响应
            
        Returns:
            默认大纲字典
        """
        return {
            "title": "未命名剧本",
            "theme": "待定",
            "setting": "待定",
            "characters": [],
            "character_relations": "待定",
            "conflict": "待定",
            "scenes": [
                {
                    "name": "第一场",
                    "description": response[:200] if len(response) > 200 else response,
                    "key_points": ["待定"],
                    "expected_length": "10-15轮"
                }
            ],
            "climax": "待定",
            "ending": "待定",
            "artistic_features": ["待定"],
            "raw_response": response
        }
    
    def refine_outline(
        self,
        outline: Dict[str, Any],
        feedback: str
    ) -> Dict[str, Any]:
        """
        根据反馈优化大纲
        
        Args:
            outline: 原始大纲
            feedback: 反馈意见
            
        Returns:
            优化后的大纲
        """
        user_input = f"""请根据以下反馈优化剧本大纲：

## 原始大纲
{json.dumps(outline, ensure_ascii=False, indent=2)}

## 反馈意见
{feedback}

请输出优化后的完整大纲（JSON格式）。
"""
        
        response = self.generate_response(user_input)
        refined_outline = self._parse_outline(response)
        
        return refined_outline
    
    def generate_scene_detail(
        self,
        scene: Dict[str, Any],
        outline: Dict[str, Any]
    ) -> str:
        """
        为特定场景生成详细描述
        
        Args:
            scene: 场景信息
            outline: 完整大纲
            
        Returns:
            场景详细描述
        """
        user_input = f"""请为以下场景生成详细的导演指导：

## 剧本信息
标题：{outline.get('title', '未命名')}
主题：{outline.get('theme', '未知')}

## 场景信息
{json.dumps(scene, ensure_ascii=False, indent=2)}

## 角色信息
{', '.join(outline.get('characters', []))}

请描述：
1. 场景的舞台布置和氛围
2. 角色的出场方式和位置
3. 关键动作和表演要点
4. 对话的节奏和情感基调
5. 需要注意的京剧程式
"""
        
        response = self.generate_response(user_input)
        return response
