"""
RAG 长期记忆
基于向量检索的长期知识存储，利用现有的 FAISS 向量索引
"""
import json
import os
from typing import List, Dict, Any, Optional


class RAGLongTermMemory:
    """
    基于RAG的长期记忆系统
    
    - 利用现有的 FAISS 向量索引作为知识库
    - 支持语义检索历史剧本知识
    - 支持存储新的经验和知识
    """
    
    def __init__(self, vector_index_path: str = "./vector_index"):
        """
        Args:
            vector_index_path: 向量索引目录路径
        """
        self.vector_index_path = vector_index_path
        self.vector_store = None
        self.documents = []
        self._load_index()
    
    def _load_index(self):
        """加载向量索引"""
        try:
            docs_path = os.path.join(self.vector_index_path, "documents.json")
            index_path = os.path.join(self.vector_index_path, "faiss.index")
            
            if os.path.exists(docs_path):
                with open(docs_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            
            if os.path.exists(index_path):
                try:
                    import faiss
                    self.vector_store = faiss.read_index(index_path)
                except ImportError:
                    print("[长期记忆] faiss 未安装，使用文本匹配模式")
                    self.vector_store = None
                    
        except Exception as e:
            print(f"[长期记忆] 加载索引失败: {e}")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        语义检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            相关文档列表
        """
        if self.vector_store is not None:
            return self._vector_retrieve(query, top_k)
        else:
            return self._text_retrieve(query, top_k)
    
    def _vector_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """使用向量检索"""
        try:
            import numpy as np
            from openai import OpenAI
            from src.config import Config
            
            client = OpenAI(api_key=Config.API_KEY, base_url=Config.BASE_URL)
            
            # 生成查询向量
            response = client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_vector = np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)
            
            # FAISS 检索
            distances, indices = self.vector_store.search(query_vector, top_k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents) and idx >= 0:
                    doc = self.documents[idx].copy()
                    doc['similarity_score'] = float(1 / (1 + distances[0][i]))
                    results.append(doc)
            
            return results
            
        except Exception as e:
            print(f"[长期记忆] 向量检索失败: {e}")
            return self._text_retrieve(query, top_k)
    
    def _text_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """使用简单文本匹配作为后备"""
        results = []
        
        for doc in self.documents:
            text = doc.get('text', '')
            # 简单关键词匹配评分
            score = sum(1 for char in query if char in text) / max(len(query), 1)
            if score > 0.3:
                doc_copy = doc.copy()
                doc_copy['similarity_score'] = score
                results.append(doc_copy)
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:top_k]
    
    def get_character_knowledge(self, character_name: str, top_k: int = 5) -> str:
        """
        获取特定角色的知识摘要
        
        Args:
            character_name: 角色名称
            top_k: 返回结果数量
            
        Returns:
            角色知识的文本摘要
        """
        # 从文档中过滤该角色的内容
        char_docs = [
            doc for doc in self.documents
            if doc.get('character', '') == character_name
        ]
        
        if not char_docs:
            return f"未找到{character_name}的历史知识"
        
        # 取前top_k个文档
        selected = char_docs[:top_k]
        
        parts = [f"## {character_name}的历史京剧知识\n"]
        for doc in selected:
            title = doc.get('title', '未知')
            text = doc.get('text', '')[:300]
            doc_type = doc.get('type', '未知')
            parts.append(f"- 【{title}】({doc_type}): {text}")
        
        return "\n".join(parts)
    
    def store(self, content: str, metadata: Optional[Dict] = None):
        """
        存储新的知识到长期记忆
        
        Args:
            content: 知识内容
            metadata: 元数据
        """
        doc = {
            'text': content,
            'type': 'experience',
            **(metadata or {})
        }
        self.documents.append(doc)
        
        # 注意：这里不更新FAISS索引，仅在内存中添加
        # 如需持久化，需要重建索引
    
    def get_stats(self) -> Dict:
        """获取长期记忆统计"""
        return {
            'total_documents': len(self.documents),
            'has_vector_store': self.vector_store is not None,
            'index_path': self.vector_index_path
        }
