"""简单测试脚本 - 请直接运行并查看输出"""

print("开始测试...")

# 测试1: 基本导入
try:
    from src.config import Config
    print("✓ Config导入成功")
except Exception as e:
    print(f"✗ Config导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 检查路径
try:
    import os
    print(f"\n当前工作目录: {os.getcwd()}")
    print(f"enhanced_script存在: {os.path.exists('enhanced_script')}")
    print(f"character存在: {os.path.exists('character')}")
    print(f"src目录存在: {os.path.exists('src')}")
except Exception as e:
    print(f"✗ 路径检查失败: {e}")

# 测试3: 导入主模块
try:
    from src.data_extraction import CharacterDataExtractor
    print("\n✓ CharacterDataExtractor导入成功")
    
    # 尝试创建实例
    extractor = CharacterDataExtractor()
    print("✓ 提取器实例创建成功")
    
except Exception as e:
    print(f"\n✗ 主模块导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")
