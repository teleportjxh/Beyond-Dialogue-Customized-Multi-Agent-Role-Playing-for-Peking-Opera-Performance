"""
CrewAI Task 定义
定义京剧创作流程中的所有任务
"""
from crewai import Task, Agent
from typing import List, Optional


def create_outline_task(screenwriter: Agent, user_request: str, characters_info: str) -> Task:
    """
    创建剧本大纲任务
    
    Args:
        screenwriter: 编剧Agent
        user_request: 用户需求
        characters_info: 角色信息
    """
    return Task(
        description=f"""根据以下用户需求创作京剧剧本大纲：

## 用户需求
{user_request}

## 可用角色信息
{characters_info}

## 输出要求
请创作一个完整的京剧剧本大纲，以JSON格式输出，包含：
1. title: 剧本标题
2. theme: 主题
3. synopsis: 剧情梗概
4. characters: 角色列表（每个角色包含name, role_type行当, description）
5. scenes: 场景列表（每个场景包含name, description, characters出场角色, key_events关键事件, emotion_tone情绪基调）

确保：
- 遵循京剧"起承转合"的戏剧结构
- 每个场景都有明确的戏剧冲突
- 角色之间有充分的互动""",
        agent=screenwriter,
        expected_output="JSON格式的京剧剧本大纲，包含标题、主题、角色、场景等完整信息"
    )


def create_costume_design_task(
    costume_designer: Agent,
    outline_context: str,
    characters_info: str
) -> Task:
    """创建服装设计任务"""
    return Task(
        description=f"""根据剧本大纲和角色信息，为每个角色设计京剧服装和脸谱方案。

## 剧本大纲
{outline_context}

## 角色信息
{characters_info}

## 输出要求
以JSON格式输出每个角色的装扮设计，包含：
1. character: 角色名
2. role_type: 行当（生/旦/净/末/丑）
3. costume: 服装描述（包括头饰、上衣、下装、靴鞋）
4. face_paint: 脸谱描述（如适用）
5. props: 道具列表
6. color_scheme: 主色调及寓意

确保服装设计符合京剧传统规制。""",
        agent=costume_designer,
        expected_output="JSON格式的角色装扮设计方案"
    )


def create_costume_review_task(screenwriter: Agent, costume_design: str) -> Task:
    """创建服装设计审查任务（编剧审查）"""
    return Task(
        description=f"""审查以下服装设计方案，检查是否符合剧本需求和京剧传统规制。

## 服装设计方案
{costume_design}

## 审查要点
1. 服装是否与角色身份匹配？
2. 颜色搭配是否符合京剧传统寓意？
3. 是否有不合理或不协调之处？
4. 整体视觉效果是否和谐？

## 输出要求
给出审查意见，包括：
- approved: 是否通过（true/false）
- feedback: 具体审查意见
- suggestions: 修改建议（如有）""",
        agent=screenwriter,
        expected_output="JSON格式的审查结果，包含是否通过和具体意见"
    )


def create_scene_design_task(
    scene_designer: Agent,
    outline_context: str
) -> Task:
    """创建场景设计任务"""
    return Task(
        description=f"""根据剧本大纲，为每个场景设计布景和音效方案。

## 剧本大纲
{outline_context}

## 输出要求
以JSON格式输出每个场景的设计方案，包含：
1. scene_number: 场景编号
2. scene_name: 场景名称
3. scenery: 布景描述（舞台布置、道具摆放）
4. lighting: 灯光设计
5. sound_effects: 音效设计
   - environment: 环境音
   - background_music: 背景音乐/曲牌
   - luogu: 锣鼓经提示
6. atmosphere: 整体氛围描述

遵循京剧舞台"虚实结合"的美学原则。""",
        agent=scene_designer,
        expected_output="JSON格式的场景设计方案"
    )


def create_scene_review_task(screenwriter: Agent, scene_design: str) -> Task:
    """创建场景设计审查任务（编剧审查）"""
    return Task(
        description=f"""审查以下场景设计方案，检查是否符合剧本需求和京剧美学。

## 场景设计方案
{scene_design}

## 审查要点
1. 布景是否与剧情氛围匹配？
2. 音效设计是否恰当？
3. 锣鼓经使用是否规范？
4. 场景过渡是否自然？

## 输出要求
给出审查意见，包括：
- approved: 是否通过（true/false）
- feedback: 具体审查意见
- suggestions: 修改建议（如有）""",
        agent=screenwriter,
        expected_output="JSON格式的审查结果"
    )


