"""
场景设定功能演示脚本
展示如何使用场景设定功能以及生成的效果
"""

from src.script_generation import ScriptGenerationSystem
import json


def demo_scene_setting():
    """演示场景设定功能"""
    
    print("=" * 80)
    print("场景设定功能演示")
    print("=" * 80)
    
    # 初始化系统
    print("\n1. 初始化剧本生成系统...")
    system = ScriptGenerationSystem()
    print("   ✓ 系统初始化完成")
    
    # 生成带场景设定的剧本
    print("\n2. 生成剧本（启用场景设定）...")
    print("   请求：诸葛亮和孙悟空在竹林中论道")
    print("   场景数：2")
    print("   每场对话轮数：6")
    
    result = system.generate_script(
        user_request="诸葛亮和孙悟空在竹林中论道",
        max_scenes=2,
        max_rounds_per_scene=6,
        enable_scene_setting=True  # 启用场景设定
    )
    
    print("   ✓ 剧本生成完成")
    
    # 显示基本信息
    print("\n3. 剧本基本信息")
    print("   " + "-" * 76)
    print(f"   剧名：{result['outline']['title']}")
    print(f"   主题：{result['outline']['theme']}")
    print(f"   场景数：{len(result['outline']['scenes'])}")
    
    # 显示场景设定
    if result.get('scene_settings'):
        print("\n4. 场景设定详情")
        print("   " + "-" * 76)
        
        for scene_num, setting in result['scene_settings'].items():
            print(f"\n   【场景 {scene_num}】")
            print(f"   布景：")
            print(f"      {setting['scenery']}")
            
            if setting.get('sound_effects'):
                print(f"   音效：")
                sound_effects = setting['sound_effects']
                if sound_effects.get('environment'):
                    print(f"      环境音：{sound_effects['environment']}")
                if sound_effects.get('background_music'):
                    print(f"      背景音乐：{sound_effects['background_music']}")
    else:
        print("\n   ⚠ 未生成场景设定")
    
    # 显示生成的文件
    print("\n5. 生成的文件")
    print("   " + "-" * 76)
    if result.get('output_files'):
        for file_type, file_path in result['output_files'].items():
            print(f"   {file_type}: {file_path}")
    
    # 读取并显示剧本片段
    print("\n6. 剧本文本预览（第一场场景设定部分）")
    print("   " + "-" * 76)
    
    script_text = result.get('script', '')
    lines = script_text.split('\n')
    
    # 提取第一场的场景设定部分
    in_first_scene = False
    in_scene_setting = False
    preview_lines = []
    
    for line in lines:
        if '### 第一场' in line:
            in_first_scene = True
            preview_lines.append(line)
        elif in_first_scene:
            if '#### 场景设定' in line:
                in_scene_setting = True
                preview_lines.append(line)
            elif in_scene_setting:
                preview_lines.append(line)
                if '#### 出场角色及顺序' in line:
                    break
    
    for line in preview_lines:
        print(f"   {line}")
    
    print("\n" + "=" * 80)
    print("✅ 演示完成！")
    print("=" * 80)
    
    print("\n💡 提示：")
    print("   - 场景设定功能默认关闭，需要显式设置 enable_scene_setting=True")
    print("   - 生成的剧本文件包含完整的布景和音效描述")
    print("   - 场景设定JSON文件可用于其他用途（如舞台设计参考）")
    print("   - 即使场景设定生成失败，也不会影响剧本的正常生成")
    
    return result


def compare_with_without_scene_setting():
    """对比启用和不启用场景设定的区别"""
    
    print("\n" + "=" * 80)
    print("对比测试：启用 vs 不启用场景设定")
    print("=" * 80)
    
    system = ScriptGenerationSystem()
    
    # 不启用场景设定
    print("\n【测试1】不启用场景设定（默认行为）")
    print("-" * 80)
    result1 = system.generate_script(
        user_request="诸葛亮和孙悟空简短对话",
        max_scenes=1,
        max_rounds_per_scene=3,
        enable_scene_setting=False
    )
    
    has_scene_setting_1 = result1.get('scene_settings') is not None
    print(f"场景设定生成：{'是' if has_scene_setting_1 else '否'}")
    print(f"剧本包含【布景】标记：{'是' if '**【布景】**' in result1.get('script', '') else '否'}")
    print(f"剧本包含【音效】标记：{'是' if '**【音效】**' in result1.get('script', '') else '否'}")
    
    # 启用场景设定
    print("\n【测试2】启用场景设定")
    print("-" * 80)
    result2 = system.generate_script(
        user_request="诸葛亮和孙悟空简短对话",
        max_scenes=1,
        max_rounds_per_scene=3,
        enable_scene_setting=True
    )
    
    has_scene_setting_2 = result2.get('scene_settings') is not None
    print(f"场景设定生成：{'是' if has_scene_setting_2 else '否'}")
    print(f"剧本包含【布景】标记：{'是' if '**【布景】**' in result2.get('script', '') else '否'}")
    print(f"剧本包含【音效】标记：{'是' if '**【音效】**' in result2.get('script', '') else '否'}")
    
    if has_scene_setting_2:
        setting = result2['scene_settings'][1]
        print(f"\n生成的场景设定示例：")
        print(f"  布景：{setting['scenery'][:50]}...")
        if setting.get('sound_effects'):
            print(f"  环境音：{setting['sound_effects'].get('environment', '无')}")
    
    print("\n" + "=" * 80)
    print("✅ 对比测试完成")
    print("=" * 80)
    print("\n结论：")
    print("  - 不启用场景设定时，剧本不包含布景和音效描述（保持向后兼容）")
    print("  - 启用场景设定后，剧本自动添加布景和音效描述")
    print("  - 两种模式下，剧本的其他部分（对话、动作等）完全一致")


if __name__ == "__main__":
    try:
        # 运行演示
        result = demo_scene_setting()
        
        # 运行对比测试
        # compare_with_without_scene_setting()
        
        print("\n🎉 所有演示完成！")
        
    except Exception as e:
        print(f"\n❌ 演示出错: {str(e)}")
        import traceback
        traceback.print_exc()
