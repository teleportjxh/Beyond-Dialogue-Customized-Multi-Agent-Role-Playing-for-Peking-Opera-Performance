"""
京剧剧本生成系统 - 主入口
整合数据提取、RAG系统和多Agent剧本生成的完整流程
"""

import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.script_generation.main import ScriptGenerationSystem


def print_banner():
    """打印系统横幅"""
    print("\n" + "=" * 70)
    print("京剧剧本生成系统".center(66))
    print("基于多Agent协作的智能剧本创作平台".center(60))
    print("=" * 70 + "\n")


def print_menu():
    """打印菜单"""
    print("\n请选择操作：")
    print("1. 生成新剧本")
    print("2. 查看示例剧本")
    print("3. 查看系统说明")
    print("0. 退出")
    print("-" * 70)


def show_examples():
    """显示示例剧本"""
    print("\n" + "=" * 70)
    print("示例剧本".center(66))
    print("=" * 70)
    
    examples = [
        "诸葛亮和孙悟空煮酒论英雄",
        "孙悟空大闹天宫",
        "诸葛亮空城计",
        "孙悟空三打白骨精",
        "诸葛亮草船借箭"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    
    print("\n提示：您可以输入类似的剧本需求，系统会自动：")
    print("  - 识别涉及的角色")
    print("  - 从RAG系统检索相关场景")
    print("  - 通过4个Agent协作生成完整剧本")
    print("=" * 70)


def show_system_info():
    """显示系统说明"""
    print("\n" + "=" * 70)
    print("系统说明".center(66))
    print("=" * 70)
    
    info = """
【系统架构】
本系统采用多Agent协作架构，包含4个专业Agent：

1. 编剧Agent（ScreenwriterAgent）
   - 负责：分析用户需求，提取角色，生成剧本大纲
   - 特点：结合RAG检索相关场景，确保剧本符合京剧风格

2. 定妆师Agent（CostumeDesignerAgent）
   - 负责：为每个角色设计装扮（行当、脸谱、服饰）
   - 特点：基于角色特征和剧本主题，设计符合京剧规范的装扮

3. 演员Agent（ActorAgent）
   - 负责：扮演具体角色，生成对话和表演
   - 特点：每个角色由独立Agent扮演，实时同步对话

4. 导演Agent（DirectorAgent）
   - 负责：评估剧本质量，提供修改建议
   - 特点：从京剧特色、角色塑造、剧情结构等维度评分

【工作流程】
步骤1：大纲建立
  - 提取角色
  - RAG检索相关场景
  - 生成剧本大纲（主题、场景、情节）

步骤2：人物特征完善
  - 为每个角色设计装扮
  - 确定行当、脸谱、服饰

步骤3：剧本完善
  - 初始化演员Agents
  - 多轮对话生成（演员实时同步）
  - 生成完整剧本

步骤4：剧本评估
  - 导演评估剧本质量
  - 提供修改建议

【输出文件】
系统会在 generated_scripts/ 目录下生成：
  - {剧名}_剧本.txt：完整的京剧剧本
  - {剧名}_大纲.json：剧本大纲
  - {剧名}_装扮设计.json：角色装扮设计
  - {剧名}_对话历史.json：对话历史记录
  - {剧名}_评估报告.json：导演评估报告
  - {剧名}_修改指导.txt：修改建议

【技术特点】
- RAG语义检索：自动检索最相关的历史场景
- 多Agent协作：4个专业Agent分工协作
- 实时同步：演员Agent实时同步对话
- 京剧规范：严格遵循京剧艺术规范（唱念做打、行当、脸谱）
"""
    
    print(info)
    print("=" * 70)


def generate_script_interactive():
    """交互式生成剧本"""
    print("\n" + "=" * 70)
    print("剧本生成".center(66))
    print("=" * 70)
    
    # 获取用户需求
    print("\n请输入您的剧本需求（例如：诸葛亮和孙悟空煮酒论英雄）：")
    user_request = input("> ").strip()
    
    if not user_request:
        print("❌ 需求不能为空")
        return
    
    # 确认生成
    print(f"\n您的需求：{user_request}")
    print("系统将自动：")
    print("  1. 识别涉及的角色")
    print("  2. 从RAG系统检索相关场景")
    print("  3. 通过4个Agent协作生成完整剧本")
    print("\n是否开始生成？(y/n)")
    
    confirm = input("> ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    # 初始化系统
    try:
        print("\n正在初始化系统...")
        system = ScriptGenerationSystem(
            character_data_dir="character_data",
            vector_index_dir="vector_index"
        )
        
        # 生成剧本
        print("\n开始生成剧本...\n")
        result = system.generate_script(user_request, enable_scene_setting=True)
        
        # 显示结果
        print("\n" + "=" * 70)
        print("生成完成！".center(66))
        print("=" * 70)
        
        output_files = result.get('output_files', {})
        print(f"\n✓ 剧本已保存：{output_files.get('script', 'N/A')}")
        print(f"✓ 大纲已保存：{output_files.get('outline', 'N/A')}")
        print(f"✓ 装扮设计已保存：{output_files.get('costumes', 'N/A')}")
        print(f"✓ 对话历史已保存：{output_files.get('dialogue', 'N/A')}")
        print(f"✓ 评估报告已保存：{output_files.get('evaluation', 'N/A')}")
        print(f"✓ 修改指导已保存：{output_files.get('guidance', 'N/A')}")
        
        # 询问是否查看剧本
        print("\n是否查看生成的剧本？(y/n)")
        view = input("> ").strip().lower()
        if view == 'y' and output_files.get('script'):
            with open(output_files['script'], 'r', encoding='utf-8') as f:
                print("\n" + "=" * 70)
                print(f.read())
                print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 生成失败：{str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print_banner()
    
    while True:
        print_menu()
        choice = input("请选择 (0-3): ").strip()
        
        if choice == '0':
            print("\n感谢使用京剧剧本生成系统！")
            break
        elif choice == '1':
            generate_script_interactive()
        elif choice == '2':
            show_examples()
        elif choice == '3':
            show_system_info()
        else:
            print("\n❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()
