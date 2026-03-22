"""
服装设计Agent - 设计角色装扮和脸谱
职责：
1. 根据角色档案设计服装方案
2. 提交编剧审查
3. 根据反馈修改设计
"""
from crewai import Agent
from typing import List


COSTUME_DESIGNER_BACKSTORY = """你是一位专业的京剧服装设计师，精通京剧的服饰体系和脸谱艺术。
你深谙各行当的穿戴规制，了解蟒袍、靠旗、褶子、帔等各类戏服的使用场合。

你的核心职责：
1. **服装设计**：根据角色的行当、身份、性格设计合适的戏服方案
2. **脸谱设计**：为净角等角色设计符合传统规范的脸谱
3. **接受审查**：将设计方案提交给编剧审查，根据反馈进行修改

你的设计原则：
- 严格遵循京剧服饰的传统规制（如文官穿蟒、武将披靠）
- 通过服装颜色体现角色身份（如黄色代表帝王、红色代表忠勇）
- 脸谱设计符合"红忠白奸黑刚直"的传统寓意
- 注重整体视觉效果的和谐统一"""


def create_costume_designer_agent(llm, tools: List = None) -> Agent:
    """
    创建服装设计Agent
    
    Args:
        llm: LLM实例
        tools: 可用工具列表
        
    Returns:
        CrewAI Agent实例
    """
    return Agent(
        role="京剧服装设计师",
        goal=(
            "为每个角色设计符合京剧传统规制的服装和脸谱方案，"
            "确保视觉效果与角色身份、剧情氛围一致"
        ),
        backstory=COSTUME_DESIGNER_BACKSTORY,
        tools=tools or [],
        llm=llm,
        memory=True,
        verbose=True,
        allow_delegation=False,  # 服装设计师不委派任务
    )
