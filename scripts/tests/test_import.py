"""测试导入和运行"""
import sys
import traceback

print("=" * 60)
print("测试数据提取模块")
print("=" * 60)

try:
    print("\n1. 测试导入config...")
    from src.config import Config
    print(f"   ✓ Config导入成功")
    print(f"   - API_KEY: {Config.API_KEY[:15]}...")
    print(f"   - 剧本路径: {Config.ENHANCED_SCRIPT_PATH}")
    
    print("\n2. 测试导入data_models...")
    from src.data_extraction.data_models import DataTemplates
    print(f"   ✓ DataTemplates导入成功")
    
    print("\n3. 测试导入llm_client...")
    from src.data_extraction.llm_client import LLMClientManager
    print(f"   ✓ LLMClientManager导入成功")
    
    print("\n4. 测试导入utils...")
    from src.data_extraction.utils import FileManager, CharacterIDManager
    print(f"   ✓ Utils导入成功")
    
    print("\n5. 测试导入extractor...")
    from src.data_extraction.extractor import CharacterDataExtractor
    print(f"   ✓ CharacterDataExtractor导入成功")
    
    print("\n6. 测试创建提取器实例...")
    extractor = CharacterDataExtractor()
    print(f"   ✓ 提取器实例创建成功")
    
    print("\n" + "=" * 60)
    print("所有测试通过！模块可以正常使用")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 错误: {str(e)}")
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1)
