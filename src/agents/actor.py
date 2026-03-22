"""
演员Agent - 扮演特定角色，生成对话
职责：
1. 扮演特定的京剧角色
2. 接受其他角色的对话并回应
3. 自我审查生成的内容
4. 接受导演的审查和指导
"""
from crewai import Agent
from typing import List, Optional


ACTOR_BACKSTORY_TEMPLATE = """你是一位专业的京剧演员，现在正在扮演角色：{character_name}。

## 角色信息
{character_profile}

## 角色数据
{character_data}

## 历史参考
{character_knowledge}

## 你的表演原则：
1. **角色一致性**：始终保持角色的性格特征、说话方式和行为逻辑
2. **京剧程式**：对话中融入京剧的唱念做打元素
3. **情感真实**：根据剧情发展展现真实的情感变化
4. **自我审查**：生成对话后，检查是否符合角色设定，是否有违反禁忌的内容

## 对话格式要求：
你的回复必须严格按照以下京剧剧本格式：
- 【念】（韵白）用于念白台词
- 【唱】用于唱段，需标注板式如[西皮原板]
- 【做】用于动作描写
- 【情】用于内心情感

## 自我审查清单：
生成对话后，你需要检查：
1. 是否符合角色的性格特征？
2. 是否使用了角色的口头禅或说话风格？
3. 是否有违反角色禁忌的内容？
4. 是否符合京剧的表演程式？
5. 情感表达是否与剧情发展一致？"""


def create_actor_agent(
    llm,
    character_name: str,
    character_profile: str = "",
    character_data: str = "",
    character_knowledge: str = "",
    tools: List = None
) -> Agent:
    """
    创建演员Agent
    
    Args:
        llm: LLM实例
        character_name: 角色名称
        character_profile: 角色档案信息
        character_data: 角色数据（口头禅、禁忌等）
        character_knowledge: 角色的历史知识（来自RAG长期记忆）
        tools: 可用工具列表
        
    Returns:
        CrewAI Agent实例
    """
    backstory = ACTOR_BACKSTORY_TEMPLATE.format(
        character_name=character_name,
        character_profile=character_profile or "（暂无详细档案）",
        character_data=character_data or "（暂无详细数据）",
        character_knowledge=character_knowledge or "（暂无历史参考）"
    )
    
    return Agent(
        role=f"京剧演员（饰演{character_name}）",
        goal=(
            f"以{character_name}的身份进行表演，生成符合角色性格和京剧程式的对话，"
            f"并在生成后进行自我审查确保质量"
        ),
        backstory=backstory,
        tools=tools or [],
        llm=llm,
        memory=True,
        verbose=True,
        allow_delegation=False,
    )
