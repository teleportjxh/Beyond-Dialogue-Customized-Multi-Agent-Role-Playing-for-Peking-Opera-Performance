"""
重新生成剧本脚本
使用改进后的格式化器重新生成煮酒论英雄剧本
"""

import json
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from script_generation.script_formatter import ScriptFormatter


def main():
    """主函数"""
    # 读取大纲
    with open('generated_scripts/煮酒论英雄_大纲.json', 'r', encoding='utf-8') as f:
        outline = json.load(f)
    
    # 读取对话历史
    with open('generated_scripts/煮酒论英雄_对话历史.json', 'r', encoding='utf-8') as f:
        dialogue_history = json.load(f)
    
    # 创建格式化器
    formatter = ScriptFormatter()
    
    # 格式化剧本
    print("正在格式化剧本...")
    script = formatter.format_script(outline, dialogue_history)
    
    # 保存剧本
    output_path = 'generated_scripts/煮酒论英雄_剧本_改进版.txt'
    formatter.export_to_file(script, output_path)
    
    print(f"剧本已保存到: {output_path}")
    print("\n预览前100行:")
    print("=" * 60)
    lines = script.split('\n')
    for line in lines[:100]:
        print(line)
    if len(lines) > 100:
        print(f"\n... (还有 {len(lines) - 100} 行)")


if __name__ == '__main__':
    main()
