"""
测试场景设定音效显示修复
"""

from src.script_generation import ScriptGenerationSystem


def test_scene_setting_display():
    """测试场景设定在剧本中的显示效果"""
    print("=" * 70)
    print("测试场景设定显示修复")
    print("=" * 70)
    
    system = ScriptGenerationSystem()
    
    # 生成一个简单的剧本，启用场景设定
    result = system.generate_script(
        user_request="诸葛亮和孙悟空在竹林中论道",
        max_scenes=1,  # 只生成1个场景以快速测试
        max_rounds_per_scene=5,
        enable_scene_setting=True
    )
    
    # 检查场景设定是否正确生成
    if result.get('scene_settings'):
        print("\n✓ 场景设定已生成")
        print("\n场景设定内容：")
        for scene_num, setting in result['scene_settings'].items():
            print(f"\n场景 {scene_num}:")
            print(f"  布景: {setting.get('scenery', '无')}")
            if setting.get('sound_effects'):
                print(f"  环境音: {setting['sound_effects'].get('environment', '无')}")
                print(f"  背景音乐: {setting['sound_effects'].get('background_music', '无')}")
    else:
        print("\n✗ 场景设定未生成")
        return False
    
    # 检查剧本文本中的格式
    script_text = result.get('script', '')
    
    print("\n" + "=" * 70)
    print("检查剧本文本格式")
    print("=" * 70)
    
    # 检查是否包含布景标记
    if '**【布景】**' in script_text:
        print("✓ 剧本包含【布景】标记")
    else:
        print("✗ 剧本缺少【布景】标记")
        return False
    
    # 检查是否包含音效标记
    if '**【音效】**' in script_text:
        print("✓ 剧本包含【音效】标记")
    else:
        print("✗ 剧本缺少【音效】标记")
        return False
    
    # 检查音效是否正确显示（不应该只显示字段名）
    if '- 环境音：' in script_text and '- 背景音乐：' in script_text:
        print("✓ 音效格式正确（包含环境音和背景音乐标签）")
    else:
        print("✗ 音效格式不正确")
        return False
    
    # 检查是否不包含错误的字段名显示
    if '- environment' in script_text or '- background_music' in script_text:
        print("✗ 音效显示了原始字段名（错误）")
        return False
    else:
        print("✓ 音效没有显示原始字段名")
    
    # 显示剧本片段
    print("\n" + "=" * 70)
    print("剧本场景设定部分预览")
    print("=" * 70)
    
    # 提取场景设定部分
    lines = script_text.split('\n')
    in_scene_setting = False
    preview_lines = []
    
    for line in lines:
        if '#### 场景设定' in line:
            in_scene_setting = True
        elif in_scene_setting:
            preview_lines.append(line)
            if '#### 出场角色及顺序' in line:
                break
    
    print('\n'.join(preview_lines[:15]))  # 显示前15行
    
    print("\n" + "=" * 70)
    print("✅ 测试通过！场景设定显示修复成功")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = test_scene_setting_display()
        if success:
            print("\n🎉 所有检查通过！")
        else:
            print("\n❌ 测试失败")
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