def create_action_plan_task(
    screenwriter: Agent,
    scene_outline: str,
    scene_number: int
) -> Task:
    """创建演员行动规划任务（编剧为演员规划）"""
    return Task(
        description=f"""为第{scene_number}场戏规划演员的表演行动。

## 场景信息
{scene_outline}

## 输出要求
为该场景中的每个角色规划：
1. character: 角色名
2. entrance: 出场方式和时机
3. emotion_arc: 情绪变化弧线
4. key_lines_direction: 关键台词方向提示
5. interaction_points: 与其他角色的互动要点
6. exit: 退场方式

确保每个角色的行动都服务于剧情发展。""",
        agent=screenwriter,
        expected_output="JSON格式的演员行动规划"
    )


def create_dialogue_task(
    actor: Agent,
    character_name: str,
    scene_context: str,
    action_plan: str,
    dialogue_history: str
) -> Task:
    """创建对话生成任务"""
    return Task(
        description=f"""你现在以{character_name}的身份进行表演。

## 当前场景
{scene_context}

## 编剧给你的行动规划
{action_plan}

## 之前的对话
{dialogue_history}

## 要求
1. 以{character_name}的身份生成一段对话
2. 严格使用京剧剧本格式（【念】【唱】【做】【情】）
3. 保持角色一致性
4. 生成后进行自我审查

## 自我审查
生成对话后，请在末尾附上自我审查结果：
- [自审] 角色一致性: 通过/需修改
- [自审] 京剧规范: 通过/需修改
- [自审] 情感表达: 通过/需修改
如有需修改项，请直接修改后输出最终版本。""",
        agent=actor,
        expected_output=f"{character_name}的京剧对话，包含唱念做打元素和自我审查结果"
    )


def create_dialogue_review_task(
    director: Agent,
    character_name: str,
    dialogue: str,
    scene_context: str
) -> Task:
    """创建对话审查任务（导演审查）"""
    return Task(
        description=f"""审查{character_name}的以下对话表演。

## 对话内容
{dialogue}

## 场景上下文
{scene_context}

## 审查标准
1. 角色一致性：对话是否符合{character_name}的性格？
2. 京剧规范：唱念做打的使用是否规范？
3. 情感表达：情感是否真实、与剧情匹配？
4. 剧情推进：对话是否推动了剧情发展？
5. 艺术质量：语言是否有京剧韵味？

## 输出要求
- approved: 是否通过（true/false）
- score: 评分（1-10）
- feedback: 具体意见
- revision_needed: 是否需要修改
- revision_guidance: 修改指导（如需要）""",
        agent=director,
        expected_output="JSON格式的对话审查结果"
    )


def create_next_speaker_task(
    director: Agent,
    scene_context: str,
    dialogue_history: str,
    available_characters: str
) -> Task:
    """创建决定下一个说话者的任务"""
    return Task(
        description=f"""决定下一轮对话中哪个角色应该说话。

## 当前场景
{scene_context}

## 已有对话
{dialogue_history}

## 可用角色
{available_characters}

## 决策依据
1. 对话的自然流转（谁被提问/被提及应该回应）
2. 剧情推进需要（哪个角色的发言能推动剧情）
3. 表演节奏（避免某个角色连续说太多）
4. 是否需要场景转换

## 输出要求
- next_speaker: 下一个说话的角色名
- reason: 选择理由
- scene_transition: 是否需要场景转换（true/false）
- dialogue_end: 该场景对话是否应该结束（true/false）""",
        agent=director,
        expected_output="JSON格式的下一个说话者决策"
    )


def create_final_evaluation_task(
    director: Agent,
    full_script: str
) -> Task:
    """创建最终评估任务"""
    return Task(
        description=f"""对以下完整剧本进行最终质量评估。

## 完整剧本
{full_script}

## 评估维度
1. 剧情完整性（1-10分）：起承转合是否完整？
2. 角色塑造（1-10分）：角色是否鲜明、一致？
3. 京剧规范（1-10分）：唱念做打是否规范？
4. 艺术质量（1-10分）：语言是否优美？
5. 整体节奏（1-10分）：节奏是否张弛有度？

## 输出要求
- scores: 各维度评分
- overall_score: 总分
- strengths: 优点列表
- weaknesses: 不足列表
- improvement_suggestions: 改进建议""",
        agent=director,
        expected_output="JSON格式的剧本评估报告"
    )
