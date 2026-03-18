"""
测试迭代机制修复 - 验证场景和装扮信息在迭代中保持不变
"""
from src.extractor.simple_prompt_extractor import _build_complete_prompt


def test_prompt_with_improvements():
    """测试带改进建议的prompt构建"""
    
    # 基础信息（应该在迭代中保持不变）
    character = "孙悟空"
    emotion = "机敏活泼，神采飞扬"
    content_text = '[一个"筋斗"翻至台中，停顿，手搭凉棚四处观望]'
    
    scene_desc = (
        "Scene: 舞台中央布置一张方桌，两侧各置一椅，桌上摆放茶具。"
        "背景是一幅大气的山水画，营造出雅致的谈话氛围。 "
        "Audio: ambient sounds: 偶有风声、虫鸣声, background music: 轻柔的琵琶背景音乐"
    )
    
    costume_desc = (
        "Character: 孙悟空 - 武生 role type. "
        "Face: 金色猴脸，经典倒栽桃心脸谱，红色心形勾勒眼、鼻、嘴. "
        "Costume: 头戴凤翅紫金冠，配两根长翎子，身穿黄色紧身短打，腰系战裙. "
        "Style: 威武神勇，灵动飘逸"
    )
    
    # 第一次生成（无改进建议）
    print("=" * 80)
    print("第1次迭代 - 初始Prompt:")
    print("=" * 80)
    
    initial_prompt = _build_complete_prompt(
        character=character,
        emotion=emotion,
        content_text=content_text,
        scene_desc=scene_desc,
        costume_desc=costume_desc,
        improvements=None
    )
    print(initial_prompt)
    
    # 模拟评估后的改进建议
    improvements = [
        {
            "dimension": "action_quality",
            "problem": "动作表现不够流畅",
            "suggestion": "Emphasize the fluidity and agility of the somersault movement"
        },
        {
            "dimension": "costume_accuracy",
            "problem": "装扮细节不够清晰",
            "suggestion": "Highlight the golden monkey face and phoenix crown details"
        }
    ]
    
    # 第二次生成（有改进建议，但保留场景和装扮）
    print("\n" + "=" * 80)
    print("第2次迭代 - 应用改进建议后的Prompt:")
    print("=" * 80)
    
    improved_prompt = _build_complete_prompt(
        character=character,
        emotion=emotion,
        content_text=content_text,
        scene_desc=scene_desc,      # 保持不变
        costume_desc=costume_desc,  # 保持不变
        improvements=improvements    # 添加改进建议
    )
    print(improved_prompt)
    
    # 验证关键信息存在
    print("\n" + "=" * 80)
    print("验证结果:")
    print("=" * 80)
    
    checks = {
        "场景描述包含'方桌'": "方桌" in improved_prompt,
        "场景描述包含'山水画'": "山水画" in improved_prompt,
        "装扮描述包含'凤翅紫金冠'": "凤翅紫金冠" in improved_prompt,
        "装扮描述包含'金色猴脸'": "金色猴脸" in improved_prompt,
        "包含改进建议1": "fluidity" in improved_prompt.lower(),
        "包含改进建议2": "phoenix crown" in improved_prompt.lower(),
        "仍然包含原始表演内容": content_text in improved_prompt,
        "仍然包含情感描述": emotion in improved_prompt
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check_name}: {result}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ 所有验证通过！场景和装扮信息在迭代中成功保留。")
    else:
        print("✗ 部分验证失败，请检查实现。")
    print("=" * 80)
    
    return all_passed


def test_improvements_extraction():
    """测试从评估结果中提取改进建议"""
    
    # 模拟评估结果
    evaluation = {
        'overall_score': 6.5,
        'passed': False,
        'dimension_scores': {
            'costume_accuracy': 7.0,
            'action_quality': 6.0,
            'dialogue_delivery': 7.5,
            'scene_consistency': 6.0,
            'overall_impression': 6.0
        },
        'improvement_suggestions': [
            {
                'dimension': 'action_quality',
                'problem': '动作不够连贯',
                'suggestion': 'Make the movements more fluid and continuous'
            },
            {
                'dimension': 'scene_consistency',
                'problem': '场景元素不清晰',
                'suggestion': 'Ensure all scene elements from the prompt are visible'
            }
        ]
    }
    
    print("\n" + "=" * 80)
    print("测试改进建议提取:")
    print("=" * 80)
    
    improvements = evaluation.get('improvement_suggestions', [])
    print(f"提取到 {len(improvements)} 条改进建议:")
    
    for i, imp in enumerate(improvements, 1):
        print(f"\n{i}. 维度: {imp.get('dimension', 'N/A')}")
        print(f"   问题: {imp.get('problem', 'N/A')}")
        print(f"   建议: {imp.get('suggestion', 'N/A')}")
    
    return len(improvements) > 0


if __name__ == "__main__":
    print("测试迭代机制修复 - 验证场景和装扮信息保留")
    print()
    
    # 测试1: 改进建议应用
    test1_passed = test_prompt_with_improvements()
    
    # 测试2: 改进建议提取
    test2_passed = test_improvements_extraction()
    
    print("\n" + "=" * 80)
    print("总体测试结果:")
    print("=" * 80)
    print(f"✓ 测试1 (Prompt构建): {'通过' if test1_passed else '失败'}")
    print(f"✓ 测试2 (建议提取): {'通过' if test2_passed else '失败'}")
    
    if test1_passed and test2_passed:
        print("\n✓✓✓ 所有测试通过！迭代机制修复成功。")
    else:
        print("\n✗✗✗ 部分测试失败，需要进一步调试。")
