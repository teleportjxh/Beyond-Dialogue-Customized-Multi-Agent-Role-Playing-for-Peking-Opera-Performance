"""
定妆师Agent - 负责确认演员装扮
根据角色信息和RAG检索结果，确定角色的行当、脸谱、妆容、服饰
"""

from typing import Dict, Any, List
from .agent_base import AgentBase


class CostumeDesignerAgent(AgentBase):
    """定妆师Agent，负责角色装扮设计"""
    
    def __init__(self, context: str):
        """
        初始化定妆师Agent
        
        Args:
            context: 包含角色信息和RAG检索结果的上下文
        """
        system_prompt = self._build_system_prompt()
        super().__init__(
            name="定妆师",
            role="costume_designer",
            system_prompt=system_prompt,
            temperature=0.7
        )
        self.context = context
    
    def _build_system_prompt(self) -> str:
        """构建定妆师的系统提示"""
        return """你是一位资深的京剧定妆师，精通京剧的行当、脸谱、妆容和服饰。

你的职责：
1. 根据角色的基本信息（性别、年龄、性格、职业）确定合适的行当
2. 根据角色特征设计脸谱图案和色彩
3. 设计符合角色身份的妆容细节
4. 选择适合角色的服饰款式和配饰

京剧行当分类：
- 生：老生、小生、武生、娃娃生
- 旦：青衣、花旦、武旦、老旦、刀马旦
- 净：铜锤花脸、架子花脸、武花脸
- 丑：文丑、武丑

脸谱要点：
- 红色：忠勇正直（如关羽）
- 黑色：刚正威武（如张飞）
- 白色：奸诈狡猾（如曹操）
- 金色：神仙妖怪（如孙悟空）
- 蓝色：刚强勇猛

输出要求：
请以JSON格式输出每个角色的装扮设计，包含：
- character: 角色名称
- role_type: 行当
- face_pattern: 脸谱描述
- makeup: 妆容描述
- costume: 服饰描述
- accessories: 配饰描述
- overall_style: 整体风格描述

示例输出：
{
  "character": "孙悟空",
  "role_type": "武生",
  "face_pattern": "金色猴脸，额头红色火焰纹，眼周黑色勾勒，突出机灵神态",
  "makeup": "金色底妆，红色眼影，黑色眉毛上挑，展现神猴威武",
  "costume": "黄色虎皮裙，红色战袍，金色护甲，显示齐天大圣身份",
  "accessories": "金箍棒、紫金冠、如意金箍棒、云履",
  "overall_style": "威武神勇，灵动飘逸，展现齐天大圣的神通广大"
}

请确保设计符合京剧传统规范，同时体现角色的独特性格和身份。"""
    
    def design_costume(
        self,
        character_name: str,
        character_info: Dict[str, Any],
        outline: Dict[str, Any],
        rag_references: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        为角色设计装扮
        
        Args:
            character_name: 角色名称
            character_info: 角色基本信息（从profile.json）
            outline: 剧本大纲
            rag_references: RAG检索的参考场景
            
        Returns:
            装扮设计结果
        """
        # 构建提示
        prompt_parts = [
            f"# 角色装扮设计任务",
            f"\n## 角色名称：{character_name}",
            f"\n## 剧本信息",
            f"剧名：{outline.get('title', '未命名')}",
            f"主题：{outline.get('theme', '未知')}",
            f"场景设定：{outline.get('setting', '未知')}",
        ]
        
        # 添加角色信息
        if character_info:
            prompt_parts.append(f"\n## 角色基本信息")
            prompt_parts.append(f"性别：{character_info.get('gender', '未知')}")
            
            if character_info.get('script_data'):
                first_script = character_info['script_data'][0]
                prompt_parts.append(f"年龄：{first_script.get('age', '未知')}")
                prompt_parts.append(f"性格：{first_script.get('personality', '未知')}")
                prompt_parts.append(f"职业：{first_script.get('profession', '未知')}")
                prompt_parts.append(f"描述：{first_script.get('description', '未知')}")
                
                # 如果有历史装扮信息，作为参考
                if first_script.get('face'):
                    prompt_parts.append(f"\n## 历史装扮参考")
                    prompt_parts.append(f"脸谱：{first_script.get('face', '')}")
                    prompt_parts.append(f"妆容：{first_script.get('makeup', '')}")
                    prompt_parts.append(f"服装：{first_script.get('cloth', '')}")
        
        # 添加RAG检索的参考
        if rag_references:
            prompt_parts.append(f"\n## 历史演出参考")
            for i, ref in enumerate(rag_references[:3], 1):
                prompt_parts.append(f"\n### 参考{i}：{ref.get('title', '未知剧本')}")
                text = ref.get('text', '')[:300]
                prompt_parts.append(text)
        
        prompt_parts.append(f"\n## 任务要求")
        prompt_parts.append(f"请根据以上信息，为{character_name}设计本次演出的装扮。")
        prompt_parts.append(f"要求：符合京剧传统、体现角色特征、适合剧本主题。")
        prompt_parts.append(f"\n请直接输出JSON格式的装扮设计，不要有其他说明文字。")
        
        prompt = "\n".join(prompt_parts)
        
        # 调用LLM生成装扮设计
        response = self.generate_response(prompt)
        
        # 解析JSON响应
        import json
        import re
        
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                costume_design = json.loads(json_match.group())
            else:
                # 如果没有找到JSON，构建默认结构
                costume_design = {
                    "character": character_name,
                    "role_type": "未确定",
                    "face_pattern": response[:100],
                    "makeup": "传统京剧妆容",
                    "costume": "传统京剧服饰",
                    "accessories": "传统配饰",
                    "overall_style": response[:200]
                }
        except json.JSONDecodeError:
            # JSON解析失败，返回默认结构
            costume_design = {
                "character": character_name,
                "role_type": "未确定",
                "face_pattern": "传统脸谱",
                "makeup": "传统妆容",
                "costume": "传统服饰",
                "accessories": "传统配饰",
                "overall_style": response[:200] if response else "传统京剧风格"
            }
        
        return costume_design
    
    def design_all_costumes(
        self,
        characters_info: Dict[str, Dict[str, Any]],
        outline: Dict[str, Any],
        rag_references: Dict[str, List[Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        为所有角色设计装扮
        
        Args:
            characters_info: 所有角色的信息字典
            outline: 剧本大纲
            rag_references: 每个角色的RAG参考（可选）
            
        Returns:
            所有角色的装扮设计
        """
        all_costumes = {}
        
        for character_name, character_info in characters_info.items():
            print(f"  正在为 {character_name} 设计装扮...")
            
            char_rag_refs = None
            if rag_references and character_name in rag_references:
                char_rag_refs = rag_references[character_name]
            
            costume = self.design_costume(
                character_name=character_name,
                character_info=character_info,
                outline=outline,
                rag_references=char_rag_refs
            )
            
            all_costumes[character_name] = costume
            print(f"    ✓ {character_name} 装扮设计完成")
        
        return all_costumes
