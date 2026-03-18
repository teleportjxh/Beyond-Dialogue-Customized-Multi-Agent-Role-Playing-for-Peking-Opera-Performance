"""
数据提取器 - 核心提取逻辑
"""
import os
import json
import copy
import time
from typing import Dict, List, Tuple
from ..config import Config
from .data_models import DataTemplates
from .llm_client import LLMClientManager
from .utils import (
    FileManager, CharacterIDManager, JSONProcessor, 
    ScriptProcessor
)


class RoleInfoExtractor:
    """角色信息提取器"""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.extract_llm = llm_manager.get_extract_llm()
    
    def extract_script_info(self, script_content: str, script_title: str, 
                           role_name: str, script_id: str) -> Dict:
        """提取单个剧本的角色信息"""
        print(f"    提取《{script_title}》中{role_name}的信息...")
        
        prompt = self._build_script_info_prompt(script_content, role_name)
        
        try:
            raw_content = self.extract_llm.invoke(prompt)
            parsed_data = JSONProcessor.safe_json_loads(
                raw_content, "role_info_extract", role_name, script_title
            )
            
            if not isinstance(parsed_data, dict):
                print(f"    ⚠️ 角色信息格式错误，使用默认值")
                FileManager.save_failed_json(
                    raw_content, "role_info_format_error", role_name, script_title
                )
                return self._get_default_script_info(script_id, script_title)
            
            return self._format_script_info(parsed_data, script_id, script_title)
            
        except Exception as e:
            print(f"    ❌ 提取失败：{str(e)}")
            FileManager.save_failed_json(
                str(e), "role_info_extract_error", role_name, script_title
            )
            return self._get_default_script_info(script_id, script_title)
    
    def update_universal_info(self, role_name: str, new_script: Dict, 
                            current_universal: Dict) -> Dict:
        """更新角色通用信息"""
        print(f"    基于《{new_script['title']}》更新通用信息...")
        
        prompt = self._build_universal_info_prompt(
            role_name, new_script, current_universal
        )
        
        try:
            raw_content = self.extract_llm.invoke(prompt)
            parsed_data = JSONProcessor.safe_json_loads(
                raw_content, "universal_info_update", role_name, new_script["title"]
            )
            
            if not isinstance(parsed_data, dict):
                print(f"    ⚠️ 通用信息格式错误，保留历史信息")
                FileManager.save_failed_json(
                    raw_content, "universal_info_format_error", 
                    role_name, new_script["title"]
                )
                return current_universal
            
            return JSONProcessor.validate_and_supplement(
                parsed_data, DataTemplates.UNIVERSAL_INFO_TEMPLATE
            )
            
        except Exception as e:
            print(f"    ❌ 更新失败，保留历史信息：{str(e)}")
            FileManager.save_failed_json(
                str(e), "universal_info_update_error", role_name, new_script["title"]
            )
            return current_universal
    
    def _build_script_info_prompt(self, script_content: str, role_name: str) -> str:
        """构建剧本信息提取提示词"""
        return (
            f"任务：提取剧本中【{role_name}】的信息，以及该剧本的剧情大纲,仅返回JSON字典！\n\n"
            "### 格式要求：\n"
            "1. 仅返回JSON字典，无多余文字\n"
            "2. 必须包含键：outline,age, personality, description, profession, face, makeup, cloth, knowledge\n"
            "下面是部分字段的解释\n"
            "outline: 该剧本剧情大纲\n"
            "age: 人物在该剧本下的年龄\n"
            "personality:人物在该剧本下的个性\n"
            "description:人物在该剧本下的描述\n"
            "profession:行当\n"
            "face:脸谱特征\n"
            "makeup:妆容细节\n"
            "cloth:服饰与头饰\n"
            "knowledge:该角色在该剧本下对于剧情的认知\n"
            "示例：{\"outline\":\"三国时期，蜀汉丞相诸葛亮因错用马谡而失守街亭...\",\"age\":\"老年\",\"personality\":\"沉稳多谋\",\"description\":\"蜀汉丞相，善用计谋\",\"profession\":\"老生(文官，帅才)\",\"face\":\"面部为传统俊扮...\",\"makeup\":\"脸施淡赭色底彩...\",\"cloth\":\"头戴软方巾或诸葛巾...\",\"knowledge\":\"精通兵法\"}\n\n"
            f"### 剧本内容：\n{script_content[:Config.SCRIPT_CONTENT_LIMIT]}\n\n"
            "### 输出：输出前请检查输出的文字，其输出的json字段的内容中不能具有引号，确保其符号符合json格式，仅返回JSON数组，无多余文字"
        )
    
    def _build_universal_info_prompt(self, role_name: str, new_script: Dict, 
                                    current_universal: Dict) -> str:
        """构建通用信息更新提示词"""
        return (
            f"任务：更新【{role_name}】的通用信息，仅返回JSON字典！\n\n"
            "### 格式要求：\n"
            "1. 仅返回JSON字典，无多余文字\n"
            "2. 必须包含键：gender（字符串）, catchphrases（数组）, forbidden（数组）\n"
            "下面是字段的解释\n"
            "gender:性别\n"
            "catchphrases:人物口头禅\n"
            "forbidden:人物禁忌(不会干的事情)\n"
            "示例：{\"gender\":\"男\",\"catchphrases\":[\"臣\"],\"forbidden\":[\"泄露军情\"]}\n\n"
            f"### 历史信息：\n{json.dumps(current_universal, ensure_ascii=False)}\n\n"
            f"### 新剧本内容：\n{new_script['content'][:Config.SCRIPT_CONTENT_LIMIT]}\n\n"
            "### 输出：输出前请检查输出的文字，其输出的json字段的内容中不能具有引号，确保其符号符合json格式，仅返回JSON数组，无多余文字"
        )
    
    def _get_default_script_info(self, script_id: str, script_title: str) -> Dict:
        """获取默认剧本信息"""
        base_info = {"id": script_id, "title": script_title}
        for key in DataTemplates.PERSON_SCRIPT_DATA_TEMPLATE:
            if key not in ["id", "title"]:
                base_info[key] = copy.deepcopy(
                    DataTemplates.PERSON_SCRIPT_DATA_TEMPLATE[key]
                )
        return base_info
    
    def _format_script_info(self, parsed_data: Dict, script_id: str, 
                           script_title: str) -> Dict:
        """格式化剧本信息"""
        base_info = {"id": script_id, "title": script_title}
        for key in DataTemplates.PERSON_SCRIPT_DATA_TEMPLATE:
            if key not in ["id", "title"]:
                value = parsed_data.get(
                    key, copy.deepcopy(DataTemplates.PERSON_SCRIPT_DATA_TEMPLATE[key])
                )
                if isinstance(value, str):
                    value = value.replace('"', '\\"')
                base_info[key] = value
        return base_info


