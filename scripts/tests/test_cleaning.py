"""
测试文本清洗功能
"""
import sys
sys.path.append('.')

from src.rag_system.vector_processor import VectorProcessor

# 创建处理器实例
processor = VectorProcessor()

# 测试清洗一个示例文件
test_file = "enhanced_script/孙悟空/01013014_金钱豹_enhanced_script.txt"

print("=" * 60)
print("测试文本清洗功能")
print("=" * 60)

# 读取原始内容
with open(test_file, 'r', encoding='utf-8') as f:
    original_content = f.read()

print(f"\n原始内容长度: {len(original_content)} 字符")
print(f"原始内容前200字符:")
print("-" * 60)
print(original_content[:200])
print("-" * 60)

# 清洗内容
cleaned_content = processor.clean_script_content(original_content)

print(f"\n清洗后内容长度: {len(cleaned_content)} 字符")
print(f"清洗后内容前200字符:")
print("-" * 60)
print(cleaned_content[:200])
print("-" * 60)

print(f"\n减少了 {len(original_content) - len(cleaned_content)} 字符")
print(f"清洗率: {((len(original_content) - len(cleaned_content)) / len(original_content) * 100):.2f}%")

# 检查是否还包含提示词
prompt_keywords = ["好的", "遵照您的指示", "我将严格依据"]
found_prompts = []
for keyword in prompt_keywords:
    if keyword in cleaned_content[:500]:  # 只检查前500字符
        found_prompts.append(keyword)

if found_prompts:
    print(f"\n⚠️  警告: 清洗后的内容前500字符中仍包含提示词: {found_prompts}")
else:
    print(f"\n✓ 成功: 清洗后的内容不包含常见提示词")

print("\n" + "=" * 60)
