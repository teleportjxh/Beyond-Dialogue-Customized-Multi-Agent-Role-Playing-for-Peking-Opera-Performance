"""
上下文构建器 - 为Agent构建所需的上下文信息
整合RAG检索和角色数据，为不同Agent提供专属上下文
"""
import json
import os
from typing import Dict, Any, List, Optional
from src.config import Config


class ContextBuilder:
    """上下文构建器，整合RAG结果和角色数据"""
    
    def __init__(self, rag_system=None):
        """
        初始化上下文构建器
        
        Args:
            rag_system: RAG系统实例（可选）
        """
        self.character_profiles: Dict[str, Dict] = {}
        self.character_data: Dict[str, Dict] = {}
        self.rag_system = rag_system
    
    def set_rag_system(self, rag_system):
        """设置RAG系统"""
        self.rag_system = rag_system
    
    def load_character_profile(self, character_name: str) -> Dict[str, Any]:
        """
        加载角色档案
        
        Args:
            character_name: 角色名称
            
        Returns:
            角色档案数据
        """
        if character_name in self.character_profiles:
            return self.character_profiles[character_name]
        
        profile_path = os.path.join(
            Config.CHARACTER_PATH,
            character_name,
            "profile.json"
        )
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"角色档案不存在: {profile_path}")
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        self.character_profiles[character_name] = profile
        return profile
    
    def load_character_data(self, character_name: str) -> Dict[str, Any]:
        """
        加载角色数据
        
        Args:
            character_name: 角色名称
            
        Returns:
            角色数据
        """
        if character_name in self.character_data:
            return self.character_data[character_name]
        
        data_path = os.path.join(
            Config.CHARACTER_DATA_PATH,
            character_name,
            "data.json"
        )
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"角色数据不存在: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.character_data[character_name] = data
        return data
    
    def extract_characters_from_request(self, user_request: str) -> List[str]:
        """
        从用户需求中提取角色名称
        
        Args:
            user_request: 用户需求
            
        Returns:
            角色名称列表
        """
        characters = []
        
        if os.path.exists(Config.CHARACTER_PATH):
            available_characters = [
                d for d in os.listdir(Config.CHARACTER_PATH)
                if os.path.isdir(os.path.join(Config.CHARACTER_PATH, d))
            ]
            
            for char in available_characters:
                if char in user_request:
                    characters.append(char)
        
        return characters
    
    def retrieve_rag_context(
        self,
        query: str,
        characters: List[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        使用RAG检索相关场景
        
        Args:
            query: 查询文本（如用户需求）
            characters: 角色列表（可选）
            top_k: 返回结果数量
            
        Returns:
            RAG检索结果
        """
        if not self.rag_system:
            return {}
        
        try:
            # 使用RAG系统的语义检索
            from src.rag_system import SemanticRetriever
            
            retriever = SemanticRetriever(self.rag_system.vector_store)
            
            # 智能检索
            smart_results = retriever.smart_retrieve(
                query=query,
                top_k_per_character=top_k,
                min_similarity=0.3
            )
            
            return {
                'query': query,
                'characters': smart_results.get('characters', []),
                'results': smart_results.get('combined_results', []),
                'total': smart_results.get('total_results', 0)
            }
        except Exception as e:
            print(f"  警告：RAG检索失败: {str(e)}")
            return {}
    
    def retrieve_character_scenes(
        self,
        character_name: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索角色的代表性场景
        
        Args:
            character_name: 角色名称
            top_k: 返回结果数量
            
        Returns:
            场景列表
        """
        if not self.rag_system:
            return []
        
        try:
            from src.rag_system import SemanticRetriever
            
            retriever = SemanticRetriever(self.rag_system.vector_store)
            context = retriever.get_character_context(character_name, top_k=top_k)
            
            # 合并对话和表演场景
            all_scenes = []
            all_scenes.extend(context.get('dialogues', []))
            all_scenes.extend(context.get('performances', []))
            
            return all_scenes[:top_k]
        except Exception as e:
            print(f"  警告：角色场景检索失败: {str(e)}")
            return []
    
    def build_costume_designer_context(
        self,
        characters: List[str],
        outline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        为定妆师Agent构建上下文
        
        Args:
            characters: 角色列表
            outline: 剧本大纲
            
        Returns:
            包含角色信息和RAG参考的上下文
        """
        context = {
            'characters_info': {},
            'rag_references': {}
        }
        
        for character in characters:
            # 加载角色档案
            try:
                profile = self.load_character_profile(character)
                context['characters_info'][character] = profile.get('data', {})
            except Exception as e:
                print(f"  警告：加载{character}档案失败: {str(e)}")
                context['characters_info'][character] = {}
            
            # 检索角色的历史装扮场景
            scenes = self.retrieve_character_scenes(character, top_k=3)
            context['rag_references'][character] = scenes
        
        return context
    
    def build_screenwriter_context(
        self,
        user_request: str,
        characters: List[str]
    ) -> str:
        """
        为编剧Agent构建上下文
        
        Args:
            user_request: 用户需求
            characters: 角色列表
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = [
            f"# 剧本创作任务",
            f"\n## 用户需求",
            user_request,
        ]
        
        # 使用RAG检索相关场景
        rag_context = self.retrieve_rag_context(user_request, characters, top_k=5)
        
        if rag_context.get('results'):
            context_parts.append(f"\n## 相关场景参考（共{rag_context.get('total', 0)}个）")
            for i, result in enumerate(rag_context['results'][:3], 1):
                context_parts.append(f"\n### 参考{i}：{result.get('title', '未知')}")
                context_parts.append(f"角色：{result.get('character', '未知')}")
                context_parts.append(f"相似度：{result.get('similarity_score', 0):.2f}")
                text = result.get('text', '')[:500]
                context_parts.append(text)
        
        # 添加角色信息
        context_parts.append(f"\n## 角色信息")
        for char in characters:
            try:
                profile = self.load_character_profile(char)
                context_parts.append(f"\n### {char}")
                context_parts.append(f"性别：{profile['data'].get('gender', '未知')}")
                
                if profile['data'].get('script_data'):
                    first_script = profile['data']['script_data'][0]
                    context_parts.append(f"性格：{first_script.get('personality', '未知')}")
                    context_parts.append(f"职业：{first_script.get('profession', '未知')}")
                    context_parts.append(f"描述：{first_script.get('description', '未知')}")
            except Exception as e:
                context_parts.append(f"\n### {char}")
                context_parts.append(f"信息加载失败：{str(e)}")
        
        return "\n".join(context_parts)
    
    def build_actor_context(
        self,
        character_name: str,
        outline: Dict[str, Any],
        scene_description: str = ""
    ) -> str:
        """
        为演员Agent构建上下文
        
        Args:
            character_name: 角色名称
            outline: 剧本大纲
            scene_description: 当前场景描述
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = [
            f"# 角色扮演任务",
            f"\n## 角色：{character_name}",
        ]
        
        # 加载角色档案
        try:
            profile = self.load_character_profile(character_name)
            context_parts.append(f"\n## 基本信息")
            context_parts.append(f"性别：{profile['data'].get('gender', '未知')}")
            
            if profile['data'].get('script_data'):
                first_script = profile['data']['script_data'][0]
                context_parts.append(f"年龄：{first_script.get('age', '未知')}")
                context_parts.append(f"性格：{first_script.get('personality', '未知')}")
                context_parts.append(f"职业：{first_script.get('profession', '未知')}")
                context_parts.append(f"描述：{first_script.get('description', '未知')}")
        except Exception as e:
            context_parts.append(f"\n基本信息加载失败：{str(e)}")
        
        # 加载角色数据（口头禅、禁忌等）
        try:
            data = self.load_character_data(character_name)
            
            if data.get('catchphrases'):
                context_parts.append(f"\n## 常用语")
                for phrase in data['catchphrases'][:5]:
                    context_parts.append(f"- {phrase}")
            
            if data.get('forbidden'):
                context_parts.append(f"\n## 行为禁忌")
                for forbidden in data['forbidden'][:5]:
                    context_parts.append(f"- {forbidden}")
        except Exception as e:
            context_parts.append(f"\n角色数据加载失败：{str(e)}")
        
        # 使用RAG检索相似场景
        if scene_description:
            query = f"{character_name} {scene_description}"
            rag_context = self.retrieve_rag_context(query, [character_name], top_k=3)
            
            if rag_context.get('results'):
                context_parts.append(f"\n## 相似场景参考")
                for i, result in enumerate(rag_context['results'][:2], 1):
                    context_parts.append(f"\n### 参考{i}：{result.get('title', '未知')}")
                    text = result.get('text', '')[:400]
                    context_parts.append(text)
        
        # 添加剧本信息
        context_parts.append(f"\n## 当前剧本")
        context_parts.append(f"剧名：{outline.get('title', '未命名')}")
        context_parts.append(f"主题：{outline.get('theme', '未知')}")
        
        return "\n".join(context_parts)
    
    def build_director_context(
        self,
        characters: List[str],
        outline: Dict[str, Any]
    ) -> str:
        """
        为导演Agent构建上下文
        
        Args:
            characters: 角色列表
            outline: 剧本大纲
            
        Returns:
            格式化的上下文字符串
        """
        context_parts = [
            "# 剧本评估任务",
            f"\n## 剧本信息",
            f"剧名：{outline.get('title', '未命名')}",
            f"主题：{outline.get('theme', '未知')}",
            f"场景数：{len(outline.get('scenes', []))}",
        ]
        
        # 添加角色信息
        context_parts.append(f"\n## 参与角色")
        for char in characters:
            try:
                profile = self.load_character_profile(char)
                context_parts.append(f"\n### {char}")
                if profile['data'].get('script_data'):
                    first_script = profile['data']['script_data'][0]
                    context_parts.append(f"性格：{first_script.get('personality', '未知')}")
                    context_parts.append(f"职业：{first_script.get('profession', '未知')}")
            except Exception as e:
                context_parts.append(f"\n### {char}")
                context_parts.append(f"信息加载失败：{str(e)}")
        
        # 检索优秀场景作为评估标准
        query = f"{' '.join(characters)} 优秀场景"
        rag_context = self.retrieve_rag_context(query, characters, top_k=3)
        
        if rag_context.get('results'):
            context_parts.append(f"\n## 优秀场景参考（评估标准）")
            for i, result in enumerate(rag_context['results'][:2], 1):
                context_parts.append(f"\n### 参考{i}：{result.get('title', '未知')}")
                context_parts.append(f"相似度：{result.get('similarity_score', 0):.2f}")
                text = result.get('text', '')[:400]
                context_parts.append(text)
        
        return "\n".join(context_parts)
