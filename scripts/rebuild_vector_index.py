"""重建向量索引 - 使用新的多级语义切分策略"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.rag_system.vector_processor import VectorProcessor

if __name__ == "__main__":
    print("=" * 60)
    print("重建向量索引 - 多级语义切分")
    print("=" * 60)
    
    processor = VectorProcessor()
    
    # 先只做切分，不生成embedding，看看效果
    docs = processor.process_all()
    
    if not docs:
        print("没有文档可处理！")
        sys.exit(1)
    
    # 统计
    type_counts = {}
    char_counts = {}
    lengths = []
    for d in docs:
        t = d["metadata"]["type"]
        c = d["metadata"]["character_name"]
        type_counts[t] = type_counts.get(t, 0) + 1
        char_counts[c] = char_counts.get(c, 0) + 1
        lengths.append(len(d["text"]))
    
    print(f"\n切分结果统计:")
    print(f"  总文档数: {len(docs)}")
    print(f"  类型分布: {type_counts}")
    print(f"  角色分布: {char_counts}")
    print(f"  文本长度: min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)//len(lengths)}, median={sorted(lengths)[len(lengths)//2]}")
    
    # 显示前20个文档
    print(f"\n前20个文档:")
    for i, d in enumerate(docs[:20]):
        m = d["metadata"]
        print(f"  doc_{i}: char={m['character_name']}, type={m['type']}, script={m['script_name']}, scene={m.get('scene_name','')}, len={len(d['text'])}")
    
    # 询问是否继续构建向量
    print(f"\n准备为 {len(docs)} 个文档生成向量并构建索引...")
    print("开始构建向量索引...")
    stats = processor.build_vector_index("vector_index")
    print(f"\n完成! 统计: {stats}")
