"""
RAG系统主入口
提供命令行接口和核心功能集成
"""

import os
import json
import argparse
from pathlib import Path
from typing import Optional, List

from .vector_processor import VectorProcessor
from .vector_store import VectorStoreManager
from .semantic_retriever import SemanticRetriever
from .scene_enhancer import SceneEnhancer
from ..config import Config


class RAGSystem:
    """RAG系统主类，整合所有功能模块"""
    
    def __init__(self, index_path: str = "vector_index"):
        """
        初始化RAG系统
        
        Args:
            index_path: 向量索引保存路径
        """
        self.index_path = index_path
        self.vector_processor = VectorProcessor()
        self.vector_store = VectorStoreManager(index_dir=index_path)
        self.retriever = None
        self.enhancer = SceneEnhancer()
        
    def build_index(self, force_rebuild: bool = False) -> bool:
        """
        构建向量索引
        
        Args:
            force_rebuild: 是否强制重建索引
            
        Returns:
            是否成功构建
        """
        print("=" * 60)
        print("开始构建RAG向量索引...")
        print("=" * 60)
        
        # 检查是否已存在索引
        if os.path.exists(self.index_path) and not force_rebuild:
            print(f"\n索引已存在于 {self.index_path}")
            print("如需重建，请使用 --rebuild 参数")
            return False
        
        try:
            # 处理所有角色数据
            print("\n步骤1: 加载和处理角色数据...")
            vectorized_docs = self.vector_processor.process_all_characters()
            
            if not vectorized_docs:
                print("错误：未找到任何数据")
                return False
            
            print(f"成功处理 {len(vectorized_docs)} 个文档")
            
            # 创建向量索引
            print("\n步骤2: 创建向量索引...")
            self.vector_store.create_index(vectorized_docs)
            
            # 保存索引
            print(f"\n步骤3: 保存索引到 {self.index_path}...")
            self.vector_store.save_index()
            
            # 显示统计信息
            stats = self.vector_store.get_statistics()
            print("\n" + "=" * 60)
            print("索引构建完成！")
            print("=" * 60)
            print(f"总文档数: {stats['total_documents']}")
            print(f"角色数: {stats['character_count']}")
            print(f"角色列表: {', '.join(stats['characters'])}")
            print(f"对话数据: {stats['dialogue_count']}")
            print(f"表演数据: {stats['performance_count']}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n错误：构建索引失败 - {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_index(self) -> bool:
        """
        加载已有的向量索引
        
        Returns:
            是否成功加载
        """
        if not os.path.exists(self.index_path):
            print(f"错误：索引不存在于 {self.index_path}")
            print("请先运行 build 命令构建索引")
            return False
        
        try:
            print(f"加载索引从 {self.index_path}...")
            self.vector_store.load_index()
            self.retriever = SemanticRetriever(self.vector_store)
            
            stats = self.vector_store.get_statistics()
            print(f"成功加载索引：{stats['total_documents']} 个文档")
            return True
            
        except Exception as e:
            print(f"错误：加载索引失败 - {str(e)}")
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        output_file: Optional[str] = None
    ) -> dict:
        """
        执行语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            output_file: 可选的输出文件路径
            
        Returns:
            搜索结果
        """
        if not self.retriever:
            if not self.load_index():
                return {}
        
        print("\n" + "=" * 60)
        print(f"查询: {query}")
        print("=" * 60)
        
        # 执行智能检索
        results = self.retriever.smart_retrieve(
            query=query,
            top_k_per_character=top_k
        )
        
        # 显示结果
        print(f"\n识别到的角色: {', '.join(results['characters']) if results['characters'] else '无'}")
        print(f"提取的关键词: {', '.join(results['keywords']) if results['keywords'] else '无'}")
        print(f"找到 {results['total_results']} 个相关结果\n")
        
        # 显示前几个结果
        for idx, result in enumerate(results['combined_results'][:top_k], 1):
            print(f"\n结果 {idx}:")
            print(f"  剧本: {result.get('title', '未知')}")
            print(f"  角色: {result.get('character', '未知')}")
            print(f"  类型: {result.get('type', '未知')}")
            print(f"  相似度: {result.get('similarity_score', 0):.3f}")
            print(f"  内容预览: {result.get('text', '')[:100]}...")
        
        # 保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n完整结果已保存到: {output_file}")
        
        return results
    
    def enhance_scene(
        self,
        query: str,
        output_file: Optional[str] = None
    ) -> dict:
        """
        增强场景上下文，为剧本生成准备
        
        Args:
            query: 查询文本
            output_file: 可选的输出文件路径
            
        Returns:
            增强后的场景上下文
        """
        if not self.retriever:
            if not self.load_index():
                return {}
        
        print("\n" + "=" * 60)
        print("生成场景增强上下文...")
        print("=" * 60)
        
        # 执行智能检索
        retrieval_results = self.retriever.smart_retrieve(query=query)
        
        # 增强场景上下文
        enhanced_context = self.enhancer.enhance_scene_context(
            query=query,
            retrieval_results=retrieval_results
        )
        
        # 生成上下文提示
        context_prompt = self.enhancer.generate_context_prompt(enhanced_context)
        
        print("\n生成的上下文提示:")
        print("-" * 60)
        print(context_prompt)
        print("-" * 60)
        
        # 保存到文件
        if output_file:
            output_data = {
                "enhanced_context": enhanced_context,
                "context_prompt": context_prompt
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n增强上下文已保存到: {output_file}")
        
        return enhanced_context
    
    def interactive_search(self):
        """交互式搜索模式"""
        if not self.retriever:
            if not self.load_index():
                return
        
        print("\n" + "=" * 60)
        print("RAG交互式搜索模式")
        print("=" * 60)
        print("输入查询内容，输入 'quit' 或 'exit' 退出")
        print("输入 'enhance' 进入场景增强模式")
        print("-" * 60)
        
        while True:
            try:
                query = input("\n请输入查询: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("退出交互模式")
                    break
                
                if query.lower() == 'enhance':
                    try:
                        enhance_query = input("请输入场景描述: ").strip()
                        if enhance_query:
                            self.enhance_scene(enhance_query)
                    except EOFError:
                        print("\n输入结束，退出交互模式")
                        break
                    continue
                
                if not query:
                    continue
                
                self.search(query, top_k=5)
                
            except EOFError:
                # 输入流结束（如管道输入），正常退出
                print("\n输入结束，退出交互模式")
                break
            except KeyboardInterrupt:
                print("\n\n退出交互模式")
                break
            except Exception as e:
                print(f"错误: {str(e)}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="RAG检索系统 - 京剧剧本语义检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 构建索引
  python -m src.rag_system.main build
  
  # 重建索引
  python -m src.rag_system.main build --rebuild
  
  # 搜索
  python -m src.rag_system.main search "诸葛亮和孙悟空的对话"
  
  # 场景增强
  python -m src.rag_system.main enhance "诸葛亮和孙悟空煮酒论英雄"
  
  # 交互式搜索
  python -m src.rag_system.main interactive
        """
    )
    
    parser.add_argument(
        'command',
        choices=['build', 'search', 'enhance', 'interactive'],
        help='执行的命令'
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='查询文本（用于search和enhance命令）'
    )
    
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='强制重建索引（用于build命令）'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='返回结果数量（默认：5）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='输出文件路径'
    )
    
    parser.add_argument(
        '--index-path',
        type=str,
        default='vector_index',
        help='向量索引路径（默认：vector_index）'
    )
    
    args = parser.parse_args()
    
    # 创建RAG系统实例
    rag_system = RAGSystem(index_path=args.index_path)
    
    # 执行命令
    if args.command == 'build':
        rag_system.build_index(force_rebuild=args.rebuild)
    
    elif args.command == 'search':
        if not args.query:
            print("错误：search命令需要提供查询文本")
            parser.print_help()
            return
        rag_system.search(args.query, top_k=args.top_k, output_file=args.output)
    
    elif args.command == 'enhance':
        if not args.query:
            print("错误：enhance命令需要提供查询文本")
            parser.print_help()
            return
        rag_system.enhance_scene(args.query, output_file=args.output)
    
    elif args.command == 'interactive':
        rag_system.interactive_search()


if __name__ == '__main__':
    main()
