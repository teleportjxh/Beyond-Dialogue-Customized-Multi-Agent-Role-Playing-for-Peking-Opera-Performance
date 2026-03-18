"""
语义检索器模块
提供高级语义检索接口，支持多角色联合检索和查询意图理解
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import OpenAIEmbeddings

from .vector_store import VectorStoreManager
from ..config import Config


class SemanticRetriever:
    """语义检索器，提供智能检索功能"""
    
    def __init__(self, vector_store: VectorStoreManager):
        """
        初始化语义检索器
        
        Args:
            vector_store: 向量数据库管理器实例
        """
        self.vector_store = vector_store
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=Config.API_KEY,
            openai_api_base=Config.BASE_URL
        )
    
    def extract_characters_from_query(self, query: str) -> List[str]:
        """
        从查询中提取角色名称
        
        Args:
            query: 用户查询文本
            
        Returns:
            提取到的角色名称列表
        """
        # 获取所有可用角色
        stats = self.vector_store.get_statistics()
        available_characters = stats.get("characters", [])
        
        # 在查询中查找角色名
        found_characters = []
        for character in available_characters:
            if character in query:
                found_characters.append(character)
        
        return found_characters
    
    def extract_scene_keywords(self, query: str) -> List[str]:
        """
        从查询中提取场景关键词
        
        Args:
            query: 用户查询文本
            
        Returns:
            场景关键词列表
        """
        # 移除角色名后的剩余文本
        characters = self.extract_characters_from_query(query)
        remaining_text = query
        for char in characters:
            remaining_text = remaining_text.replace(char, "")
        
        # 提取关键动作和场景词
        keywords = []
        
        # 常见场景动作词
        action_patterns = [
            r'(战斗|对战|交战|大战)',
            r'(对话|交谈|论|说)',
            r'(相遇|见面|会面)',
            r'(计谋|智斗|斗智)',
            r'(救|帮助|援助)',
            r'(追|逃|躲)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, remaining_text)
            keywords.extend(matches)
        
        return keywords
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        character_filter: Optional[List[str]] = None,
        type_filter: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        基础语义检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            character_filter: 角色过滤列表
            type_filter: 类型过滤（dialogue/performance）
            min_similarity: 最小相似度阈值
            
        Returns:
            检索结果列表
        """
        # 向量化查询
        query_vector = self.embeddings.embed_query(query)
        
        # 执行搜索
        if character_filter:
            results_dict = self.vector_store.search_by_character(
                query_vector=query_vector,
                character_names=character_filter,
                top_k=top_k
            )
            # search_by_character返回字典，需要展平为列表
            results = []
            for char_results in results_dict.values():
                results.extend(char_results)
        elif type_filter:
            results = self.vector_store.search_by_type(
                query_vector,
                doc_type=type_filter,
                top_k=top_k
            )
        else:
            results = self.vector_store.search(query_vector, top_k=top_k)
        
        # 过滤低相似度结果
        filtered_results = [
            r for r in results 
            if r.get("similarity_score", 0) >= min_similarity
        ]
        
        return filtered_results
    
    def smart_retrieve(
        self,
        query: str,
        top_k_per_character: int = 3,
        min_similarity: float = 0.3
    ) -> Dict[str, Any]:
        """
        智能检索：自动识别查询意图并返回结构化结果
        
        Args:
            query: 用户查询文本
            top_k_per_character: 每个角色返回的结果数
            min_similarity: 最小相似度阈值
            
        Returns:
            结构化检索结果，包含：
            - characters: 识别到的角色列表
            - keywords: 提取的关键词
            - results_by_character: 按角色分组的检索结果
            - combined_results: 综合排序的结果
        """
        # 提取角色和关键词
        characters = self.extract_characters_from_query(query)
        keywords = self.extract_scene_keywords(query)
        
        # 按角色检索
        results_by_character = {}
        all_results = []
        
        if characters:
            # 有明确角色时，分别检索每个角色
            for character in characters:
                char_results = self.retrieve(
                    query=query,
                    top_k=top_k_per_character,
                    character_filter=[character],
                    min_similarity=min_similarity
                )
                results_by_character[character] = char_results
                all_results.extend(char_results)
        else:
            # 无明确角色时，全局检索
            all_results = self.retrieve(
                query=query,
                top_k=top_k_per_character * 2,
                min_similarity=min_similarity
            )
        
        # 按相似度排序综合结果
        combined_results = sorted(
            all_results,
            key=lambda x: x.get("similarity_score", 0),
            reverse=True
        )
        
        # 去重（基于文档ID）
        seen_ids = set()
        unique_results = []
        for result in combined_results:
            doc_id = result.get("id")
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(result)
        
        return {
            "query": query,
            "characters": characters,
            "keywords": keywords,
            "results_by_character": results_by_character,
            "combined_results": unique_results[:top_k_per_character * len(characters) if characters else top_k_per_character * 2],
            "total_results": len(unique_results)
        }
    
    def retrieve_multi_character_scenes(
        self,
        characters: List[str],
        scene_description: str,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        检索多角色相关场景
        
        Args:
            characters: 角色列表
            scene_description: 场景描述
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值
            
        Returns:
            检索结果列表
        """
        # 构建查询文本
        query = f"{' '.join(characters)} {scene_description}"
        
        # 执行智能检索
        smart_results = self.smart_retrieve(
            query=query,
            top_k_per_character=top_k,
            min_similarity=min_similarity
        )
        
        return smart_results["combined_results"]
    
    def retrieve_similar_dialogues(
        self,
        reference_text: str,
        character: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相似对话
        
        Args:
            reference_text: 参考文本
            character: 可选的角色过滤
            top_k: 返回结果数量
            
        Returns:
            相似对话列表
        """
        return self.retrieve(
            query=reference_text,
            top_k=top_k,
            character_filter=[character] if character else None,
            type_filter="dialogue"
        )
    
    def retrieve_similar_performances(
        self,
        reference_text: str,
        character: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相似表演
        
        Args:
            reference_text: 参考文本
            character: 可选的角色过滤
            top_k: 返回结果数量
            
        Returns:
            相似表演列表
        """
        return self.retrieve(
            query=reference_text,
            top_k=top_k,
            character_filter=[character] if character else None,
            type_filter="performance"
        )
    
    def get_character_context(
        self,
        character: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        获取角色的代表性上下文
        
        Args:
            character: 角色名称
            top_k: 返回结果数量
            
        Returns:
            角色上下文信息
        """
        # 使用角色名作为查询
        query = f"{character}的经典场景和对话"
        
        results = self.retrieve(
            query=query,
            top_k=top_k,
            character_filter=[character]
        )
        
        # 分类结果
        dialogues = [r for r in results if r.get("type") == "dialogue"]
        performances = [r for r in results if r.get("type") == "performance"]
        
        return {
            "character": character,
            "total_scenes": len(results),
            "dialogues": dialogues,
            "performances": performances,
            "representative_texts": [r.get("text", "")[:200] for r in results[:3]]
        }
