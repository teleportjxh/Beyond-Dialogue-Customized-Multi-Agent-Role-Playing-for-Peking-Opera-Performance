"""
京剧创作 Crew - 主编排层
使用 CrewAI 框架编排多Agent协作完成京剧剧本创作
"""
import json
import os
from typing import Dict, List, Any, Optional
from crewai import Crew, Process
from openai import OpenAI

from src.config import Config
from src.memory.sliding_window_memory import SlidingWindowMemory
from src.memory.rag_long_term_memory import RAGLongTermMemory
from src.tools.rag_tools import RAGSearchTool, CharacterSceneRetrieveTool
from src.tools.character_tools import (
    LoadCharacterProfileTool, LoadCharacterDataTool, ExtractCharactersTool
)
from src.tools.script_tools import ParseJSONTool, FormatScriptTool
from src.agents.screenwriter import create_screenwriter_agent
from src.agents.costume_designer import create_costume_designer_agent
from src.agents.scene_designer import create_scene_designer_agent
from src.agents.actor import create_actor_agent
from src.agents.director import create_director_agent
from src.crew.tasks import (
    create_outline_task,
    create_costume_design_task,
    create_costume_review_task,
    create_scene_design_task,
    create_scene_review_task,
    create_action_plan_task,
    create_dialogue_task,
    create_dialogue_review_task,
    create_next_speaker_task,
    create_final_evaluation_task,
)


