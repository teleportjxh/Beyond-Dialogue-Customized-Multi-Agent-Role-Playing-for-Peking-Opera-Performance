"""
RAG 检索工具 - 封装 RAG 系统为 CrewAI Tool
"""
import json
import os
from typing import Any, Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class RAGSearchInput(BaseModel):
    """RAG搜索工具的输入参数"""
    query: str = Field(..., description="搜索查询文本，如'诸葛亮空城计'")
    character_filter: Optional[str] = Field(None, description="按角色过滤，如'诸葛亮'")
    top_k: int = Field(5, description="返回结果数量")


class RAGSearchTool(BaseTool):
    """RAG语义检索工具 - 从京剧历史剧本库中检索相关场景"""
    name: str = "rag_search"
    description: str = (
        "从京剧历史剧本库中语义检索相关场景和对话。"
        "输入查询文本，返回最相关的历史剧本片段。"
        "可选按角色名过滤结果。"
    )
    args_schema: Type[BaseModel] = RAGSearchInput
    
    # RAG系统实例（在初始化时注入）
    rag_system: Any = None
    
    model_config = {"arbitrary_types_allowed": True}
    
    def _run(self, query: str, character_filter: Optional[str] = None, top_k: int = 5) -> str:
        """执行RAG语义检索"""
        if not self.rag_system:
            return json.dumps({"error": "RAG系统未初始化"}, ensure_ascii=False)
        
        try:
            from src.rag_system import SemanticRetriever
            retriever = SemanticRetriever(self.rag_system.vector_store)
            
            if character_filter:
                # 按角色过滤检索
                results = retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    character_filter=[character_filter]
                )
            else:
                # 智能检索
                smart_results = retriever.smart_retrieve(
                    query=query,
                    top_k_per_character=top_k,
                    min_similarity=0.3
                )
                results = smart_results.get('combined_results', [])
            
            # 格式化结果
            formatted = []
            for r in results[:top_k]:
                formatted.append({
                    'title': r.get('title', '未知'),
                    'character': r.get('character', '未知'),
                    'type': r.get('type', '未知'),
                    'similarity_score': round(r.get('similarity_score', 0), 3),
                    'text': r.get('text', '')[:500]
                })
            
            return json.dumps({
                'query': query,
                'total': len(formatted),
                'results': formatted
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"RAG检索失败: {str(e)}"}, ensure_ascii=False)


class CharacterSceneInput(BaseModel):
    """角色场景检索工具的输入参数"""
    character_name: str = Field(..., description="角色名称，如'孙悟空'")
    top_k: int = Field(5, description="返回结果数量")


class CharacterSceneRetrieveTool(BaseTool):
    """角色场景检索工具 - 检索特定角色的代表性场景"""
    name: str = "character_scene_retrieve"
    description: str = (
        "检索特定角色在历史京剧剧本中的代表性场景。"
        "输入角色名称，返回该角色最具代表性的对话和表演片段。"
    )
    args_schema: Type[BaseModel] = CharacterSceneInput
    
    rag_system: Any = None
    
    model_config = {"arbitrary_types_allowed": True}
    
    def _run(self, character_name: str, top_k: int = 5) -> str:
        """检索角色的代表性场景"""
        if not self.rag_system:
            return json.dumps({"error": "RAG系统未初始化"}, ensure_ascii=False)
        
        try:
            from src.rag_system import SemanticRetriever
            retriever = SemanticRetriever(self.rag_system.vector_store)
            context = retriever.get_character_context(character_name, top_k=top_k)
            
            all_scenes = []
            for scene in context.get('dialogues', [])[:top_k]:
                all_scenes.append({
                    'type': 'dialogue',
                    'title': scene.get('title', '未知'),
                    'text': scene.get('text', '')[:400],
                    'similarity_score': round(scene.get('similarity_score', 0), 3)
                })
            for scene in context.get('performances', [])[:top_k]:
                all_scenes.append({
                    'type': 'performance',
                    'title': scene.get('title', '未知'),
                    'text': scene.get('text', '')[:400],
                    'similarity_score': round(scene.get('similarity_score', 0), 3)
                })
            
            return json.dumps({
                'character': character_name,
                'total': len(all_scenes),
                'scenes': all_scenes[:top_k]
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"角色场景检索失败: {str(e)}"}, ensure_ascii=False)
