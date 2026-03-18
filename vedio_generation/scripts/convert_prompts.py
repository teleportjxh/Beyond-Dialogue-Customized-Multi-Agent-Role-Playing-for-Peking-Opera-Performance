"""
Prompt转换脚本
将generated_scripts中的原始数据转换为新的6部分prompt结构
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.utils.file_manager import FileManager

def convert_prompts(task_name: str):
    """转换prompts为新格式"""
    settings = Settings()
    file_manager = FileManager()
    
    # 读取源数据
    source_dir = project_root / "generated_scripts"
    
    # 读取装扮设计
    costume_file = source_dir / f"{task_name}_装扮设计.json"
    costumes = file_manager.read_json(str(costume_file))
    
    # 读取场景设定
    scene_file = source_dir / f"{task_name}_场景设定.json"
    scenes = file_manager.read_json(str(scene_file))
    
    # 读取对话历史
    dialogue_file = source_dir / f"{task_name}_对话历史.json"
    dialogues = file_manager.read_json(str(dialogue_file))
    
    # 按场景组织对话
    scene_dialogues = {}
    current_scene = None
    
    for dialogue in dialogues:
        if dialogue.get('character') == '系统' and '【场景开始】' in dialogue.get('content', ''):
            # 提取场景编号
            scene_desc = dialogue.get('metadata', {}).get('description', '')
            scene_num = dialogue.get('metadata', {}).get('scene_number')
            if not scene_num:
                # 从turn推断场景号
                turn = dialogue.get('turn', 0)
                if turn == 0:
                    scene_num = 1
                elif turn == 10:
                    scene_num = 2
                elif turn == 20:
                    scene_num = 3
            current_scene = scene_num
            if current_scene not in scene_dialogues:
                scene_dialogues[current_scene] = {
                    'description': scene_desc,
                    'dialogues': []
                }
        elif current_scene and dialogue.get('character') != '系统':
            scene_dialogues[current_scene]['dialogues'].append(dialogue)
    
    # 构建新的prompts
    new_prompts = []
    
    for scene_num in sorted(scene_dialogues.keys()):
        scene_data = scene_dialogues[scene_num]
        scene_info = scenes.get(str(scene_num), {})
        
        # 为每个对话轮次创建prompt
        for idx, dialogue in enumerate(scene_data['dialogues'], 1):
            character = dialogue.get('character')
            content = dialogue.get('content', '')
            parsed = dialogue.get('parsed', {})
            
            # 获取角色装扮
            costume = costumes.get(character, {})
            
            # 构建6部分prompt
            prompt = {
                "scene_number": scene_num,
                "round": idx,
                "character": character,
                
                # 1. 核心约束
                "core_constraints": {
                    "style": "京剧表演风格",
                    "focus": "角色直接唱戏，不出现其他内容",
                    "duration": "5-10秒",
                    "camera": "固定机位，全景展示"
                },
                
                # 2. 剧本场景
                "scene_context": {
                    "scene_name": f"场景{scene_num}",
                    "description": scene_data['description'],
                    "scenery": scene_info.get('scenery', ''),
                    "sound_effects": scene_info.get('sound_effects', {})
                },
                
                # 3. 角色装扮
                "character_costume": {
                    "character": character,
                    "role_type": costume.get('role_type', ''),
                    "face_pattern": costume.get('face_pattern', ''),
                    "makeup": costume.get('makeup', ''),
                    "costume": costume.get('costume', ''),
                    "accessories": costume.get('accessories', ''),
                    "overall_style": costume.get('overall_style', '')
                },
                
                # 4. 表演内容
                "performance": {
                    "emotion": parsed.get('emotion', ''),
                    "action": parsed.get('text', '') if parsed.get('type') == '动作' else '',
                    "dialogue": parsed.get('text', '') if parsed.get('type') == '念白' else '',
                    "singing": content if '(唱)' in content or '[西皮' in content or '[二黄' in content else '',
                    "full_content": content
                },
                
                # 5. 音乐伴奏
                "music": {
                    "background": scene_info.get('sound_effects', {}).get('background_music', '京剧传统伴奏'),
                    "rhythm": "根据表演节奏调整",
                    "instruments": "京胡、锣鼓等传统乐器"
                },
                
                # 6. 重要提示
                "important_notes": [
                    "必须展现京剧的程式化动作和身段",
                    "保持角色的脸谱妆容清晰可见",
                    "服装和配饰要符合京剧传统",
                    "表演要有京剧的韵味和节奏感",
                    "背景布景要简洁，突出角色表演"
                ],
                
                # 原始数据引用
                "original_turn": dialogue.get('turn'),
                "timestamp": dialogue.get('timestamp')
            }
            
            new_prompts.append(prompt)
    
    # 保存新的prompts
    output_dir = settings.DATA_DIR / "prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{task_name}_prompts.json"
    file_manager.write_json(output_file, new_prompts)
    
    print(f"✓ 成功转换 {len(new_prompts)} 个prompt")
    print(f"✓ 保存到: {output_file}")
    
    # 打印统计信息
    scene_counts = {}
    for prompt in new_prompts:
        scene_num = prompt['scene_number']
        scene_counts[scene_num] = scene_counts.get(scene_num, 0) + 1
    
    print("\n场景统计:")
    for scene_num in sorted(scene_counts.keys()):
        print(f"  场景{scene_num}: {scene_counts[scene_num]} 个prompt")
    
    return new_prompts

if __name__ == "__main__":
    task_name = "煮酒论英雄"
    
    print(f"开始转换 {task_name} 的prompts...")
    print("=" * 60)
    
    try:
        prompts = convert_prompts(task_name)
        print("\n" + "=" * 60)
        print("转换完成！")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