class DialoguePerformanceExtractor:
    """对话和表演提取器"""
    
    def __init__(self, llm_manager: LLMClientManager):
        self.extract_llm = llm_manager.get_extract_llm()
        self.judge_llm = llm_manager.get_judge_llm()
    
    def extract_dialogues_and_performances(self, script_content: str, 
                                          role_name: str, script_title: str) -> Dict:
        """提取对话和表演数据"""
        print(f"    抽取《{script_title}》中{role_name}的对话和表演数据...")
        
        print("    【第一阶段】使用LLM抽取连续对话...")
        llm_dialogues = self._extract_dialogues(role_name, script_content, script_title)
        print(f"    LLM抽取到{len(llm_dialogues)}条对话轮次")
        
        print("    【第二阶段】使用LLM抽取连续表演...")
        llm_performances = self._extract_performances(role_name, script_content, script_title)
        print(f"    LLM抽取到{len(llm_performances)}条表演片段")
        
        all_dialogue_turns = ScriptProcessor.deduplicate_items(llm_dialogues)
        if not all_dialogue_turns:
            return {"dialogues": [], "performances": []}
        
        print("    【第三阶段】组合对话组（支持多角色拆分）...")
        dialogue_groups = self._group_dialogues(all_dialogue_turns, role_name, script_title)
        print(f"    有效对话组：{len(dialogue_groups)}组（含多角色拆分）")
        
        print("    【第四阶段】判断连续表演片段有效性...")
        valid_performances = self._validate_performances(
            llm_performances, role_name, script_title
        )
        print(f"    有效连续表演片段：{len(valid_performances)}条")
        
        return {
            "dialogues": dialogue_groups,
            "performances": valid_performances
        }
    
    def _extract_dialogues(self, role_name: str, script_content: str, 
                          script_title: str) -> List[Dict]:
        """提取对话"""
        all_marked_roles = ScriptProcessor.extract_marked_roles(script_content)
        roles_str = ", ".join(all_marked_roles) if all_marked_roles else "其他带**标记的角色"
        
        correct_example = '''[
{"role":"赵云","content":"(白) 丞相，司马懿大军已至城下！[单膝跪地，语气急切。]"},
{"role":"诸葛亮","content":"(白) 老将军莫慌，传令下去，大开城门。[羽扇轻摇，神态镇定。]"},
{"role":"马谡","content":"(白) 丞相不可！此乃空城，司马懿进城必败！[快步上前，抱拳劝阻。]"},
{"role":"诸葛亮","content":"(白) 幼常多虑，司马懿生性多疑，必不进城。[目光坚定，挥手示意马谡退下。]"}
]'''
        
        prompt = (
            f"任务：从以下剧本中提取【包含{role_name}的完整对话】，需覆盖多角色交互场景，严格按示例格式返回JSON数组！\n\n"
            "### 核心要求：\n"
            f"1. 对话需完整：包含{role_name}与其他角色的交互，若有第三角色介入需完整记录\n"
            "2. 角色区分：明确标注每个台词的角色名（如示例中的赵云、诸葛亮、马谡）\n"
            "3. 排除表演内容：仅保留(白)/(念)，排除(唱)/(西皮)/(二黄)\n\n"
            "### 格式要求：\n"
            "每个对话对象为：{\"role\":\"角色名\",\"content\":\"(白) 台词[动作描写]\"}\n\n"
            f"### 多角色交互示例：\n{correct_example}\n"
            "（示例中马谡为第三角色，介入诸葛亮与赵云的对话）\n\n"
            f"### 剧本内容：\n{script_content[:Config.SCRIPT_CONTENT_LIMIT]}\n\n"
            "### 输出：输出前请检查输出的文字，确保其符号符合json格式，仅返回JSON数组，无多余文字"
        )
        
        try:
            raw_content = self.extract_llm.invoke(prompt)
            result = JSONProcessor.safe_json_loads(
                raw_content, "dialogue_extract", role_name, script_title
            )
            if isinstance(result, list):
                return [item for item in result if isinstance(item, dict) 
                       and "role" in item and item["role"].strip() 
                       and "content" in item 
                       and (item["role"] == role_name or any(
                           r["role"] == role_name for r in result 
                           if isinstance(r, dict) and "role" in r
                       ))]
            return []
        except Exception as e:
            print(f"    ❌ LLM对话抽取失败：{str(e)}")
            FileManager.save_failed_json(
                str(e), "dialogue_extract_error", role_name, script_title
            )
            return []
    
    def _extract_performances(self, role_name: str, script_content: str, 
                            script_title: str) -> List[Dict]:
        """提取表演"""
        correct_example = '''[
{"role":"诸葛亮","content":"(唱) [西皮慢板]我本是卧龙岗散淡的人，[轻摇羽扇，目光远眺，神情悠然自得。](昔日隐居山林，不问世事，如今却身负重任，此情此景，不禁追忆往昔)论阴阳如反掌保定乾坤。[羽扇收回至胸前，双手轻握扇柄，向城外作揖，眼神坚定。](天机在握，运筹帷幄之中，决胜千里之外)先帝爷下南阳御驾三请，[右手持扇指向台左方向，双手合一，再三作揖，头部微微颔首。](感念刘备三顾之情)算就了汉家业鼎足三分。[左手呈单指状轻晃，感慨天下局势。]"}
]'''
        
        prompt = (
            f"任务：从以下剧本中提取【{role_name}的完整连续表演】，严格按示例格式返回JSON数组！\n\n"
            "### 核心要求：\n"
            f"1. 表演需连续完整：从{role_name}开始表演，到其他角色对话/表演前结束\n"
            "2. 元素完整：包含(唱)标注、[板式]、唱词、[动作描写]、(内心独白)\n\n"
            "### 格式要求：\n"
            "{\"role\":\"角色名\",\"content\":\"(唱) [板式]唱词[动作](内心独白)...完整内容\"}\n\n"
            f"### 连续表演示例：\n{correct_example}\n\n"
            f"### 剧本内容：\n{script_content[:Config.SCRIPT_CONTENT_LIMIT]}\n\n"
            "### 输出：输出前请检查输出内容，确保其符号符合json格式，仅返回JSON数组，无多余文字"
        )
        
        try:
            raw_content = self.extract_llm.invoke(prompt)
            result = JSONProcessor.safe_json_loads(
                raw_content, "performance_extract", role_name, script_title
            )
            if isinstance(result, list):
                return [item for item in result if isinstance(item, dict) 
                       and "role" in item and item["role"] == role_name 
                       and "content" in item and item["content"].startswith("(唱)")]
            return []
        except Exception as e:
            print(f"    ❌ LLM表演抽取失败：{str(e)}")
            FileManager.save_failed_json(
                str(e), "performance_extract_error", role_name, script_title
            )
            return []
    
    def _group_dialogues(self, all_dialogue_turns: List[Dict], 
                        role_name: str, script_title: str) -> List[Dict]:
        """组合对话组"""
        dialogue_groups = []
        current_group = [all_dialogue_turns[0]]
        core_roles = {role_name, all_dialogue_turns[0]["role"]}
        if role_name in core_roles:
            core_roles.discard(role_name)
        
        for turn in all_dialogue_turns[1:]:
            current_role = turn["role"]
            
            if current_role in core_roles or current_role == role_name:
                current_group.append(turn)
            else:
                if len(current_group) >= Config.MIN_DIALOGUE_GROUP_SIZE:
                    is_valid, reason = self._judge_dialogue_validity(
                        role_name, current_group, script_title
                    )
                    if is_valid:
                        dialogue_groups.append({
                            "group": current_group,
                            "source": "llm",
                            "judgment": {"is_valid": True, "reason": reason}
                        })
                
                current_group = [turn]
                core_roles = {role_name, current_role}
        
        if len(current_group) >= Config.MIN_DIALOGUE_GROUP_SIZE:
            is_valid, reason = self._judge_dialogue_validity(
                role_name, current_group, script_title
            )
            if is_valid:
                dialogue_groups.append({
                    "group": current_group,
                    "source": "llm",
                    "judgment": {"is_valid": True, "reason": reason}
                })
        
        return dialogue_groups
    
    def _validate_performances(self, llm_performances: List[Dict], 
                              role_name: str, script_title: str) -> List[Dict]:
        """验证表演有效性"""
        valid_performances = []
        seen_perfs = set()
        
        for perf in llm_performances:
            content = perf.get("content", "").strip()
            if not content or content in seen_perfs or len(content) < Config.MIN_PERFORMANCE_LENGTH:
                continue
            seen_perfs.add(content)
            
            if any(tag in content for tag in ["(唱)", "(西皮)", "(二黄)"]):
                is_valid, reason = self._judge_performance_validity(
                    role_name, content, script_title
                )
                if is_valid:
                    valid_performances.append({
                        "content": content,
                        "source": "llm",
                        "judgment": {"is_valid": True, "reason": reason}
                    })
        
        return valid_performances
    
    def _judge_dialogue_validity(self, role_name: str, dialogue_group: List[Dict], 
                                script_title: str) -> Tuple[bool, str]:
        """判断对话有效性"""
        roles_in_group = list(set([
            item["role"] for item in dialogue_group 
            if isinstance(item, dict) and "role" in item
        ]))
        
        prompt = (
            "任务：判断以下对话组是否有效，仅返回JSON！\n"
            "有效标准：\n"
            "1. 格式正确：包含(白)/(念)、台词、[动作描写]\n"
            f"2. 包含{role_name}：至少有一句是{role_name}的台词\n"
            "3. 连续性：角色交互自然（允许第三角色介入，但需完整）\n"
            "4. 无表演内容：不含(唱)/(西皮)/(二黄)\n"
            f"对话组角色：{','.join(roles_in_group)}\n"
            f"对话组：{json.dumps(dialogue_group, ensure_ascii=False)}\n"
            "输出格式：{\"is_valid\":true/false,\"reason\":\"判断依据（说明是否含第三角色及连续性）\"}"
        )
        
        try:
            raw_judgment = self.judge_llm.invoke(prompt)
            judgment = JSONProcessor.safe_json_loads(
                raw_judgment, "dialogue_judgment", role_name, script_title
            )
            return judgment.get("is_valid", False), judgment.get("reason", "未获取依据")
        except Exception as e:
            error_msg = f"判断出错：{str(e)}"
            print(f"    ❌ {error_msg}")
            FileManager.save_failed_json(
                error_msg, "dialogue_judgment_error", role_name, script_title
            )
            return False, error_msg
    
    def _judge_performance_validity(self, role_name: str, performance_content: str, 
                                   script_title: str) -> Tuple[bool, str]:
        """判断表演有效性"""
        prompt = (
            "任务：判断以下表演是否有效，仅返回JSON！\n"
            "有效标准：\n"
            "1. 格式正确：包含(西皮)(二黄)(唱)、[板式]\n"
            f"2. 连续性：是{role_name}的完整表演（无其他角色介入）\n"
            "3. 长度达标：内容不少于20字符\n"
            f"表演内容：{performance_content}\n"
            "输出格式：{\"is_valid\":true/false,\"reason\":\"判断依据\"}"
        )
        
        try:
            raw_judgment = self.judge_llm.invoke(prompt)
            judgment = JSONProcessor.safe_json_loads(
                raw_judgment, "performance_judgment", role_name, script_title
            )
            return judgment.get("is_valid", False), judgment.get("reason", "未获取依据")
        except Exception as e:
            error_msg = f"判断出错：{str(e)}"
            print(f"    ❌ {error_msg}")
            FileManager.save_failed_json(
                error_msg, "performance_judgment_error", role_name, script_title
            )
            return False, error_msg


