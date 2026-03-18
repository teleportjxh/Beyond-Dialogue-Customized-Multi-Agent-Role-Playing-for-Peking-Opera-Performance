"""
数据提取主入口文件
提供命令行接口来执行角色数据提取任务
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_extraction import CharacterDataExtractor
from src.config import Config


def main():
    """主函数：执行角色数据提取"""
    print("=" * 60)
    print("京剧角色数据提取系统")
    print("=" * 60)
    print(f"\n配置信息：")
    print(f"  - 剧本路径: {Config.ENHANCED_SCRIPT_PATH}")
    print(f"  - 角色信息输出: {Config.CHARACTER_PATH}")
    print(f"  - 角色数据输出: {Config.CHARACTER_DATA_PATH}")
    print(f"  - 错误JSON保存: {Config.ERROR_JSON_DIR}")
    print(f"  - 使用模型: {Config.MODEL_NAME}")
    print(f"  - API地址: {Config.BASE_URL}")
    print()
    
    # 确认是否继续
    response = input("是否开始提取？(y/n): ").strip().lower()
    if response != 'y':
        print("已取消提取任务")
        return
    
    print("\n开始提取角色数据...")
    print("-" * 60)
    
    try:
        # 创建提取器实例
        extractor = CharacterDataExtractor()
        
        # 执行提取
        extractor.process_all_characters()
        
        print("\n" + "=" * 60)
        print("数据提取完成！")
        print("=" * 60)
        print(f"\n请查看以下目录：")
        print(f"  - 角色信息: {Config.CHARACTER_PATH}")
        print(f"  - 角色数据: {Config.CHARACTER_DATA_PATH}")
        if os.path.exists(Config.ERROR_JSON_DIR):
            print(f"  - 错误JSON: {Config.ERROR_JSON_DIR}")
        
    except KeyboardInterrupt:
        print("\n\n用户中断提取任务")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n错误：提取过程中发生异常")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
