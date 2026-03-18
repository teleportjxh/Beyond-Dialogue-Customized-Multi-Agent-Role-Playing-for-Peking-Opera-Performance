"""
测试场景设定功能
"""

import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.script_generation.main import ScriptGenerationSystem


def test_scene_setting():
    """测试场景设定功能"""
    print("=" * 70)
    print("测试场景设定功能")
    print("=" * 70)
    
    # 初始化系统
    print("\n1. 初始化系统...")
    system = ScriptGenerationSystem(
        character_data_dir="character_data",
        vector_index_dir="vector_index"
    )
    print("✓ 系统初始化完成")
    
    # 生成剧本（启用场景设定）
    print("\n2. 生成剧本（启用场景设定）...")
    user_request = "诸葛亮和孙悟空煮酒论英雄"
    result = system.generate_script(user_request, enable_scene_setting=True)
    print("✓ 剧本生成完成")
    
    # 检查输出文件
    print("\n3. 检查输出文件...")
    output_files = result.get('output_files', {})
    
    script_file = output_files.get('script')
    scene_setting_file = output_files.get('scene_settings')
    
    if script_file and os.path.exists(script_file):
        print(f"✓ 剧本文件存在：{script_file}")
    else:
        print(f"✗ 剧本文件不存在")
        return False
    
    if scene_setting_file and os.path.exists(scene_setting_file):
        print(f"✓ 场景设定文件存在：{scene_setting_file}")
    else:
        print(f"✗ 场景设定文件不存在")
        return False
    
    # 检查剧本内容
    print("\n4. 检查剧本内容...")
    with open(script_file, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 检查是否包含布景和音效
    has_scenery = "【布景】" in script_content
    has_sound = "【音效】" in script_content
    
    if has_scenery:
        print("✓ 剧本包含布景设定")
    else:
        print("✗ 剧本不包含布景设定")
    
    if has_sound:
        print("✓ 剧本包含音效设定")
    else:
        print("✗ 剧本不包含音效设定")
    
    # 显示场景设定示例
    if has_scenery or has_sound:
        print("\n5. 场景设定示例：")
        print("-" * 70)
        lines = script_content.split('\n')
        in_scene = False
        scene_lines = []
        
        for line in lines:
            if line.startswith('【第') and '场】' in line:
                in_scene = True
                scene_lines = [line]
            elif in_scene:
                scene_lines.append(line)
                if line.startswith('【音效】') or (len(scene_lines) > 10):
                    # 显示前10行或到音效为止
                    print('\n'.join(scene_lines[:15]))
                    print("...")
                    break
        print("-" * 70)
    
    # 总结
    print("\n" + "=" * 70)
    if has_scenery and has_sound:
        print("✓ 测试通过！场景设定功能正常工作")
        print("=" * 70)
        return True
    else:
        print("✗ 测试失败！场景设定功能未正常工作")
        print("=" * 70)
        return False


if __name__ == "__main__":
    try:
        success = test_scene_setting()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试出错：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