class PekingOperaCrew:
    """
    京剧创作Crew - 采用CrewAI结构编排多Agent协作
    
    流程：
    Phase 1: 大纲创作（编剧主导）
    Phase 2: 设计阶段（编剧审查服装和场景）
    Phase 3: 对话生成（导演控制流程，演员表演）
    Phase 4: 评估与优化
    """
    
    def __init__(self):
        """初始化京剧创作Crew"""
        self.llm = "openai/" + Config.MODEL_NAME
        
        os.environ["OPENAI_API_KEY"] = Config.API_KEY
        os.environ["OPENAI_API_BASE"] = Config.BASE_URL
        
        # 记忆系统
        self.long_term_memory = RAGLongTermMemory()
        self.dialogue_memories: Dict[str, SlidingWindowMemory] = {}
        
        # 工具
        self.rag_search_tool = RAGSearchTool()
        self.character_scene_tool = CharacterSceneRetrieveTool()
        self.profile_tool = LoadCharacterProfileTool()
        self.data_tool = LoadCharacterDataTool()
        self.extract_tool = ExtractCharactersTool()
        self.json_tool = ParseJSONTool()
        self.format_tool = FormatScriptTool()
        
        # 核心Agents
        self.screenwriter = create_screenwriter_agent(
            llm=self.llm,
            tools=[self.rag_search_tool, self.profile_tool, self.data_tool,
                   self.extract_tool, self.json_tool]
        )
        self.costume_designer = create_costume_designer_agent(
            llm=self.llm,
            tools=[self.profile_tool, self.rag_search_tool]
        )
        self.scene_designer = create_scene_designer_agent(
            llm=self.llm,
            tools=[self.rag_search_tool]
        )
        self.director = create_director_agent(
            llm=self.llm,
            tools=[self.rag_search_tool, self.json_tool]
        )
        
        # 演员Agents（动态创建）
        self.actors: Dict[str, Any] = {}
        
        # 中间结果
        self.outline = None
        self.costume_design = None
        self.scene_design = None
        self.dialogue_history: List[Dict] = []
        self.evaluation = None
    
    def _get_dialogue_memory(self, character_name: str) -> SlidingWindowMemory:
        if character_name not in self.dialogue_memories:
            self.dialogue_memories[character_name] = SlidingWindowMemory(window_size=10)
        return self.dialogue_memories[character_name]
    
    def _create_actor_for_character(self, character_name: str) -> Any:
        profile_result = self.profile_tool._run(character_name)
        data_result = self.data_tool._run(character_name)
        knowledge = self.long_term_memory.get_character_knowledge(character_name)
        actor = create_actor_agent(
            llm=self.llm,
            character_name=character_name,
            character_profile=profile_result,
            character_data=data_result,
            character_knowledge=knowledge,
            tools=[self.rag_search_tool, self.data_tool]
        )
        self.actors[character_name] = actor
        return actor
    
    def _extract_characters(self, user_request: str) -> List[str]:
        result = self.extract_tool._run(user_request)
        try:
            data = json.loads(result)
            return data.get('characters', [])
        except json.JSONDecodeError:
            return []
    
    def _gather_characters_info(self, characters: List[str]) -> str:
        info_parts = []
        for char in characters:
            profile = self.profile_tool._run(char)
            data = self.data_tool._run(char)
            info_parts.append("### " + char + "\n**档案**: " + profile + "\n**数据**: " + data)
        return "\n\n".join(info_parts)
    
    def _parse_json_result(self, result: str) -> Dict:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            parsed = self.json_tool._run(result)
            try:
                return json.loads(parsed)
            except json.JSONDecodeError:
                return {"raw": result}
    
    def _run_single_task(self, agent, task):
        """运行单个任务的辅助方法"""
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        return str(crew.kickoff())
    
    # ==================== Phase 1: 大纲创作 ====================
    
    def phase1_outline(self, user_request: str, characters: List[str]) -> Dict:
        print("\n" + "=" * 60)
        print("Phase 1: 剧本大纲创作")
        print("=" * 60)
        
        characters_info = self._gather_characters_info(characters)
        task = create_outline_task(self.screenwriter, user_request, characters_info)
        result = self._run_single_task(self.screenwriter, task)
        self.outline = self._parse_json_result(result)
        
        print("[完成] 大纲创作完成: " + self.outline.get('title', '未命名'))
        return self.outline
    
    # ==================== Phase 2: 设计阶段 ====================
    
    def phase2_design(self, outline: Dict, characters: List[str]) -> tuple:
        print("\n" + "=" * 60)
        print("Phase 2: 设计阶段（服装 + 场景）")
        print("=" * 60)
        
        outline_str = json.dumps(outline, ensure_ascii=False, indent=2)
        characters_info = self._gather_characters_info(characters)
        
        # 2a: 服装设计
        print("\n--- 2a: 服装设计 ---")
        costume_task = create_costume_design_task(self.costume_designer, outline_str, characters_info)
        costume_result = self._run_single_task(self.costume_designer, costume_task)
        
        # 编剧审查服装
        print("\n--- 编剧审查服装设计 ---")
        review_task = create_costume_review_task(self.screenwriter, costume_result)
        review_result = self._run_single_task(self.screenwriter, review_task)
        review_data = self._parse_json_result(review_result)
        
        if not review_data.get('approved', True):
            print("\n--- 服装设计修改中 ---")
            feedback = review_data.get('feedback', '') + '\n' + str(review_data.get('suggestions', ''))
            revised_task = create_costume_design_task(
                self.costume_designer,
                outline_str + "\n\n## 编剧审查反馈\n" + feedback,
                characters_info
            )
            costume_result = self._run_single_task(self.costume_designer, revised_task)
        
        self.costume_design = self._parse_json_result(costume_result)
        print("[完成] 服装设计完成")
        
        # 2b: 场景设计
        print("\n--- 2b: 场景设计 ---")
        scene_task = create_scene_design_task(self.scene_designer, outline_str)
        scene_result = self._run_single_task(self.scene_designer, scene_task)
        
        # 编剧审查场景
        print("\n--- 编剧审查场景设计 ---")
        scene_review_task = create_scene_review_task(self.screenwriter, scene_result)
        scene_review_result = self._run_single_task(self.screenwriter, scene_review_task)
        scene_review_data = self._parse_json_result(scene_review_result)
        
        if not scene_review_data.get('approved', True):
            print("\n--- 场景设计修改中 ---")
            feedback = scene_review_data.get('feedback', '') + '\n' + str(scene_review_data.get('suggestions', ''))
            revised_task = create_scene_design_task(
                self.scene_designer,
                outline_str + "\n\n## 编剧审查反馈\n" + feedback
            )
            scene_result = self._run_single_task(self.scene_designer, revised_task)
        
        self.scene_design = self._parse_json_result(scene_result)
        print("[完成] 场景设计完成")
        
        return self.costume_design, self.scene_design
    
    # ==================== Phase 3: 对话生成 ====================
    
    def phase3_dialogue(self, outline: Dict, characters: List[str]) -> List[Dict]:
        print("\n" + "=" * 60)
        print("Phase 3: 对话生成（导演控制 + 演员表演）")
        print("=" * 60)
        
        for char in characters:
            self._create_actor_for_character(char)
        
        scenes = outline.get('scenes', [])
        all_dialogues = []
        
        for scene_idx, scene in enumerate(scenes):
            scene_num = scene_idx + 1
            scene_name = scene.get('name', '场景' + str(scene_num))
            scene_chars = scene.get('characters', characters)
            
            print("\n--- 第" + str(scene_num) + "场: " + scene_name + " ---")
            
            # 编剧规划演员行动
            scene_str = json.dumps(scene, ensure_ascii=False, indent=2)
            action_plan_task = create_action_plan_task(self.screenwriter, scene_str, scene_num)
            action_plan = self._run_single_task(self.screenwriter, action_plan_task)
            
            # 导演控制对话循环
            scene_dialogues = []
            max_turns = 8
            
            for turn in range(max_turns):
                # 构建对话历史字符串
                history_parts = []
                for d in scene_dialogues:
                    history_parts.append("[" + d['character'] + "] " + d['content'][:200])
                dialogue_history_str = "\n".join(history_parts) if history_parts else "（尚无对话）"
                
                # 导演决定下一个说话者
                next_speaker_task = create_next_speaker_task(
                    self.director, scene_str, dialogue_history_str, ", ".join(scene_chars)
                )
                speaker_result = self._parse_json_result(
                    self._run_single_task(self.director, next_speaker_task)
                )
                
                if speaker_result.get('dialogue_end', False):
                    print("  导演决定结束第" + str(scene_num) + "场对话")
                    break
                
                next_speaker = speaker_result.get('next_speaker', scene_chars[turn % len(scene_chars)])
                print("  导演选择: " + next_speaker + " 发言")
                
                # 确保该角色有对应的演员Agent
                if next_speaker not in self.actors:
                    self._create_actor_for_character(next_speaker)
                
                actor = self.actors[next_speaker]
                memory = self._get_dialogue_memory(next_speaker)
                
                # 演员生成对话（含自我审查）
                dialogue_task = create_dialogue_task(
                    actor=actor,
                    character_name=next_speaker,
                    scene_context=scene_str,
                    action_plan=action_plan,
                    dialogue_history=dialogue_history_str
                )
                dialogue_result = self._run_single_task(actor, dialogue_task)
                
                # 导演审查对话
                review_task = create_dialogue_review_task(
                    self.director, next_speaker, dialogue_result, scene_str
                )
                review_result = self._parse_json_result(
                    self._run_single_task(self.director, review_task)
                )
                
                # 如果导演不通过，给出反馈让演员修改
                if review_result.get('revision_needed', False):
                    guidance = review_result.get('revision_guidance', '请改进表演质量')
                    print("  导演要求修改: " + guidance[:50])
                    
                    revised_task = create_dialogue_task(
                        actor=actor,
                        character_name=next_speaker,
                        scene_context=scene_str,
                        action_plan=action_plan + "\n\n## 导演修改指导\n" + guidance,
                        dialogue_history=dialogue_history_str
                    )
                    dialogue_result = self._run_single_task(actor, revised_task)
                
                # 记录对话
                dialogue_entry = {
                    'character': next_speaker,
                    'content': dialogue_result,
                    'scene_number': scene_num,
                    'turn': turn + 1,
                    'review_score': review_result.get('score', 0)
                }
                scene_dialogues.append(dialogue_entry)
                
                # 更新短期记忆
                memory.add(role=next_speaker, content=dialogue_result,
                          metadata={'scene': scene_num, 'turn': turn + 1})
                
                # 更新其他角色的记忆
                for other_char in scene_chars:
                    if other_char != next_speaker:
                        other_memory = self._get_dialogue_memory(other_char)
                        other_memory.add(
                            role=next_speaker,
                            content=dialogue_result,
                            metadata={'scene': scene_num, 'turn': turn + 1}
                        )
            
            all_dialogues.extend(scene_dialogues)
        
        self.dialogue_history = all_dialogues
        print("\n[完成] 对话生成完成，共" + str(len(all_dialogues)) + "轮对话")
        return all_dialogues
    
    # ==================== Phase 4: 评估 ====================
    
    def phase4_evaluate(self, outline: Dict, dialogues: List[Dict]) -> Dict:
        print("\n" + "=" * 60)
        print("Phase 4: 最终评估")
        print("=" * 60)
        
        # 构建完整剧本文本
        script_parts = ["# " + outline.get('title', '未命名剧本') + "\n"]
        current_scene = 0
        for d in dialogues:
            if d['scene_number'] != current_scene:
                current_scene = d['scene_number']
                script_parts.append("\n## 第" + str(current_scene) + "场\n")
            script_parts.append("[" + d['character'] + "]\n" + d['content'] + "\n")
        
        full_script = "\n".join(script_parts)
        
        eval_task = create_final_evaluation_task(self.director, full_script)
        eval_result = self._run_single_task(self.director, eval_task)
        self.evaluation = self._parse_json_result(eval_result)
        
        print("[完成] 评估完成")
        return self.evaluation
    
    # ==================== 主流程 ====================
    
    def run(self, user_request: str) -> Dict:
        """
        执行完整的京剧剧本创作流程
        
        Args:
            user_request: 用户需求描述
            
        Returns:
            包含所有结果的字典
        """
        print("\n" + "#" * 60)
        print("# 京剧多Agent创作系统 (CrewAI)")
        print("# 用户需求: " + user_request)
        print("#" * 60)
        
        # 提取角色
        characters = self._extract_characters(user_request)
        if not characters:
            print("[警告] 未识别到角色，请确保输入中包含已有角色名")
            return {"error": "未识别到角色"}
        
        print("识别到角色: " + ", ".join(characters))
        
        # Phase 1: 大纲
        outline = self.phase1_outline(user_request, characters)
        
        # Phase 2: 设计
        costume_design, scene_design = self.phase2_design(outline, characters)
        
        # Phase 3: 对话
        dialogues = self.phase3_dialogue(outline, characters)
        
        # Phase 4: 评估
        evaluation = self.phase4_evaluate(outline, dialogues)
        
        # 保存结果
        result = {
            'user_request': user_request,
            'characters': characters,
            'outline': outline,
            'costume_design': costume_design,
            'scene_design': scene_design,
            'dialogues': dialogues,
            'evaluation': evaluation
        }
        
        self._save_results(result, outline.get('title', '未命名'))
        
        print("\n" + "#" * 60)
        print("# 创作完成!")
        print("#" * 60)
        
        return result
    
    def _save_results(self, result: Dict, title: str):
        """保存所有结果到文件"""
        output_dir = "generated_scripts"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存大纲
        with open(os.path.join(output_dir, title + "_大纲.json"), 'w', encoding='utf-8') as f:
            json.dump(result['outline'], f, ensure_ascii=False, indent=2)
        
        # 保存装扮设计
        with open(os.path.join(output_dir, title + "_装扮设计.json"), 'w', encoding='utf-8') as f:
            json.dump(result['costume_design'], f, ensure_ascii=False, indent=2)
        
        # 保存场景设定
        with open(os.path.join(output_dir, title + "_场景设定.json"), 'w', encoding='utf-8') as f:
            json.dump(result['scene_design'], f, ensure_ascii=False, indent=2)
        
        # 保存对话历史
        with open(os.path.join(output_dir, title + "_对话历史.json"), 'w', encoding='utf-8') as f:
            json.dump(result['dialogues'], f, ensure_ascii=False, indent=2)
        
        # 保存评估报告
        with open(os.path.join(output_dir, title + "_评估报告.json"), 'w', encoding='utf-8') as f:
            json.dump(result['evaluation'], f, ensure_ascii=False, indent=2)
        
        # 保存完整剧本文本
        script_parts = ["# " + title + "\n"]
        current_scene = 0
        for d in result['dialogues']:
            if d['scene_number'] != current_scene:
                current_scene = d['scene_number']
                script_parts.append("\n## 第" + str(current_scene) + "场\n")
            script_parts.append("[" + d['character'] + "]\n" + d['content'] + "\n")
        
        with open(os.path.join(output_dir, title + "_剧本.txt"), 'w', encoding='utf-8') as f:
            f.write("\n".join(script_parts))
        
        print("[保存] 所有结果已保存到 " + output_dir + "/ 目录")
