"""
京剧多Agent创作系统 - 主入口
基于 CrewAI 框架的多Agent协作京剧剧本创作
"""
import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主函数"""
    from src.crew.opera_crew import PekingOperaCrew
    
    print("=" * 60)
    print("  京剧多Agent创作系统 (CrewAI版)")
    print("  Beyond Dialogue: Multi-Agent Peking Opera")
    print("=" * 60)
    
    # 获取用户输入
    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        print("\n请输入您的创作需求（例如：请创作一出诸葛亮和孙悟空的京剧）")
        print("可用角色: 诸葛亮、孙悟空、赵匡胤")
        user_request = input("\n> ").strip()
    
    if not user_request:
        print("未输入需求，使用默认示例...")
        user_request = "请创作一出诸葛亮和孙悟空相遇的京剧，主题是智慧与力量的碰撞"
    
    # 创建并运行Crew
    crew = PekingOperaCrew()
    result = crew.run(user_request)
    
    if "error" in result:
        print("\n创作失败: " + result["error"])
        return
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("创作摘要")
    print("=" * 60)
    
    outline = result.get('outline', {})
    print("标题: " + outline.get('title', '未命名'))
    print("主题: " + outline.get('theme', '未知'))
    print("角色: " + ", ".join(result.get('characters', [])))
    
    dialogues = result.get('dialogues', [])
    print("对话轮数: " + str(len(dialogues)))
    
    evaluation = result.get('evaluation', {})
    if isinstance(evaluation, dict) and 'overall_score' in evaluation:
        print("总评分: " + str(evaluation['overall_score']))
    
    print("\n结果已保存到 generated_scripts/ 目录")


if __name__ == "__main__":
    main()
