"""
多Agent剧本生成系统主入口
实现4个Agent协作的完整剧本生成流程
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .context_builder import ContextBuilder
from .costume_designer_agent import CostumeDesignerAgent
from .screenwriter_agent import ScreenwriterAgent
from .actor_agent import ActorAgent
from .director_agent import DirectorAgent
from .dialogue_manager import DialogueManager
from .script_formatter import ScriptFormatter
from .scene_setting_agent import SceneSettingAgent


class ScriptGenerationSystem:
    """多Agent剧本生成系统 - 4个Agent协作"""
    
    def __init__(self, 
                 character_dir: str = "character",
                 character_data_dir: str = "character_data",
                 vector_index_dir: str = "vector_index",
                 output_dir: str = "generated_scripts"):
        """
        初始化剧本生成系统
        
        Args:
            character_dir: 角色profile目录
            character_data_dir: 角色data目录
            vector_index_dir: 向量索引目录
            output_dir: 输出目录
        """
        self.character_dir = character_dir
        self.character_data_dir = character_data_dir
        self.vector_index_dir = vector_index_dir
        self.output_dir = output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化RAG系统
        self.rag_system = None
        self._initialize_rag_system()
        
        # 初始化上下文构建器
        self.context_builder = ContextBuilder(rag_system=self.rag_system)
        
        # 初始化对话管理器和格式化器
        self.dialogue_manager = DialogueManager()
        self.script_formatter = ScriptFormatter()
        
        # Agent实例
        self.costume_designer = None
        self.screenwriter = None
        self.director = None
        self.actors = {}
        
        print("✓ 剧本生成系统初始化完成")
    
    def _initialize_rag_system(self):
        """初始化RAG系统"""
        try:
            from src.rag_system import RAGSystem
            
            self.rag_system = RAGSystem(
                index_path=self.vector_index_dir
            )
            
            # 加载向量索引
            if os.path.exists(os.path.join(self.vector_index_dir, "faiss.index")):
                self.rag_system.load_index()
                print("✓ RAG系统加载成功")
            else:
                print("⚠ 警告：向量索引不存在，RAG功能将受限")
        except Exception as e:
            print(f"⚠ 警告：RAG系统初始化失败: {str(e)}")
            self.rag_system = None
    
    def generate_script(self,
                       user_request: str,
                       max_scenes: int = 3,
                       max_rounds_per_scene: int = 10,
                       enable_scene_setting: bool = False) -> Dict[str, Any]:
        """
        生成完整剧本 - 4步流程
        
        Args:
            user_request: 用户需求描述
            max_scenes: 最大场景数
            max_rounds_per_scene: 每场景最大对话轮数
            enable_scene_setting: 是否启用场景设定功能（布景和音效），默认False保持向后兼容
            
        Returns:
            包含剧本和元数据的字典
        """
        print(f"\n{'='*70}")
        print(f"开始生成剧本：{user_request}")
        print(f"{'='*70}\n")
        
        # 步骤1：大纲建立
        print("【步骤1/4】大纲建立")
        print("-" * 70)
        characters, outline = self._step1_create_outline(user_request)
        
        # 场景设定生成（可选功能）
        scene_settings = None
        if enable_scene_setting:
            print(f"\n【附加功能】场景设定生成")
            print("-" * 70)
            try:
                scene_settings = self._generate_scene_settings(outline)
                print(f"      ✓ 场景设定生成完成")
            except Exception as e:
                print(f"      ⚠ 场景设定生成失败（不影响剧本生成）: {str(e)}")
                scene_settings = None
        
        # 步骤2：人物特征完善
        print(f"\n【步骤2/4】人物特征完善")
        print("-" * 70)
        costumes = self._step2_design_costumes(characters, outline)
        
        # 步骤3：剧本完善
        print(f"\n【步骤3/4】剧本完善")
        print("-" * 70)
        self._step3_generate_dialogues(characters, outline, costumes, max_scenes, max_rounds_per_scene)
        
        # 步骤4：剧本评估
        print(f"\n【步骤4/4】剧本评估")
        print("-" * 70)
        evaluation = self._step4_evaluate_script(outline, costumes)
        
        # 格式化和保存
        print(f"\n【完成】格式化和保存")
        print("-" * 70)
        dialogue_history = self.dialogue_manager.dialogue_history
        script_text = self.script_formatter.format_script(outline, dialogue_history, scene_settings)
        output_files = self._save_results(outline, script_text, dialogue_history, costumes, evaluation, scene_settings)
        
        print(f"\n{'='*70}")
        print("✓ 剧本生成完成！")
        print(f"{'='*70}\n")
        
        return {
            'outline': outline,
            'costumes': costumes,
            'script_text': script_text,
            'dialogue_history': dialogue_history,
            'evaluation': evaluation,
            'output_files': output_files,
            'scene_settings': scene_settings
        }
    
    def _generate_scene_settings(self, outline: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """
        生成场景设定（布景和音效）
        
        Args:
            outline: 剧本大纲
            
        Returns:
            场景设定字典，格式为 {scene_number: {scenery: str, sound_effects: list}}
        """
        print("  生成各场景的布景和音效...")
        scene_setting_agent = SceneSettingAgent()
        
        scenes = outline.get('scenes', [])
        scene_settings = {}
        
        for idx, scene in enumerate(scenes, 1):
            try:
                # 识别场景类型
                scene_type = self._identify_scene_type(scene, idx)
                
                # 提取角色
                characters = scene.get('characters', [])
                
                # 生成场景设定
                setting = scene_setting_agent.generate_scene_setting(
                    scene_info=scene,
                    scene_type=scene_type,
                    characters=characters
                )
                scene_settings[idx] = setting
                print(f"      场景{idx}: {scene.get('title', '未命名')} - 已生成设定")
            except Exception as e:
                print(f"      场景{idx}: 生成失败 - {str(e)}")
                continue
        
        return scene_settings
    
    def _step1_create_outline(self, user_request: str) -> tuple:
        """
        步骤1：大纲建立
        编剧Agent根据用户需求和RAG检索结果生成剧本大纲
        """
        print("  1.1 提取角色...")
        characters = self.context_builder.extract_characters_from_request(user_request)
        if not characters:
            raise ValueError("未能从需求中识别角色，请确保需求中包含角色名称（如：诸葛亮、孙悟空）")
        print(f"      ✓ 识别到角色：{', '.join(characters)}")
        
        print("  1.2 构建编剧上下文（含RAG检索）...")
        screenwriter_context = self.context_builder.build_screenwriter_context(
            user_request, characters
        )
        
        print("  1.3 生成剧本大纲...")
        self.screenwriter = ScreenwriterAgent(temperature=0.8)
        outline = self.screenwriter.generate_outline(user_request, screenwriter_context)
        
        print(f"      ✓ 剧本大纲生成完成")
        print(f"        剧名：{outline.get('title', '未命名')}")
        print(f"        主题：{outline.get('theme', '未知')}")
        print(f"        场景数：{len(outline.get('scenes', []))}")
        
        return characters, outline
    
    def _step2_design_costumes(self, characters: List[str], outline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        步骤2：人物特征完善
        定妆师Agent根据角色信息和RAG检索确定装扮
        """
        print("  2.1 构建定妆师上下文（含RAG检索）...")
        costume_context = self.context_builder.build_costume_designer_context(
            characters, outline
        )
        
        print("  2.2 设计角色装扮...")
        self.costume_designer = CostumeDesignerAgent("")
        costumes = self.costume_designer.design_all_costumes(
            characters_info=costume_context['characters_info'],
            outline=outline,
            rag_references=costume_context['rag_references']
        )
        
        print(f"      ✓ 所有角色装扮设计完成")
        for char_name, costume in costumes.items():
            print(f"        {char_name}：{costume.get('role_type', '未知')} - {costume.get('overall_style', '未知')[:30]}...")
        
        return costumes
    
    def _step3_generate_dialogues(
        self,
        characters: List[str],
        outline: Dict[str, Any],
        costumes: Dict[str, Dict[str, Any]],
        max_scenes: int,
        max_rounds_per_scene: int
    ):
        """
        步骤3：剧本完善
        演员Agents协作生成对话，编剧Agent协调
        """
        print("  3.1 初始化演员Agents...")
        for character in characters:
            actor_context = self.context_builder.build_actor_context(
                character, outline
            )
            self.actors[character] = ActorAgent(character, actor_context)
        print(f"      ✓ 已初始化 {len(self.actors)} 个演员Agent")
        
        print("  3.2 生成场景对话...")
        scenes = outline.get('scenes', [])[:max_scenes]
        
        for scene_idx, scene in enumerate(scenes, 1):
            print(f"\n      场景 {scene_idx}/{len(scenes)}：{scene.get('title', '未命名')}")
            self._generate_scene_dialogues(
                scene_idx, scene, characters, max_rounds_per_scene
            )
        
        print(f"\n      ✓ 所有场景对话生成完成")
    
    def _generate_scene_dialogues(
        self,
        scene_number: int,
        scene_outline: Dict[str, Any],
        characters: List[str],
        max_rounds: int
    ):
        """生成单个场景的对话"""
        scene_name = f"场景{scene_number}：{scene_outline.get('title', '未命名')}"
        scene_desc = scene_outline.get('description', '')
        self.dialogue_manager.start_scene(scene_name, scene_desc)
        
        # 识别场景类型
        scene_type = self._identify_scene_type(scene_outline, scene_number)
        print(f"        场景类型：{scene_type}")
        
        # 轮流让角色说话
        current_speaker_idx = 0
        character_first_appearance = {char: True for char in characters}
        
        for round_num in range(max_rounds):
            current_speaker = characters[current_speaker_idx]
            actor = self.actors[current_speaker]
            
            # 判断是否首次登场
            is_first_appearance = character_first_appearance.get(current_speaker, False)
            if is_first_appearance:
                character_first_appearance[current_speaker] = False
            
            # 获取最近对话历史
            recent_dialogues = self.dialogue_manager.get_recent_dialogues(count=5)
            
            # 使用RAG检索相似场景（为当前对话提供参考）
            scene_desc = scene_outline.get('description', '')
            if self.rag_system:
                try:
                    from src.rag_system import SemanticRetriever
                    retriever = SemanticRetriever(self.rag_system.vector_store)
                    query = f"{current_speaker} {scene_desc}"
                    rag_refs = retriever.retrieve(query, top_k=2, character_filter=[current_speaker])
                except:
                    rag_refs = []
            else:
                rag_refs = []
            
            # 根据轮次动态调整场景类型
            current_scene_type = self._adjust_scene_type_by_round(
                scene_type, round_num, max_rounds, is_first_appearance
            )
            
            # 生成对话
            scene_context = f"{scene_outline.get('title', '未命名场景')}: {scene_outline.get('description', '')}"
            dialogue_data = actor.generate_dialogue(
                context=scene_context,
                other_dialogues=recent_dialogues,
                is_first_appearance=is_first_appearance,
                scene_type=current_scene_type
            )
            
            if dialogue_data:
                dialogue_data['scene_number'] = scene_number
                dialogue_data['round'] = round_num + 1
                
                # 添加到对话历史
                self.dialogue_manager.add_dialogue(
                    character=dialogue_data['character'],
                    content=dialogue_data['content'],
                    parsed_data=dialogue_data.get('parsed'),
                    metadata={'scene_number': scene_number, 'round': round_num + 1, 'scene_type': current_scene_type}
                )
                
                # 同步给其他演员
                for char_name, other_actor in self.actors.items():
                    if char_name != current_speaker:
                        other_actor.receive_other_dialogue(
                            character=dialogue_data['character'],
                            dialogue=dialogue_data['content']
                        )
                
                # 显示进度
                content_preview = dialogue_data.get('content', '')[:40]
                scene_type_tag = f"[{current_scene_type}]" if current_scene_type != "对话" else ""
                print(f"        轮{round_num + 1}: {current_speaker}{scene_type_tag} - {content_preview}...")
            
            # 切换说话者
            current_speaker_idx = (current_speaker_idx + 1) % len(characters)
            
            # 简单的结束条件：达到最大轮数
            if round_num >= max_rounds - 1:
                print(f"        场景完成（{round_num + 1}轮对话）")
                break
    
    def _identify_scene_type(self, scene_outline: Dict[str, Any], scene_number: int) -> str:
        """
        识别场景类型
        
        Args:
            scene_outline: 场景大纲
            scene_number: 场景编号
            
        Returns:
            场景类型
        """
        title = scene_outline.get('title', '').lower()
        description = scene_outline.get('description', '').lower()
        combined = f"{title} {description}"
        
        # 关键词匹配
        if scene_number == 1 or any(kw in combined for kw in ['开场', '登场', '上场', '初见', '相遇']):
            return "开场"
        elif any(kw in combined for kw in ['武打', '战斗', '打斗', '交手', '对战', '厮杀', '争斗']):
            return "武打"
        elif any(kw in combined for kw in ['抒情', '感慨', '回忆', '思念', '悲伤', '喜悦', '唱']):
            return "抒情"
        elif any(kw in combined for kw in ['叙事', '讲述', '回顾', '说明', '介绍']):
            return "叙事"
        elif any(kw in combined for kw in ['冲突', '争执', '争论', '辩论', '对峙', '愤怒']):
            return "冲突"
        elif any(kw in combined for kw in ['追赶', '逃跑', '追击', '奔跑', '逃离']):
            return "追赶"
        else:
            return "对话"
    
    def _adjust_scene_type_by_round(
        self,
        base_scene_type: str,
        round_num: int,
        max_rounds: int,
        is_first_appearance: bool
    ) -> str:
        """
        根据对话轮次动态调整场景类型
        
        Args:
            base_scene_type: 基础场景类型
            round_num: 当前轮次
            max_rounds: 最大轮次
            is_first_appearance: 是否首次登场
            
        Returns:
            调整后的场景类型
        """
        # 首次登场优先级最高
        if is_first_appearance:
            return "开场"
        
        # 根据轮次调整
        progress = round_num / max_rounds
        
        # 开场场景：前30%保持开场风格
        if base_scene_type == "开场" and progress < 0.3:
            return "开场"
        
        # 武打场景：中间60%保持武打风格
        if base_scene_type == "武打" and 0.2 < progress < 0.8:
            return "武打"
        
        # 抒情场景：适合在中间和结尾
        if base_scene_type == "抒情" and progress > 0.3:
            return "抒情"
        
        # 冲突场景：适合在中间
        if base_scene_type == "冲突" and 0.3 < progress < 0.7:
            return "冲突"
        
        # 其他情况，每3-4轮可能出现一次抒情
        if round_num % 4 == 2 and progress > 0.3:
            return "抒情"
        
        # 默认返回对话
        return "对话"
    
    def _step4_evaluate_script(
        self,
        outline: Dict[str, Any],
        costumes: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        步骤4：剧本评估
        导演Agent评估剧本质量并提供建议
        """
        print("  4.1 构建导演上下文（含RAG参考）...")
        characters = list(costumes.keys())
        director_context = self.context_builder.build_director_context(
            characters, outline
        )
        
        print("  4.2 评估剧本质量...")
        self.director = DirectorAgent(director_context)
        
        dialogue_history = self.dialogue_manager.dialogue_history
        
        # 获取RAG参考场景作为评估标准
        rag_references = []
        if self.rag_system:
            try:
                query = f"{' '.join(characters)} 优秀场景"
                rag_context = self.context_builder.retrieve_rag_context(query, characters, top_k=3)
                rag_references = rag_context.get('results', [])
            except:
                pass
        
        evaluation = self.director.evaluate_script(
            outline=outline,
            dialogue_history=dialogue_history,
            costumes=costumes,
            rag_references=rag_references
        )
        
        print(f"      ✓ 剧本评估完成")
        print(f"        总分：{evaluation.get('overall_score', 0)}/100")
        print(f"        京剧特色：{evaluation.get('scores', {}).get('peking_opera_style', 0)}/30")
        print(f"        角色塑造：{evaluation.get('scores', {}).get('character_portrayal', 0)}/25")
        print(f"        剧情结构：{evaluation.get('scores', {}).get('plot_structure', 0)}/25")
        print(f"        艺术表现：{evaluation.get('scores', {}).get('artistic_expression', 0)}/20")
        
        if evaluation.get('need_revision'):
            print(f"        建议修改：{evaluation.get('revision_priority', 'low')}优先级")
        
        return evaluation
    
    def _save_results(
        self,
        outline: Dict[str, Any],
        script_text: str,
        dialogue_history: List[Dict[str, Any]],
        costumes: Dict[str, Dict[str, Any]],
        evaluation: Dict[str, Any],
        scene_settings: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """保存生成结果"""
        title = outline.get('title', '未命名剧本')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-', '中', '文'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存剧本
        script_path = os.path.join(self.output_dir, f"{safe_title}_剧本.txt")
        self.script_formatter.export_to_file(script_text, script_path)
        print(f"  ✓ 剧本已保存：{script_path}")
        
        # 保存大纲
        outline_path = os.path.join(self.output_dir, f"{safe_title}_大纲.json")
        with open(outline_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 大纲已保存：{outline_path}")
        
        # 保存装扮设计
        costume_path = os.path.join(self.output_dir, f"{safe_title}_装扮设计.json")
        with open(costume_path, 'w', encoding='utf-8') as f:
            json.dump(costumes, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 装扮设计已保存：{costume_path}")
        
        # 保存对话历史
        dialogue_path = os.path.join(self.output_dir, f"{safe_title}_对话历史.json")
        with open(dialogue_path, 'w', encoding='utf-8') as f:
            json.dump(dialogue_history, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 对话历史已保存：{dialogue_path}")
        
        # 保存评估结果
        evaluation_path = os.path.join(self.output_dir, f"{safe_title}_评估报告.json")
        with open(evaluation_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 评估报告已保存：{evaluation_path}")
        
        # 保存评估指导（文本格式）
        guidance = self.director.provide_revision_guidance(evaluation)
        guidance_path = os.path.join(self.output_dir, f"{safe_title}_修改指导.txt")
        with open(guidance_path, 'w', encoding='utf-8') as f:
            f.write(guidance)
        print(f"  ✓ 修改指导已保存：{guidance_path}")
        
        # 保存场景设定（如果有）
        scene_settings_path = None
        if scene_settings:
            scene_settings_path = os.path.join(self.output_dir, f"{safe_title}_场景设定.json")
            with open(scene_settings_path, 'w', encoding='utf-8') as f:
                json.dump(scene_settings, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 场景设定已保存：{scene_settings_path}")
        
        result = {
            'script': script_path,
            'outline': outline_path,
            'costumes': costume_path,
            'dialogue': dialogue_path,
            'evaluation': evaluation_path,
            'guidance': guidance_path
        }
        
        if scene_settings_path:
            result['scene_settings'] = scene_settings_path
        
        return result


def main():
    """主函数示例"""
    print("\n" + "="*70)
    print("京剧剧本生成系统 - 多Agent协作")
    print("="*70 + "\n")
    
    system = ScriptGenerationSystem()
    
    # 示例：诸葛亮和孙悟空煮酒论英雄
    user_request = "诸葛亮和孙悟空煮酒论英雄"
    
    result = system.generate_script(
        user_request=user_request,
        max_scenes=2,
        max_rounds_per_scene=8,
        enable_scene_setting=True  # 启用场景设定功能（布景和音效）
    )
    
    print("\n" + "="*70)
    print("生成结果文件：")
    print("="*70)
    for file_type, file_path in result['output_files'].items():
        print(f"  {file_type}: {file_path}")
    print()


if __name__ == "__main__":
    main()
