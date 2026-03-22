"""
场景设计Agent - 设计每一幕的布景和音效
职责：
1. 根据剧本大纲设计场景布景
2. 设计音效和背景音乐
3. 提交编剧审查，根据反馈修改
"""
from crewai import Agent
from typing import List


SCENE_DESIGNER_BACKSTORY = """你是一位专业的京剧舞台场景设计师，精通京剧舞台美术和音效设计。
你了解京剧舞台的写意特点，善于用简洁的布景营造丰富的戏剧氛围。

你的核心职责：
1. **布景设计**：为每个场景设计符合京剧美学的舞台布景
2. **音效设计**：设计环境音效和背景音乐，烘托戏剧氛围
3. **接受审查**：将设计方案提交给编剧审查，根据反馈进行修改

你的设计原则：
- 遵循京剧舞台"虚实结合"的美学原则
- 布景以写意为主，一桌二椅可代表万千场景
- 音效设计注重锣鼓经的运用（如急急风、慢长锤等）
- 背景音乐选择与剧情氛围匹配的曲牌"""


def create_scene_designer_agent(llm, tools: List = None) -> Agent:
    """
    创建场景设计Agent
    
    Args:
        llm: LLM实例
        tools: 可用工具列表
        
    Returns:
        CrewAI Agent实例
    """
    return Agent(
        role="京剧场景设计师",
        goal=(
            "为每个场景设计符合京剧美学的舞台布景和音效方案，"
            "营造恰当的戏剧氛围，支撑剧情发展"
        ),
        backstory=SCENE_DESIGNER_BACKSTORY,
        tools=tools or [],
        llm=llm,
        memory=True,
        verbose=True,
        allow_delegation=False,
    )