class CharacterDataExtractor:
    """角色数据提取器（主控制器）"""
    
    def __init__(self):
        self.llm_manager = LLMClientManager()
        self.role_info_extractor = RoleInfoExtractor(self.llm_manager)
        self.dialogue_perf_extractor = DialoguePerformanceExtractor(self.llm_manager)
    
    def process_all_characters(self):
        """处理所有角色"""
        start_time = time.time()
        
        FileManager.create_directories()
        role_scripts = ScriptProcessor.collect_scripts(Config.ENHANCED_SCRIPT_PATH)
        
        if not role_scripts:
            return
        
        print(f"[3/4] 处理角色信息和数据...")
        
        for role_idx, (role_name, scripts) in enumerate(role_scripts.items(), 1):
            print(f"\n===== 处理角色 {role_idx}/{len(role_scripts)}：{role_name} =====")
            role_start_time = time.time()
            
            self._process_single_character(role_name, scripts)
            
            role_time = time.time() - role_start_time
            print(f"\n===== 角色【{role_name}】处理完成，耗时{role_time:.2f}秒 =====")
        
        total_time = time.time() - start_time
        print(f"\n[4/4] 所有处理完成！总耗时{total_time:.2f}秒")
        
        if os.path.exists(Config.ERROR_JSON_DIR) and len(os.listdir(Config.ERROR_JSON_DIR)) > 0:
            print(f"⚠️  注意：有{len(os.listdir(Config.ERROR_JSON_DIR))}个JSON解析失败文件已保存到 {Config.ERROR_JSON_DIR}")
    
    def _process_single_character(self, role_name: str, scripts: List[Dict]):
        """处理单个角色"""
        char_dir = os.path.join(Config.CHARACTER_PATH, role_name)
        os.makedirs(char_dir, exist_ok=True)
        profile_path = os.path.join(char_dir, "profile.json")
        
        char_data_dir = os.path.join(Config.CHARACTER_DATA_PATH, role_name)
        os.makedirs(char_data_dir, exist_ok=True)
        data_path = os.path.join(char_data_dir, "data.json")
        
        all_data = []
        data_id = 1
        
        char_id = CharacterIDManager.get_unique_id(role_name)
        print(f"    角色唯一ID：{char_id}")
        
        profile, current_universal, existing_script_ids = self._load_or_create_profile(
            profile_path, char_id, role_name
        )
        
        for script_idx, script in enumerate(scripts, 1):
            script_title = script["title"]
            script_path = script["path"]
            script_id = str(script_idx)
            
            if script_id in existing_script_ids:
                print(f"\n  剧本 {script_idx}/{len(scripts)}：《{script_title}》已处理，跳过")
                continue
            
            print(f"\n  处理剧本 {script_idx}/{len(scripts)}：《{script_title}》")
            
            script_content = self._read_script(script_path, role_name, script_title)
            if not script_content:
                continue
            
            single_script_info = self.role_info_extractor.extract_script_info(
                script_content, script_title, role_name, script_id
            )
            
            current_universal = self.role_info_extractor.update_universal_info(
                role_name, {"title": script_title, "content": script_content}, 
                current_universal
            )
            print(f"    更新后通用信息：{json.dumps(current_universal, ensure_ascii=False)}")
            
            profile["data"]["script_data"].append(single_script_info)
            profile["data"]["gender"] = current_universal["gender"]
            profile["data"]["catchphrases"] = current_universal["catchphrases"]
            profile["data"]["forbidden"] = current_universal["forbidden"]
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            print(f"    已保存角色信息（累计{len(profile['data']['script_data'])}个剧本）")
            
            split_data = self.dialogue_perf_extractor.extract_dialogues_and_performances(
                script_content, role_name, script_title
            )
            
            data_id = self._process_dialogues(
                split_data["dialogues"], all_data, data_id, profile, 
                single_script_info, current_universal, role_name, script_title
            )
            
            data_id = self._process_performances(
                split_data["performances"], all_data, data_id, profile, 
                single_script_info, current_universal, role_name, script_title
            )
            
            print(f"    已处理《{script_title}》，累计{len(all_data)}条有效数据")
        
        try:
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"    ❌ 保存角色数据失败: {str(e)}")
            FileManager.save_failed_json(str(e), "data_save_error", role_name, "")
    
    def _load_or_create_profile(self, profile_path: str, char_id: str, 
                               role_name: str) -> Tuple[Dict, Dict, List[str]]:
        """加载或创建角色profile"""
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                
                if isinstance(profile["data"]["script_data"], dict):
                    profile["data"]["script_data"] = [profile["data"]["script_data"]]
                
                sorted_script_data = []
                for item in profile["data"]["script_data"]:
                    sorted_item = {"id": item.get("id", ""), "title": item.get("title", "")}
                    for key, value in item.items():
                        if key not in ["id", "title"]:
                            sorted_item[key] = value
                    sorted_script_data.append(sorted_item)
                profile["data"]["script_data"] = sorted_script_data
                
                current_universal = {
                    "gender": profile["data"]["gender"],
                    "catchphrases": profile["data"]["catchphrases"],
                    "forbidden": profile["data"]["forbidden"]
                }
                existing_script_ids = [item["id"] for item in profile["data"]["script_data"]]
                print(f"    加载现有角色信息，已包含{len(existing_script_ids)}个剧本的数据")
            except Exception as e:
                print(f"    现有profile格式错误，重新初始化: {str(e)}")
                FileManager.save_failed_json(str(e), "profile_load_error", role_name, "")
                profile = DataTemplates.get_person_template()
                profile["id"] = char_id
                profile["name"] = role_name
                current_universal = DataTemplates.get_universal_info_template()
                existing_script_ids = []
        else:
            profile = DataTemplates.get_person_template()
            profile["id"] = char_id
            profile["name"] = role_name
            current_universal = DataTemplates.get_universal_info_template()
            existing_script_ids = []
        
        return profile, current_universal, existing_script_ids
    
    def _read_script(self, script_path: str, role_name: str, script_title: str) -> str:
        """读取剧本内容"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            print(f"    ✅ 成功读取剧本（{len(script_content)}字符）")
            if "**" not in script_content:
                print(f"    ⚠️ 剧本无**角色标记，跳过此剧本")
                return ""
            return script_content
        except Exception as e:
            print(f"    ❌ 读取失败：{str(e)}，跳过")
            FileManager.save_failed_json(str(e), "script_read_error", role_name, script_title)
            return ""
    
    def _process_dialogues(self, dialogues: List[Dict], all_data: List[Dict], 
                          data_id: int, profile: Dict, single_script_info: Dict,
                          current_universal: Dict, role_name: str, script_title: str) -> int:
        """处理对话数据"""
        for dialog in dialogues:
            dialog_entry = DataTemplates.get_dialogue_template()
            dialog_entry["id"] = str(data_id)
            dialog_entry["title"] = script_title
            dialog_entry["role"]["bot"] = {
                "id": profile["id"],
                "name": role_name,
                "outline": single_script_info["outline"],
                "age": single_script_info["age"],
                "gender": current_universal["gender"],
                "personality": single_script_info["personality"],
                "catchphrases": current_universal["catchphrases"],
                "description": single_script_info["description"],
                "forbidden": current_universal["forbidden"],
                "knowledge": single_script_info["knowledge"]
            }
            
            roles_in_group = set([item["role"] for item in dialog["group"]])
            roles_in_group.discard(role_name)
            main_user = next(iter(roles_in_group)) if roles_in_group else "未知角色"
            third_roles = [r for r in roles_in_group if r != main_user]
            
            dialog_entry["role"]["user"]["name"] = main_user
            dialog_entry["third_role"] = third_roles[0] if third_roles else ""
            dialog_entry["messages"] = dialog["group"]
            dialog_entry["judgment"] = dialog["judgment"]
            
            all_data.append(dialog_entry)
            data_id += 1
        
        return data_id
    
    def _process_performances(self, performances: List[Dict], all_data: List[Dict],
                            data_id: int, profile: Dict, single_script_info: Dict,
                            current_universal: Dict, role_name: str, script_title: str) -> int:
        """处理表演数据"""
        for perf in performances:
            perf_entry = DataTemplates.get_performance_template()
            perf_entry["id"] = str(data_id)
            perf_entry["title"] = script_title
            perf_entry["role"]["bot"] = {
                "id": profile["id"],
                "name": role_name,
                "outline": single_script_info["outline"],
                "age": single_script_info["age"],
                "gender": current_universal["gender"],
                "personality": single_script_info["personality"],
                "catchphrases": current_universal["catchphrases"],
                "description": single_script_info["description"],
                "forbidden": current_universal["forbidden"],
                "knowledge": single_script_info["knowledge"]
            }
            
            perf_lines = [line.strip() for line in perf["content"].split('\n') if line.strip()]
            perf_entry["messages"] = [{"role": role_name, "content": line} for line in perf_lines]
            perf_entry["judgment"] = perf["judgment"]
            
            all_data.append(perf_entry)
            data_id += 1
        
        return data_id
