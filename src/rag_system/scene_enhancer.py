"""
场景增强器模块
整合检索结果，格式化为多agent系统所需的上下文
"""

from typing import List, Dict, Any, Optional
import json


class SceneEnhancer:
    """场景增强器，将检索结果转换为剧本生成所需的上下文"""
    
    def __init__(self):
        """初始化场景增强器"""
        pass
    
    def format_dialogue_context(
        self,
        dialogue_results: List[Dict[str, Any]],
        max_examples: int = 3
    ) -> str:
        """
        格式化对话上下文
        
        Args:
            dialogue_results: 对话检索结果
            max_examples: 最大示例数量
            
        Returns:
            格式化的对话上下文文本
        """
        if not dialogue_results:
            return "暂无相关对话参考。"
        
        context_parts = ["## 相关对话参考\n"]
        
        for idx, result in enumerate(dialogue_results[:max_examples], 1):
            title = result.get("title", "未知剧本")
            character = result.get("character", "未知角色")
            text = result.get("text", "")
            similarity = result.get("similarity_score", 0)
            
            context_parts.append(f"\n### 参考{idx}：《{title}》（相似度：{similarity:.2f}）")
            context_parts.append(f"角色：{character}")
            context_parts.append(f"内容：\n{text}\n")
        
        return "\n".join(context_parts)
    
    def format_performance_context(
        self,
        performance_results: List[Dict[str, Any]],
        max_examples: int = 3
    ) -> str:
        """
        格式化表演上下文
        
        Args:
            performance_results: 表演检索结果
            max_examples: 最大示例数量
            
        Returns:
            格式化的表演上下文文本
        """
        if not performance_results:
            return "暂无相关表演参考。"
        
        context_parts = ["## 相关表演参考\n"]
        
        for idx, result in enumerate(performance_results[:max_examples], 1):
            title = result.get("title", "未知剧本")
            character = result.get("character", "未知角色")
            text = result.get("text", "")
            similarity = result.get("similarity_score", 0)
            
            context_parts.append(f"\n### 参考{idx}：《{title}》（相似度：{similarity:.2f}）")
            context_parts.append(f"角色：{character}")
            context_parts.append(f"表演：\n{text}\n")
        
        return "\n".join(context_parts)
    
    def format_character_context(
        self,
        character: str,
        character_results: List[Dict[str, Any]],
        max_examples: int = 5
    ) -> str:
        """
        格式化角色上下文
        
        Args:
            character: 角色名称
            character_results: 角色相关检索结果
            max_examples: 最大示例数量
            
        Returns:
            格式化的角色上下文文本
        """
        if not character_results:
            return f"暂无{character}的相关参考。"
        
        # 分类结果
        dialogues = [r for r in character_results if r.get("type") == "dialogue"]
        performances = [r for r in character_results if r.get("type") == "performance"]
        
        context_parts = [f"## {character}角色参考\n"]
        
        # 添加对话示例
        if dialogues:
            context_parts.append("\n### 经典对话")
            for idx, result in enumerate(dialogues[:max_examples], 1):
                title = result.get("title", "未知剧本")
                text = result.get("text", "")[:200]  # 截取前200字
                context_parts.append(f"{idx}. 《{title}》：{text}...")
        
        # 添加表演示例
        if performances:
            context_parts.append("\n### 经典表演")
            for idx, result in enumerate(performances[:max_examples], 1):
                title = result.get("title", "未知剧本")
                text = result.get("text", "")[:200]
                context_parts.append(f"{idx}. 《{title}》：{text}...")
        
        return "\n".join(context_parts)
    
    def enhance_scene_context(
        self,
        query: str,
        retrieval_results: Dict[str, Any],
        max_examples_per_type: int = 3
    ) -> Dict[str, Any]:
        """
        增强场景上下文，为多agent系统准备完整的上下文信息
        
        Args:
            query: 原始查询
            retrieval_results: 检索结果（来自smart_retrieve）
            max_examples_per_type: 每种类型的最大示例数
            
        Returns:
            增强后的场景上下文
        """
        characters = retrieval_results.get("characters", [])
        combined_results = retrieval_results.get("combined_results", [])
        
        # 分类所有结果
        all_dialogues = [r for r in combined_results if r.get("type") == "dialogue"]
        all_performances = [r for r in combined_results if r.get("type") == "performance"]
        
        # 按角色分组
        character_contexts = {}
        for character in characters:
            char_results = [
                r for r in combined_results 
                if r.get("character") == character
            ]
            character_contexts[character] = self.format_character_context(
                character,
                char_results,
                max_examples=max_examples_per_type
            )
        
        # 格式化整体上下文
        dialogue_context = self.format_dialogue_context(
            all_dialogues,
            max_examples=max_examples_per_type
        )
        
        performance_context = self.format_performance_context(
            all_performances,
            max_examples=max_examples_per_type
        )
        
        # 构建完整的增强上下文
        enhanced_context = {
            "query": query,
            "characters": characters,
            "character_contexts": character_contexts,
            "dialogue_context": dialogue_context,
            "performance_context": performance_context,
            "total_references": len(combined_results),
            "raw_results": combined_results
        }
        
        return enhanced_context
    
    def generate_context_prompt(
        self,
        enhanced_context: Dict[str, Any],
        include_raw_data: bool = False
    ) -> str:
        """
        生成用于多agent系统的上下文提示
        
        Args:
            enhanced_context: 增强后的场景上下文
            include_raw_data: 是否包含原始数据
            
        Returns:
            格式化的上下文提示文本
        """
        prompt_parts = []
        
        # 添加查询信息
        query = enhanced_context.get("query", "")
        characters = enhanced_context.get("characters", [])
        
        prompt_parts.append("# 剧本生成上下文\n")
        prompt_parts.append(f"## 用户需求\n{query}\n")
        prompt_parts.append(f"## 涉及角色\n{', '.join(characters)}\n")
        
        # 添加角色上下文
        character_contexts = enhanced_context.get("character_contexts", {})
        if character_contexts:
            prompt_parts.append("\n# 角色背景参考\n")
            for character, context in character_contexts.items():
                prompt_parts.append(context)
                prompt_parts.append("")
        
        # 添加对话上下文
        dialogue_context = enhanced_context.get("dialogue_context", "")
        if dialogue_context and dialogue_context != "暂无相关对话参考。":
            prompt_parts.append(f"\n{dialogue_context}\n")
        
        # 添加表演上下文
        performance_context = enhanced_context.get("performance_context", "")
        if performance_context and performance_context != "暂无相关表演参考。":
            prompt_parts.append(f"\n{performance_context}\n")
        
        # 添加原始数据（可选）
        if include_raw_data:
            raw_results = enhanced_context.get("raw_results", [])
            prompt_parts.append("\n## 原始检索数据\n")
            prompt_parts.append(f"```json\n{json.dumps(raw_results, ensure_ascii=False, indent=2)}\n```\n")
        
        # 添加使用说明
        prompt_parts.append("\n## 使用说明")
        prompt_parts.append("请基于以上参考内容，保持京剧艺术风格，生成符合角色特点的新剧本。")
        prompt_parts.append("注意：")
        prompt_parts.append("1. 保持角色的语言风格和性格特点")
        prompt_parts.append("2. 融入京剧的表演形式（唱、念、做、打）")
        prompt_parts.append("3. 参考但不照搬原有剧本内容")
        prompt_parts.append("4. 创造性地结合用户需求和传统元素\n")
        
        return "\n".join(prompt_parts)
    
    def extract_key_elements(
        self,
        enhanced_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提取关键元素，用于agent系统的决策
        
        Args:
            enhanced_context: 增强后的场景上下文
            
        Returns:
            关键元素字典
        """
        raw_results = enhanced_context.get("raw_results", [])
        
        # 提取高频词汇
        all_texts = [r.get("text", "") for r in raw_results]
        combined_text = " ".join(all_texts)
        
        # 提取剧本标题
        titles = list(set([r.get("title", "") for r in raw_results]))
        
        # 统计对话和表演数量
        dialogue_count = len([r for r in raw_results if r.get("type") == "dialogue"])
        performance_count = len([r for r in raw_results if r.get("type") == "performance"])
        
        # 计算平均相似度
        similarities = [r.get("similarity_score", 0) for r in raw_results]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        return {
            "referenced_scripts": titles,
            "dialogue_count": dialogue_count,
            "performance_count": performance_count,
            "average_similarity": avg_similarity,
            "total_references": len(raw_results),
            "characters": enhanced_context.get("characters", []),
            "text_length": len(combined_text)
        }
    
    def format_for_agent(
        self,
        character: str,
        enhanced_context: Dict[str, Any]
    ) -> str:
        """
        为特定角色的agent格式化上下文
        
        Args:
            character: 角色名称
            enhanced_context: 增强后的场景上下文
            
        Returns:
            该角色agent的专属上下文
        """
        # 获取该角色的专属上下文
        character_context = enhanced_context.get("character_contexts", {}).get(character, "")
        
        # 获取该角色相关的结果
        raw_results = enhanced_context.get("raw_results", [])
        character_results = [
            r for r in raw_results 
            if r.get("character") == character
        ]
        
        prompt_parts = []
        prompt_parts.append(f"# {character}角色扮演指南\n")
        prompt_parts.append(f"## 你的角色\n你将扮演：{character}\n")
        prompt_parts.append(f"## 场景需求\n{enhanced_context.get('query', '')}\n")
        prompt_parts.append(f"\n{character_context}\n")
        
        # 添加该角色的具体示例
        if character_results:
            prompt_parts.append(f"\n## {character}的表演风格参考\n")
            for idx, result in enumerate(character_results[:3], 1):
                title = result.get("title", "")
                text = result.get("text", "")
                prompt_parts.append(f"\n### 示例{idx}：《{title}》\n{text}\n")
        
        prompt_parts.append("\n## 表演要求")
        prompt_parts.append(f"1. 严格按照{character}的性格特点和语言风格表演")
        prompt_parts.append("2. 注意与其他角色的互动和配合")
        prompt_parts.append("3. 融入京剧的表演技巧")
        prompt_parts.append("4. 保持角色的连贯性和真实性\n")
        
        return "\n".join(prompt_parts)
