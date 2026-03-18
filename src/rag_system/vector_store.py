"""
向量数据库管理器 - 使用FAISS管理向量索引
"""
import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
from ..config import Config


class VectorStoreManager:
    """向量数据库管理器类"""
    
    def __init__(self, index_dir: str = "./vector_index"):
        """
        初始化向量数据库管理器
        
        Args:
            index_dir: 索引文件存储目录
        """
        self.index_dir = index_dir
        self.index_file = os.path.join(index_dir, "faiss.index")
        self.metadata_file = os.path.join(index_dir, "metadata.pkl")
        self.documents_file = os.path.join(index_dir, "documents.json")
        
        self.index = None
        self.documents = []
        self.dimension = 1536  # text-embedding-3-small的维度
        
        # 确保目录存在
        os.makedirs(index_dir, exist_ok=True)
    
    def create_index(self, documents: List[Dict[str, Any]]) -> bool:
        """
        创建FAISS索引
        
        Args:
            documents: 包含向量的文档列表
            
        Returns:
            是否创建成功
        """
        if not documents:
            print("错误: 没有文档可以创建索引")
            return False
        
        print(f"\n创建FAISS索引，文档数量: {len(documents)}")
        
        try:
            # 提取向量
            vectors = []
            for doc in documents:
                if "embedding" in doc and doc["embedding"]:
                    vectors.append(doc["embedding"])
                else:
                    print(f"警告: 文档 {doc.get('id', 'unknown')} 缺少向量")
            
            if not vectors:
                print("错误: 没有有效的向量数据")
                return False
            
            # 转换为numpy数组
            vectors_array = np.array(vectors, dtype=np.float32)
            
            # 创建FAISS索引 (使用L2距离)
            self.index = faiss.IndexFlatL2(self.dimension)
            
            # 添加向量到索引
            self.index.add(vectors_array)
            
            # 保存文档（不包含向量，节省空间）
            self.documents = []
            for doc in documents:
                doc_copy = doc.copy()
                if "embedding" in doc_copy:
                    del doc_copy["embedding"]  # 删除向量，只保留元数据
                self.documents.append(doc_copy)
            
            print(f"索引创建成功，包含 {self.index.ntotal} 个向量")
            return True
            
        except Exception as e:
            print(f"创建索引失败: {str(e)}")
            return False
    
    def save_index(self) -> bool:
        """
        保存索引到磁盘
        
        Returns:
            是否保存成功
        """
        if self.index is None:
            print("错误: 索引未创建，无法保存")
            return False
        
        try:
            # 保存FAISS索引
            faiss.write_index(self.index, self.index_file)
            print(f"FAISS索引已保存到: {self.index_file}")
            
            # 保存文档元数据
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            print(f"文档元数据已保存到: {self.documents_file}")
            
            return True
            
        except Exception as e:
            print(f"保存索引失败: {str(e)}")
            return False
    
    def load_index(self) -> bool:
        """
        从磁盘加载索引
        
        Returns:
            是否加载成功
        """
        if not os.path.exists(self.index_file):
            print(f"索引文件不存在: {self.index_file}")
            return False
        
        if not os.path.exists(self.documents_file):
            print(f"文档文件不存在: {self.documents_file}")
            return False
        
        try:
            # 加载FAISS索引
            self.index = faiss.read_index(self.index_file)
            print(f"FAISS索引已加载，包含 {self.index.ntotal} 个向量")
            
            # 加载文档元数据
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            print(f"文档元数据已加载，共 {len(self.documents)} 个文档")
            
            return True
            
        except Exception as e:
            print(f"加载索引失败: {str(e)}")
            return False
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索最相似的文档
        
        Args:
            query_vector: 查询向量
            top_k: 返回前k个结果
            
        Returns:
            相似文档列表，包含文档和相似度分数
        """
        if self.index is None:
            print("错误: 索引未加载")
            return []
        
        try:
            # 转换查询向量
            query_array = np.array([query_vector], dtype=np.float32)
            
            # 搜索
            distances, indices = self.index.search(query_array, top_k)
            
            # 构建结果
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    # 将L2距离转换为相似度分数 (距离越小，相似度越高)
                    doc["similarity_score"] = float(1 / (1 + dist))
                    doc["distance"] = float(dist)
                    doc["rank"] = i + 1
                    results.append(doc)
            
            return results
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []
    
    def search_by_character(self, query_vector: List[float], character_names: List[str], 
                           top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        按角色搜索相似文档
        
        Args:
            query_vector: 查询向量
            character_names: 角色名称列表
            top_k: 每个角色返回前k个结果
            
        Returns:
            按角色分组的搜索结果
        """
        # 先搜索更多结果
        all_results = self.search(query_vector, top_k * len(character_names) * 2)
        
        # 按角色分组
        results_by_character = {name: [] for name in character_names}
        
        for result in all_results:
            char = result.get("character", "")
            if char in results_by_character and len(results_by_character[char]) < top_k:
                results_by_character[char].append(result)
        
        return results_by_character
    
    def search_by_type(self, query_vector: List[float], doc_type: str, 
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """
        按文档类型搜索
        
        Args:
            query_vector: 查询向量
            doc_type: 文档类型 (dialogue/performance)
            top_k: 返回前k个结果
            
        Returns:
            指定类型的相似文档列表
        """
        # 搜索更多结果以便过滤
        all_results = self.search(query_vector, top_k * 3)
        
        # 过滤指定类型
        filtered_results = [r for r in all_results if r.get("type") == doc_type]
        
        return filtered_results[:top_k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        if self.index is None or not self.documents:
            return {
                "total_documents": 0,
                "index_loaded": False
            }
        
        # 统计各类信息
        characters = set()
        doc_types = {}
        scripts = set()
        
        for doc in self.documents:
            characters.add(doc.get("character", ""))
            doc_type = doc.get("type", "")
            if doc_type:
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # 兼容旧格式的title字段和新格式的script_name字段
            script_name = doc.get("title", "") or doc.get("script_name", "")
            if script_name:
                scripts.add(script_name)
        
        stats = {
            "total_documents": len(self.documents),
            "total_vectors": self.index.ntotal,
            "characters": list(characters),
            "character_count": len(characters),
            "script_count": len(scripts),
            "index_loaded": True
        }
        
        # 添加文档类型统计
        for doc_type, count in doc_types.items():
            stats[f"{doc_type}_count"] = count
        
        # 为了向后兼容，保留dialogue_count和performance_count字段
        stats["dialogue_count"] = doc_types.get("dialogue", 0)
        stats["performance_count"] = doc_types.get("performance", 0)
        
        return stats
    
    def rebuild_index(self, documents: List[Dict[str, Any]]) -> bool:
        """
        重建索引（删除旧索引并创建新索引）
        
        Args:
            documents: 新的文档列表
            
        Returns:
            是否重建成功
        """
        print("\n重建索引...")
        
        # 删除旧索引文件
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.documents_file):
            os.remove(self.documents_file)
        
        # 创建新索引
        success = self.create_index(documents)
        
        if success:
            # 保存新索引
            success = self.save_index()
        
        return success
