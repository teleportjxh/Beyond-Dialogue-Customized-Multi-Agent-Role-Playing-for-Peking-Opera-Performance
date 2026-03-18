"""
简化的Prompt提取器 - 直接从JSON解析，不使用大模型
组合：通用京剧描述 + 场景设定 + 角色装扮 + 具体动作/念白
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)


def _load_scene_settings(script_name: str) -> Dict:
    """加载场景设定"""
    scene_file = Path(f"generated_scripts/{script_name}_场景设定.json")
    if scene_file.exists():
        with open(scene_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    logger.warning(f"场景设定文件不存在: {scene_file}")
    return {}


def _load_costume_designs(script_name: str) -> Dict:
    """加载装扮设计"""
    costume_file = Path(f"generated_scripts/{script_name}_装扮设计.json")
    if costume_file.exists():
        with open(costume_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    logger.warning(f"装扮设计文件不存在: {costume_file}")
    return {}


def _extract_scene_number(scene_id: str) -> Optional[str]:
    """从场景ID提取数字，如'场景2' -> '2'"""
    match = re.search(r'\d+', scene_id)
    return match.group() if match else None


def _format_scene_description(scene_data: Dict) -> str:
    """格式化场景描述为英文"""
    if not scene_data:
        return ""
    
    parts = []
    
    # 场景布置
    if 'scenery' in scene_data:
        parts.append(f"Scene: {scene_data['scenery']}")
    
    # 音效
    if 'sound_effects' in scene_data:
        sound = scene_data['sound_effects']
        sound_parts = []
        if 'environment' in sound:
            sound_parts.append(f"ambient sounds: {sound['environment']}")
        if 'background_music' in sound:
            sound_parts.append(f"background music: {sound['background_music']}")
        if sound_parts:
            parts.append(f"Audio: {', '.join(sound_parts)}")
    
    return ". ".join(parts) if parts else ""


def _format_costume_description(costume_data: Dict) -> str:
    """格式化角色装扮描述为英文"""
    if not costume_data:
        return ""
    
    parts = []
    
    # 角色和行当
    character = costume_data.get('character', '')
    role_type = costume_data.get('role_type', '')
    if character and role_type:
        parts.append(f"Character: {character} - {role_type} role type")
    
    # 脸谱
    if 'face_pattern' in costume_data:
        parts.append(f"Face: {costume_data['face_pattern']}")
    
    # 服装
    if 'costume' in costume_data:
        parts.append(f"Costume: {costume_data['costume']}")
    
    # 整体风格
    if 'overall_style' in costume_data:
        parts.append(f"Style: {costume_data['overall_style']}")
    
    return ". ".join(parts) if parts else ""


def _build_complete_prompt(
    character: str,
    emotion: str,
    content_text: str,
    scene_desc: str,
    costume_desc: str,
    improvements: Optional[List[Dict]] = None
) -> str:
    """
    构建完整的prompt
    结构：通用京剧描述 + 场景 + 装扮 + 具体表演 + 改进要求（可选）
    
    Args:
        character: 角色名
        emotion: 情感描述
        content_text: 表演内容文本
        scene_desc: 场景描述
        costume_desc: 装扮描述
        improvements: 改进建议列表（可选），每项包含dimension, problem, suggestion
    """
    parts = []
    
    # 1. 通用京剧描述（固定）
    parts.append(
        "Chinese Peking Opera performance. "
        "Traditional theatrical style with elaborate costumes, "
        "stylized movements, and cultural authenticity."
    )
    
    # 2. 场景描述（基础信息，迭代中保持不变）
    if scene_desc:
        parts.append(scene_desc)
    
    # 3. 角色装扮（基础信息，迭代中保持不变）
    if costume_desc:
        parts.append(costume_desc)
    
    # 4. 具体表演（保持中文）
    performance_parts = []
    if emotion:
        performance_parts.append(f"with emotion ({emotion})")
    performance_parts.append(f"{character} performs: {content_text}")
    
    # 5. 应用改进建议（如果有）
    if improvements:
        improvement_notes = []
        for imp in improvements:
            suggestion = imp.get('suggestion', '')
            if suggestion:
                improvement_notes.append(suggestion)
        
        if improvement_notes:
            performance_parts.append("\nRefinements: " + "; ".join(improvement_notes))
    
    parts.append("Performance: " + " ".join(performance_parts))
    
    return "\n\n".join(parts)


def extract_prompts_simple(script_name: str) -> List[Dict]:
    """
    直接从对话历史JSON提取prompt，组合场景和装扮信息
    
    Args:
        script_name: 剧本名称（不含扩展名）
        
    Returns:
        List[Dict]: 提取的prompt列表，每个包含：
            - scene_id: 场景ID
            - character: 角色名
            - prompt: 完整的prompt文本
            - emotion: 情感描述
            - type: 内容类型（念白/动作/唱词）
            - turn: 对话轮次
    """
    dialogue_file = Path(f"generated_scripts/{script_name}_对话历史.json")
    
    if not dialogue_file.exists():
        raise FileNotFoundError(f"对话历史文件不存在: {dialogue_file}")
    
    logger.info(f"从 {dialogue_file} 提取prompts...")
    
    # 加载所有相关文件
    with open(dialogue_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scene_settings = _load_scene_settings(script_name)
    costume_designs = _load_costume_designs(script_name)
    
    logger.info(f"加载了 {len(scene_settings)} 个场景设定")
    logger.info(f"加载了 {len(costume_designs)} 个角色装扮")
    
    prompts = []
    # JSON文件本身就是数组格式，不是对象
    turns = data if isinstance(data, list) else data.get('turns', [])
    
    for idx, turn in enumerate(turns, 1):
        character = turn.get('character', '未知角色')
        parsed = turn.get('parsed', {})
        
        # 提取核心信息
        emotion = parsed.get('emotion', '')
        content_type = parsed.get('type', '')
        content_text = parsed.get('text', '')
        
        # 跳过空内容
        if not content_text.strip():
            logger.info(f"场景{idx} - {character}: 跳过空内容")
            continue
        
        # 构建场景ID并提取场景编号
        scene_id = f"场景{idx}"
        scene_num = _extract_scene_number(scene_id)
        
        # 获取场景描述
        scene_desc = ""
        if scene_num and scene_num in scene_settings:
            scene_desc = _format_scene_description(scene_settings[scene_num])
        
        # 获取角色装扮描述
        costume_desc = ""
        if character in costume_designs:
            costume_desc = _format_costume_description(costume_designs[character])
        
        # 构建完整prompt
        prompt = _build_complete_prompt(
            character=character,
            emotion=emotion,
            content_text=content_text,
            scene_desc=scene_desc,
            costume_desc=costume_desc
        )
        
        prompt_info = {
            'scene_id': scene_id,
            'character': character,
            'prompt': prompt,
            'emotion': emotion,
            'type': content_type,
            'turn': idx,
            'raw_text': content_text,
            'scene_desc': scene_desc,      # 添加场景描述，用于迭代时保持不变
            'costume_desc': costume_desc,  # 添加装扮描述，用于迭代时保持不变
            'content_text': content_text   # 添加原始内容文本
        }
        
        prompts.append(prompt_info)
        logger.info(f"{scene_id} - {character} ({content_type}): {emotion}")
    
    logger.info(f"成功提取 {len(prompts)} 个prompts")
    
    # 保存提取结果
    output_file = Path(f"generated_scripts/{script_name}_prompts_complete.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    logger.info(f"完整Prompts已保存到: {output_file}")
    
    return prompts


def main():
    """测试函数"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("用法: python simple_prompt_extractor.py <剧本名称>")
        print("示例: python simple_prompt_extractor.py 煮酒论英雄")
        sys.exit(1)
    
    script_name = sys.argv[1]
    
    try:
        prompts = extract_prompts_simple(script_name)
        print(f"\n成功提取 {len(prompts)} 个prompts:")
        for p in prompts:
            print(f"\n{p['scene_id']}:")
            print(f"  角色: {p['character']}")
            print(f"  类型: {p['type']}")
            print(f"  情感: {p['emotion']}")
            print(f"  Prompt: {p['prompt'][:100]}...")
    except Exception as e:
        logger.error(f"提取失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
