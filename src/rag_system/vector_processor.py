"""
向量化处理器 - 负责从enhanced_script文本文件中提取数据并转换为向量表示
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from ..config import Config


class VectorProcessor:
    """向量化处理器类 - 直接从enhanced_script提取数据"""
    
    def __init__(self):
        """初始化向量处理器"""
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=Config.API_KEY,
            openai_api_base=Config.BASE_URL
        )
        self.enhanced_script_path = Config.ENHANCED_SCRIPT_PATH
        
    def clean_script_content(self, content: str) -> str:
        """
        清洗剧本内容，移除AI生成时的提示词和无关内容
        
        Args:
            content: 原始剧本内容
            
        Returns:
            清洗后的剧本内容
        """
        # 移除文件开头的AI提示词
        # 常见模式：以"好的"、"遵照"等开头的提示词
        prompt_patterns = [
            r'^好的[，,].*?(?=###|\*\*\*|剧目：|剧情大纲)',
            r'^遵照.*?(?=###|\*\*\*|剧目：|剧情大纲)',
            r'^根据.*?(?=###|\*\*\*|剧目：|剧情大纲)',
            r'^按照.*?(?=###|\*\*\*|剧目：|剧情大纲)',
        ]
        
        for pattern in prompt_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)
        
        # 移除分隔符行（如 *** 或 --- 等）
        content = re.sub(r'^\s*[\*\-=]{3,}\s*$', '', content, flags=re.MULTILINE)
        
        # 查找剧本真正的开始位置
        # 优先从"### **剧目："或"#### **剧情大纲**"开始
        start_markers = [
            r'###\s*\*\*剧目[：:]',
            r'####\s*\*\*剧情大纲\*\*',
            r'###\s*剧目[：:]',
            r'##\s*剧情大纲',
        ]
        
        start_pos = -1
        for marker in start_markers:
            match = re.search(marker, content)
            if match:
                start_pos = match.start()
                break
        
        # 如果找到标记，从该位置开始截取
        if start_pos > 0:
            content = content[start_pos:]
        
        # 移除多余的空行（连续3个以上空行压缩为2个）
        content = re.sub(r'\n{4,}', '\n\n\n', content)
        
        # 移除首尾空白
        content = content.strip()
        
        return content
    
    def parse_script_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析单个剧本文件
        
        Args:
            file_path: 剧本文件路径
            
        Returns:
            包含剧本结构化数据的字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清洗剧本内容
            content = self.clean_script_content(content)
            
            # 从文件路径提取元数据
            path_obj = Path(file_path)
            character_name = path_obj.parent.name
            filename = path_obj.stem
            
            # 从文件名提取剧本ID和名称
            # 格式: 01019004_舌战群儒_enhanced_script
            filename = filename.replace('_enhanced_script', '')
            parts = filename.split('_', 1)
            script_id = parts[0] if len(parts) > 0 else "unknown"
            script_name = parts[1] if len(parts) > 1 else "unknown"
            
            return {
                'character_name': character_name,
                'script_id': script_id,
                'script_name': script_name,
                'content': content,
                'file_path': file_path
            }
            
        except Exception as e:
            print(f"解析文件 {file_path} 失败: {str(e)}")
            return None
    
    def extract_scenes(self, script_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从剧本中提取场景分段
        
        Args:
            script_data: 剧本数据字典
            
        Returns:
            场景列表，每个场景包含文本和元数据
        """
        content = script_data['content']
        character_name = script_data['character_name']
        script_id = script_data['script_id']
        script_name = script_data['script_name']
        
        scenes = []
        
        # 使用正则表达式分割场景
        scene_pattern = r'【第[一二三四五六七八九十百]+[场幕]】'
        scene_splits = re.split(f'({scene_pattern})', content)
        
        # 提取剧情大纲（在第一个场景之前的内容）
        if len(scene_splits) > 0 and not re.match(scene_pattern, scene_splits[0]):
            outline = scene_splits[0].strip()
            if outline and len(outline) > 50:
                scenes.append({
                    'text': outline,
                    'metadata': {
                        'character_name': character_name,
                        'script_id': script_id,
                        'script_name': script_name,
                        'scene_number': 0,
                        'scene_name': '剧情大纲',
                        'type': 'outline'
                    }
                })
        
        # 处理各个场景
        current_scene_name = None
        current_scene_content = []
        scene_number = 0
        
        for i, part in enumerate(scene_splits[1:], 1):
            if re.match(scene_pattern, part):
                # 保存上一个场景
                if current_scene_name and current_scene_content:
                    scene_text = '\n'.join(current_scene_content).strip()
                    if scene_text:
                        scenes.append({
                            'text': scene_text,
                            'metadata': {
                                'character_name': character_name,
                                'script_id': script_id,
                                'script_name': script_name,
                                'scene_number': scene_number,
                                'scene_name': current_scene_name,
                                'type': 'scene'
                            }
                        })
                
                # 开始新场景
                current_scene_name = part.strip('【】')
                current_scene_content = [part]
                scene_number += 1
            else:
                # 累积场景内容
                if part.strip():
                    current_scene_content.append(part)
        
        # 保存最后一个场景
        if current_scene_name and current_scene_content:
            scene_text = '\n'.join(current_scene_content).strip()
            if scene_text:
                scenes.append({
                    'text': scene_text,
                    'metadata': {
                        'character_name': character_name,
                        'script_id': script_id,
                        'script_name': script_name,
                        'scene_number': scene_number,
                        'scene_name': current_scene_name,
                        'type': 'scene'
                    }
                })
        
        # 如果没有找到场景分段，将整个剧本作为一个单元
        if len(scenes) == 0:
            scenes.append({
                'text': content.strip(),
                'metadata': {
                    'character_name': character_name,
                    'script_id': script_id,
                    'script_name': script_name,
                    'scene_number': 1,
                    'scene_name': '完整剧本',
                    'type': 'full_script'
                }
            })
        
        return scenes
    
    def process_enhanced_scripts(self) -> List[Dict[str, Any]]:
        """
        处理enhanced_script目录下的所有剧本文件
        
        Returns:
            所有场景的文档列表
        """
        all_documents = []
        script_dir = Path(self.enhanced_script_path)
        
        if not script_dir.exists():
            print(f"错误: 目录不存在: {self.enhanced_script_path}")
            return all_documents
        
        # 遍历所有角色目录
        character_dirs = [d for d in script_dir.iterdir() if d.is_dir()]
        print(f"找到 {len(character_dirs)} 个角色目录")
        
        doc_id = 0
        for character_dir in character_dirs:
            character_name = character_dir.name
            print(f"\n处理角色: {character_name}")
            
            # 遍历该角色的所有剧本文件
            script_files = list(character_dir.glob("*_enhanced_script.txt"))
            print(f"  找到 {len(script_files)} 个剧本文件")
            
            for script_file in script_files:
                # 解析剧本文件
                script_data = self.parse_script_file(str(script_file))
                if script_data is None:
                    continue
                
                # 提取场景
                scenes = self.extract_scenes(script_data)
                print(f"    {script_data['script_name']}: 提取 {len(scenes)} 个场景")
                
                # 转换为文档格式
                for scene in scenes:
                    doc = {
                        "id": f"doc_{doc_id}",
                        "character": scene['metadata']['character_name'],
                        "title": scene['metadata']['script_name'],
                        "script_id": scene['metadata']['script_id'],
                        "type": scene['metadata']['type'],
                        "text": scene['text'],
                        "metadata": scene['metadata']
                    }
                    all_documents.append(doc)
                    doc_id += 1
        
        print(f"\n总共提取了 {len(all_documents)} 个文档片段")
        return all_documents
    
    def vectorize_documents(self, documents: List[Dict[str, Any]], batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        批量向量化文档
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
            
        Returns:
            包含向量的文档列表
        """
        print(f"\n开始向量化 {len(documents)} 个文档...")
        
        vectorized_docs = []
        
        # 批量处理
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc["text"] for doc in batch]
            
            try:
                # 调用Embedding API
                embeddings = self.embeddings.embed_documents(texts)
                
                # 将向量添加到文档中
                for doc, embedding in zip(batch, embeddings):
                    doc["embedding"] = embedding
                    vectorized_docs.append(doc)
                
                print(f"  - 已处理 {len(vectorized_docs)}/{len(documents)} 个文档")
                
            except Exception as e:
                print(f"向量化批次失败: {str(e)}")
                continue
        
        print(f"向量化完成，成功处理 {len(vectorized_docs)} 个文档")
        return vectorized_docs
    
    def process_all_characters(self) -> List[Dict[str, Any]]:
        """
        处理所有角色的数据（主入口方法）
        
        Returns:
            所有角色的向量化文档列表
        """
        # 从enhanced_script提取所有文档
        all_documents = self.process_enhanced_scripts()
        
        if len(all_documents) == 0:
            print("警告: 没有提取到任何文档")
            return []
        
        # 批量向量化
        vectorized_docs = self.vectorize_documents(all_documents)
        
        return vectorized_docs
