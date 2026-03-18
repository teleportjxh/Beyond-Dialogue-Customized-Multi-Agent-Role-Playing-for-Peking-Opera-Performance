import os
import json
import copy
import time
import random
import re
import argparse
import openai
from langchain.llms.base import LLM
from typing import Optional, List, Dict, Any

# 自定义LLM类（未修改）
class CustomOpenAILLM(LLM):
    api_key: str
    base_url: str
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 10000

    @property
    def _llm_type(self) -> str:
        return "custom-openai"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=stop
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM调用错误: {str(e)}")
            return "{}"

    def invoke(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return self._call(prompt, stop)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

# 配置参数（新增jingju根目录参数）
parser = argparse.ArgumentParser(description="提取角色信息与对话表演数据")
parser.add_argument('--jingju_root', default="./jingju", help='京剧数据根目录')
parser.add_argument('--enhanced_script_path', default="./jingju/enhanced_script", help='增强剧本目录（相对于根目录）')
parser.add_argument('--character_path', default="./jingju/character", help='角色信息存储目录（相对于根目录）')
parser.add_argument('--character_data_path', default="./jingju/character_data", help='角色对话/表演数据存储目录（相对于根目录）')
parser.add_argument('--judge_temperature', default=0.0, type=float, help='判断模型温度')
parser.add_argument('--error_json_dir', default="./jingju/error_json", help='JSON解析失败文件存储目录')
args = parser.parse_args()

# 初始化LLM（未修改）
def init_custom_llm(temperature=0.2):
    api_key = "sk-uNTaHplU891bjK5tF67eBf24285f4b8689F23c734dF9C9Ea"
    base_url = "https://api.shubiaobiao.cn/v1/"
    
    if not api_key.startswith("sk-"):
        raise ValueError("API Key格式错误！需以'sk-'开头")
    
    return CustomOpenAILLM(
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=5000
    )

extract_llm = init_custom_llm(temperature=0.1)
judge_llm = init_custom_llm(temperature=args.judge_temperature)

# 数据模板（未修改内容生成相关字段）
PERSON_SCRIPT_DATA_TEMPLATE = {
    "id": "", "title": "", "outline": "","age": "", "personality": "", "description": "", 
    "profession": "", "face": "", "makeup": "", "cloth": "", "knowledge": "",
    "expression": False
}

UNIVERSAL_INFO_TEMPLATE = {
    "gender": "", "catchphrases": [], "forbidden": []
}

person_template = {
    "id": "", "name": "",
    "data": {
        "script_data": [],  # 数组存储多剧本信息
        "gender": "", "catchphrases": [], "forbidden": []
    }
}

dialogue_data_template = {
    "id": "", "title": "", "type": "dialogue",
    "role": {
        "bot": {"id": "", "name": "", "age": "", "gender": "", "personality": "", 
                "catchphrases": [], "description": "", "forbidden": [], "knowledge": ""},
        "user": {"name": "", "description": ""}  # 主交互角色（非第三角色）
    },
    "third_role": "",  # 记录第三角色（若有）
    "scene": "", "tags": [], "relation": "",
    "messages": [{"role": "", "content": ""}],  # 连续对话内容
    "source": "llm",
    "judgment": {"is_valid": True, "reason": ""}
}

performance_data_template = {
    "id": "", "title": "", "type": "performance",
    "role": {
        "bot": {"id": "", "name": "", "age": "", "gender": "", "personality": "", 
                "catchphrases": [], "description": "", "forbidden": [], "knowledge": ""}
    },
    "scene": "", "tags": [], "relation": "", 
    "messages": [{"role": "", "content": ""}],  # 连续表演内容
    "source": "llm",
    "judgment": {"is_valid": True, "reason": ""}
}

# 新增：保存JSON解析失败的内容到本地文件
def save_failed_json(content: str, error_type: str, role_name: str = "", script_title: str = ""):
    """
    保存JSON解析失败的内容到本地文件
    
    Args:
        content: 解析失败的原始内容
        error_type: 错误类型（如"dialogue_extract", "performance_extract", "role_info", "universal_info"等）
        role_name: 角色名称（可选）
        script_title: 剧本标题（可选）
    """
    try:
        # 创建错误JSON存储目录
        os.makedirs(args.error_json_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename_parts = [timestamp, error_type]
        if role_name:
            filename_parts.append(role_name.replace(" ", "_"))
        if script_title:
            filename_parts.append(script_title.replace(" ", "_")[:50])  # 限制长度
        
        filename = "_".join(filename_parts) + ".json"
        filepath = os.path.join(args.error_json_dir, filename)
        
        # 保存内容
        with open(filepath, 'w', encoding='utf-8') as f:
            # 创建包含元数据的JSON结构
            error_data = {
                "timestamp": timestamp,
                "error_type": error_type,
                "role_name": role_name,
                "script_title": script_title,
                "raw_content": content,
                "error_message": "JSON解析失败"
            }
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        print(f"    💾 已保存解析失败的JSON到: {filepath}")
        return filepath
    except Exception as e:
        print(f"    ❌ 保存失败JSON时出错: {str(e)}")
        return None

# 工具函数
def create_dirs():
    print(f"[1/4] 初始化目录结构...")
    # 确保根目录存在
    os.makedirs(args.jingju_root, exist_ok=True)
    # 创建角色信息目录
    os.makedirs(args.character_path, exist_ok=True)
    # 创建角色数据目录
    os.makedirs(args.character_data_path, exist_ok=True)
    # 创建错误JSON存储目录
    os.makedirs(args.error_json_dir, exist_ok=True)
    print(f"  - 京剧根目录: {args.jingju_root}")
    print(f"  - 角色信息目录: {args.character_path}")
    print(f"  - 角色数据目录: {args.character_data_path}")
    print(f"  - 错误JSON目录: {args.error_json_dir}")
    print(f"[1/4] 目录初始化完成\n")

def get_character_id_file_path():
    """获取全局角色ID文件路径（jingju/character_id.txt）"""
    return os.path.join(args.jingju_root, "character_id.txt")

def load_existing_character_ids():
    """加载已存在的角色ID和名称，返回字典{id: 角色名}"""
    id_file = get_character_id_file_path()
    if not os.path.exists(id_file):
        return {}
    try:
        with open(id_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        id_map = {}
        for line in lines:
            # 格式：编号 角色名（空格分隔）
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and parts[0].isdigit():
                char_id = parts[0]
                char_name = parts[1]
                id_map[char_id] = char_name
        return id_map
    except Exception as e:
        print(f"加载角色ID文件失败: {str(e)}，将重新创建")
        return {}

def get_unique_character_id(role_name):
    """获取角色唯一ID：已存在则返回对应ID，否则生成新ID（最大ID+1）"""
    id_map = load_existing_character_ids()
    
    # 检查角色名是否已存在
    for char_id, name in id_map.items():
        if name == role_name:
            return char_id
    
    # 生成新ID（最大ID+1）
    existing_ids = [int(id) for id in id_map.keys() if id.isdigit()]
    max_id = max(existing_ids) if existing_ids else 0
    new_id = str(max_id + 1)
    
    # 写入文件（追加新行）
    id_file = get_character_id_file_path()
    with open(id_file, 'a', encoding='utf-8') as f:
        f.write(f"{new_id} {role_name}\n")
    
    return new_id

import re

def clean_json_response(raw_content):
    if not raw_content:
        return "[]"
    
    # 1. 移除代码块标记（```json 或 ```）
    cleaned = re.sub(r'^```json\s*', '', raw_content, flags=re.MULTILINE)
    cleaned = re.sub(r'```\s*$', '', cleaned, flags=re.MULTILINE)
    
    return cleaned

def safe_json_loads(json_str, error_type, role_name, script_title):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e1:
        try:
            cleaned = clean_json_response(json_str)
            return json.loads(cleaned)
        except json.JSONDecodeError as e2:
            try:
                repaired = re.sub(r'}{', '},{', cleaned)
                return json.loads(repaired)
            except:
                print(f"JSON解析失败: {str(e2)}, 原始内容: {json_str[:100]}")
                save_failed_json(cleaned, error_type, role_name, script_title)
                return []
    except Exception as e:
        print(f"JSON处理异常: {str(e)}")
        return []


def validate_and_supplement_json(json_data, template):
    def escape_string_values(data):
        """递归转义字符串中的双引号"""
        if isinstance(data, dict):
            return {k: escape_string_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [escape_string_values(item) for item in data]
        elif isinstance(data, str):
            # 将字符串中的双引号转义
            return data.replace('"', '\\"')
        else:
            return data
    
    for key in template:
        if key not in json_data:
            json_data[key] = copy.deepcopy(template[key])
    
    # 对所有字符串值进行转义处理
    return escape_string_values(json_data)

def deduplicate_items(items):
    seen = set()
    unique_items = []
    for item in items:
        if isinstance(item, dict) and "role" in item and "content" in item:
            key = f"{item['role']}||{item['content'][:100]}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
    return unique_items

def extract_marked_roles(script_content):
    role_pattern = r'\*\*(.*?)\*\*'
    roles = re.findall(role_pattern, script_content)
    return list(set([role.strip() for role in roles if role.strip()]))

# 对话抽取（未修改内容生成逻辑）
def llm_extract_dialogues(role_name, script_content, script_title):
    all_marked_roles = extract_marked_roles(script_content)
    roles_str = ", ".join(all_marked_roles) if all_marked_roles else "其他带**标记的角色"
    
    correct_example = '''[
{"role":"赵云","content":"(白) 丞相，司马懿大军已至城下！[单膝跪地，语气急切。]"},
{"role":"诸葛亮","content":"(白) 老将军莫慌，传令下去，大开城门。[羽扇轻摇，神态镇定。]"},
{"role":"马谡","content":"(白) 丞相不可！此乃空城，司马懿进城必败！[快步上前，抱拳劝阻。]"},
{"role":"诸葛亮","content":"(白) 幼常多虑，司马懿生性多疑，必不进城。[目光坚定，挥手示意马谡退下。]"}
]'''
    
    prompt = (
        "任务：从以下剧本中提取【包含" + role_name + "的完整对话】，需覆盖多角色交互场景，严格按示例格式返回JSON数组！\n\n"
        "### 核心要求：\n"
        "1. 对话需完整：包含" + role_name + "与其他角色的交互，若有第三角色介入需完整记录\n"
        "2. 角色区分：明确标注每个台词的角色名（如示例中的赵云、诸葛亮、马谡）\n"
        "3. 排除表演内容：仅保留(白)/(念)，排除(唱)/(西皮)/(二黄)\n\n"
        "### 格式要求：\n"
        "每个对话对象为：{\"role\":\"角色名\",\"content\":\"(白) 台词[动作描写]\"}\n\n"
        "### 多角色交互示例：\n" + correct_example + "\n"
        "（示例中马谡为第三角色，介入诸葛亮与赵云的对话）\n\n"
        "### 剧本内容：\n" + script_content[0:5000] + "\n\n"
        "### 输出：输出前请检查输出的文字，确保其符号符合json格式，仅返回JSON数组，无多余文字"
    )
    
    try:
        raw_content = extract_llm.invoke(prompt)
        # 调用safe_json_loads时添加错误类型、角色名和剧本标题
        result = safe_json_loads(raw_content, "dialogue_extract", role_name, script_title)
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict) 
                    and "role" in item and item["role"].strip() 
                    and "content" in item 
                    and (item["role"] == role_name or any(
                        r["role"] == role_name for r in result if isinstance(r, dict) and "role" in r
                    ))]
        return []
    except Exception as e:
        print(f"    ❌ LLM对话抽取失败：{str(e)}")
        # 保存失败的内容
        save_failed_json(str(e), "dialogue_extract_error", role_name, script_title)
        return []

# 表演抽取（未修改内容生成逻辑）
def llm_extract_performances(role_name, script_content, script_title):
    correct_example = '''[
{"role":"诸葛亮","content":"(唱) [西皮慢板]我本是卧龙岗散淡的人，[轻摇羽扇，目光远眺，神情悠然自得。](昔日隐居山林，不问世事，如今却身负重任，此情此景，不禁追忆往昔)论阴阳如反掌保定乾坤。[羽扇收回至胸前，双手轻握扇柄，向城外作揖，眼神坚定。](天机在握，运筹帷幄之中，决胜千里之外)先帝爷下南阳御驾三请，[右手持扇指向台左方向，双手合一，再三作揖，头部微微颔首。](感念刘备三顾之情)算就了汉家业鼎足三分。[左手呈单指状轻晃，感慨天下局势。]"}
]'''
    
    prompt = (
        "任务：从以下剧本中提取【" + role_name + "的完整连续表演】，严格按示例格式返回JSON数组！\n\n"
        "### 核心要求：\n"
        "1. 表演需连续完整：从" + role_name + "开始表演，到其他角色对话/表演前结束\n"
        "2. 元素完整：包含(唱)标注、[板式]、唱词、[动作描写]、(内心独白)\n\n"
        "### 格式要求：\n"
        "{\"role\":\"角色名\",\"content\":\"(唱) [板式]唱词[动作](内心独白)...完整内容\"}\n\n"
        "### 连续表演示例：\n" + correct_example + "\n\n"
        "### 剧本内容：\n" + script_content[0:5000] + "\n\n"
        "### 输出：输出前请检查输出内容，确保其符号符合json格式，仅返回JSON数组，无多余文字"
    )
    
    try:
        raw_content = extract_llm.invoke(prompt)
        print(raw_content)
        # 调用safe_json_loads时添加错误类型、角色名和剧本标题
        result = safe_json_loads(raw_content, "performance_extract", role_name, script_title)
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict) 
                    and "role" in item and item["role"] == role_name 
                    and "content" in item and item["content"].startswith("(唱)")]
        return []
    except Exception as e:
        print(f"    ❌ LLM表演抽取失败：{str(e)}")
        # 保存失败的内容
        save_failed_json(str(e), "performance_extract_error", role_name, script_title)
        return []

# 对话有效性判断（未修改内容生成逻辑）
def judge_dialogue_validity(role_name, dialogue_group,script_title):
    roles_in_group = list(set([item["role"] for item in dialogue_group if isinstance(item, dict) and "role" in item]))
    prompt = (
        "任务：判断以下对话组是否有效，仅返回JSON！\n"
        "有效标准：\n"
        "1. 格式正确：包含(白)/(念)、台词、[动作描写]\n"
        "2. 包含" + role_name + "：至少有一句是" + role_name + "的台词\n"
        "3. 连续性：角色交互自然（允许第三角色介入，但需完整）\n"
        "4. 无表演内容：不含(唱)/(西皮)/(二黄)\n"
        "对话组角色：" + ",".join(roles_in_group) + "\n"
        "对话组：" + json.dumps(dialogue_group, ensure_ascii=False) + "\n"
        "输出格式：{\"is_valid\":true/false,\"reason\":\"判断依据（说明是否含第三角色及连续性）\"}"
    )
    
    try:
        raw_judgment = judge_llm.invoke(prompt)
        # 调用safe_json_loads时添加错误类型和角色名
        judgment = safe_json_loads(raw_judgment, "dialogue_judgment", role_name,script_title)
        return judgment.get("is_valid", False), judgment.get("reason", "未获取依据")
    except Exception as e:
        error_msg = f"判断出错：{str(e)}"
        print(f"    ❌ {error_msg}")
        # 保存失败的内容
        save_failed_json(error_msg, "dialogue_judgment_error", role_name)
        return False, error_msg

# 表演有效性判断（未修改内容生成逻辑）
def judge_performance_validity(role_name, performance_content,script_title):
    prompt = (
        "任务：判断以下表演是否有效，仅返回JSON！\n"
        "有效标准：\n"
        "1. 格式正确：包含(西皮)(二黄)(唱)、[板式]\n"
        "2. 连续性：是" + role_name + "的完整表演（无其他角色介入）\n"
        "3. 长度达标：内容不少于20字符\n"
        "表演内容：" + performance_content + "\n"
        "输出格式：{\"is_valid\":true/false,\"reason\":\"判断依据\"}"
    )
    
    try:
        raw_judgment = judge_llm.invoke(prompt)
        # 调用safe_json_loads时添加错误类型和角色名
        judgment = safe_json_loads(raw_judgment, "performance_judgment", role_name,script_title)
        return judgment.get("is_valid", False), judgment.get("reason", "未获取依据")
    except Exception as e:
        error_msg = f"判断出错：{str(e)}"
        print(f"    ❌ {error_msg}")
        # 保存失败的内容
        save_failed_json(error_msg, "performance_judgment_error", role_name)
        return False, error_msg

# 提取角色信息（仅调整script_data的id和title顺序，不修改内容生成）
def extract_single_script_info(script_content, script_title, role_name, script_id):
    print(f"    提取《{script_title}》中{role_name}的信息...")
    
    prompt = (
        "任务：提取剧本中【" + role_name + "】的信息，以及该剧本的剧情大纲,仅返回JSON字典！\n\n"
        "### 格式要求：\n"
        "1. 仅返回JSON字典，无多余文字\n"
        "2. 必须包含键：outline,age, personality, description, profession, face, makeup, cloth, knowledge\n"
        "下面是部分字段的解释"
        "outline: 该剧本剧情大纲"
        "age: 人物在该剧本下的年龄"
        "personality:人物在该剧本下的个性"
        "description:人物在该剧本下的描述"
        "profession:行当"
        "face:脸谱特征"
        "makeup:妆容细节"
        "cloth:服饰与头饰"
        "knowledge:该角色在该剧本下对于剧情的认知"
        "示例：{\"outline\":三国时期，蜀汉丞相诸葛亮因错用马谡而失守街亭，导致魏国大都督司马懿率四十万大军直逼兵力空虚的西城。危急关头，诸葛亮无法迎战亦无路可退，遂设下空城计。他命人将四门大开，派老军洒扫街道，自己则携二琴童登上城楼，焚香抚琴，神态自若。司马懿兵临城下，见此情景疑心大起，又闻琴声安闲沉稳，断定城内必有伏兵，不敢贸然进击，最终下令大军后撤。诸葛亮借此良机调来赵云驰援，成功化解西城之危，并决意待马谡回营后严明军纪。\"age\":\"老年\",\"personality\":\"沉稳多谋\",\"description\":\"蜀汉丞相，善用计谋\",\"profession\":\"老生(文官，帅才)\",\"face\":\"面部为传统俊扮，不勾画脸谱，以素面突显其儒雅与智慧。额头中央勾一红色额色(有时为太极图样)，象征其忠义之心与运筹帷幄的道家智慧。眉眼细长，目光如炬，于沉稳中透出锐利。\",\"makeup\":\"脸施淡赭色底彩，显得清癯而有神采。口鼻轮廓清晰，唇色淡红。吊眉，以增强眼神的凝聚力。髯口为黑白相间的三绺长须，垂至胸前，象征其年事已高、阅历深厚\",\"cloth\":\"头戴软方巾或诸葛巾，象征其文士身份。身着最为经典的八卦衣(鹤氅)，衣上绣有太极与八卦图案，边缘饰以白色羽毛，尽显其飘逸出尘、通晓阴阳的智者风范。手持白色鹅毛扇，为其标志性道具，用以指挥、思考与表达情绪。足蹬厚底靴。\",\"knowledge\":\"精通兵法\"}\n\n"
        "### 剧本内容：\n" + script_content[:5000] + "\n\n"
        "### 输出：输出前请检查输出的文字，其输出的json字段的内容中不能具有引号，确保其符号符合json格式，仅返回JSON数组，无多余文字"
    )
    
    try:
        raw_content = extract_llm.invoke(prompt)
        # 调用safe_json_loads时添加错误类型、角色名和剧本标题
        parsed_data = safe_json_loads(raw_content, "role_info_extract", role_name, script_title)
        if not isinstance(parsed_data, dict):
            print(f"    ⚠️ 角色信息格式错误，使用默认值")
            # 保存格式错误的内容
            save_failed_json(raw_content, "role_info_format_error", role_name, script_title)
            # 强制id和title在最前
            base_info = {"id": script_id, "title": script_title}
            for key in PERSON_SCRIPT_DATA_TEMPLATE:
                if key not in ["id", "title"]:
                    base_info[key] = copy.deepcopy(PERSON_SCRIPT_DATA_TEMPLATE[key])
        else:
            # 强制id和title在最前，其他字段按模板补充
            base_info = {"id": script_id, "title": script_title}
            for key in PERSON_SCRIPT_DATA_TEMPLATE:
                if key not in ["id", "title"]:
                    value = parsed_data.get(key, copy.deepcopy(PERSON_SCRIPT_DATA_TEMPLATE[key]))
                    # 如果是字符串类型，确保双引号被正确转义
                    if isinstance(value, str):
                        # 将字符串中的双引号转义
                        value = value.replace('"', '\\"')
                    base_info[key] = value
        
        return base_info
    except Exception as e:
        print(f"    ❌ 提取失败：{str(e)}")
        # 保存失败的内容
        save_failed_json(str(e), "role_info_extract_error", role_name, script_title)
        base_info = {"id": script_id, "title": script_title}
        for key in PERSON_SCRIPT_DATA_TEMPLATE:
            if key not in ["id", "title"]:
                base_info[key] = copy.deepcopy(PERSON_SCRIPT_DATA_TEMPLATE[key])
        return base_info

# 更新通用信息（未修改内容生成逻辑）
def update_universal_info(role_name, new_script, current_universal):
    print(f"    基于《{new_script['title']}》更新通用信息...")
    
    prompt = (
        "任务：更新【" + role_name + "】的通用信息，仅返回JSON字典！\n\n"
        "### 格式要求：\n"
        "1. 仅返回JSON字典，无多余文字\n"
        "2. 必须包含键：gender（字符串）, catchphrases（数组）, forbidden（数组）\n"
        "下面是字段的解释"
        "gender:性别"
        "catchphrases:人物口头禅"
        "forbidden:人物禁忌(不会干的事情)"
        "示例：{\"gender\":\"男\",\"catchphrases\":[\"臣\"],\"forbidden\":[\"泄露军情\"]}\n\n"
        "### 历史信息：\n" + json.dumps(current_universal, ensure_ascii=False) + "\n\n"
        "### 新剧本内容：\n" + new_script["content"][:5000] + "\n\n"
        "### 输出：输出前请检查输出的文字，其输出的json字段的内容中不能具有引号，确保其符号符合json格式，仅返回JSON数组，无多余文字"
    )
    
    try:
        raw_content = extract_llm.invoke(prompt)
        # 调用safe_json_loads时添加错误类型、角色名和剧本标题
        parsed_data = safe_json_loads(raw_content, "universal_info_update", role_name, new_script["title"])
        # save_failed_json(parsed_data, "parsed_data", role_name, new_script["title"])
        if not isinstance(parsed_data, dict):
            print(f"    ⚠️ 通用信息格式错误，保留历史信息")
            # 保存格式错误的内容
            save_failed_json(raw_content, "universal_info_format_error", role_name, new_script["title"])
            return current_universal
        
        return validate_and_supplement_json(parsed_data, UNIVERSAL_INFO_TEMPLATE)
    except Exception as e:
        print(f"    ❌ 更新失败，保留历史信息：{str(e)}")
        # 保存失败的内容
        save_failed_json(str(e), "universal_info_update_error", role_name, new_script["title"])
        return current_universal

# 对话组拆分（未修改内容生成逻辑）
def split_dialogue_performance(script_content, role_name, script_title):
    print(f"    抽取《{script_title}》中{role_name}的对话和表演数据...")
    
    # 抽取连续对话
    print("    【第一阶段】使用LLM抽取连续对话...")
    llm_dialogues = llm_extract_dialogues(role_name, script_content, script_title)
    print(f"    LLM抽取到{len(llm_dialogues)}条对话轮次")
    
    # 抽取连续表演
    print("    【第二阶段】使用LLM抽取连续表演...")
    llm_performances = llm_extract_performances(role_name, script_content, script_title)
    print(f"    LLM抽取到{len(llm_performances)}条表演片段")
    
    # 对话去重（保留连续完整性）
    all_dialogue_turns = deduplicate_items(llm_dialogues)
    if not all_dialogue_turns:
        return {"dialogues": [], "performances": []}
    
    # 组合对话组（核心逻辑：第三角色介入时拆分）
    print("    【第三阶段】组合对话组（支持多角色拆分）...")
    dialogue_groups = []
    current_group = [all_dialogue_turns[0]]  # 初始化第一个对话组
    # 记录当前对话组的核心角色（目标角色+首个交互角色）
    core_roles = {role_name, all_dialogue_turns[0]["role"]}
    if role_name in core_roles:
        core_roles.discard(role_name)  # 确保核心角色为：目标角色 + 主交互角色
    
    for turn in all_dialogue_turns[1:]:
        current_role = turn["role"]
        
        # 场景1：当前角色是核心角色 → 继续加入当前组
        if current_role in core_roles or current_role == role_name:
            current_group.append(turn)
        
        # 场景2：当前角色是新角色（第三角色）
        else:
            # 保存当前组（如果有效）
            if len(current_group) >= 2:
                is_valid, reason = judge_dialogue_validity(role_name, current_group,script_title)
                if is_valid:
                    dialogue_groups.append({
                        "group": current_group,
                        "source": "llm",
                        "judgment": {"is_valid": True, "reason": reason}
                    })
            
            # 以第三角色创建新对话组，核心角色更新为：目标角色 + 第三角色
            current_group = [turn]
            core_roles = {role_name, current_role}
    
    # 处理最后一个对话组
    if len(current_group) >= 2:
        is_valid, reason = judge_dialogue_validity(role_name, current_group,script_title)
        if is_valid:
            dialogue_groups.append({
                "group": current_group,
                "source": "llm",
                "judgment": {"is_valid": True, "reason": reason}
            })
    
    print(f"    有效对话组：{len(dialogue_groups)}组（含多角色拆分）")
    
    # 处理连续表演片段
    print("    【第四阶段】判断连续表演片段有效性...")
    valid_performances = []
    seen_perfs = set()
    for perf in llm_performances:
        content = perf.get("content", "").strip()
        if not content or content in seen_perfs or len(content) < 30:
            continue
        seen_perfs.add(content)
        
        if any(tag in content for tag in ["(唱)", "(西皮)", "(二黄)"]):
            is_valid, reason = judge_performance_validity(role_name, content,script_title)
            if is_valid:
                valid_performances.append({
                    "content": content,
                    "source": "llm",
                    "judgment": {"is_valid": True, "reason": reason}
                })
    
    print(f"    有效连续表演片段：{len(valid_performances)}条")
    
    return {
        "dialogues": dialogue_groups,
        "performances": valid_performances
    }

# 主流程（仅调整ID相关逻辑，不修改内容生成）
def main():
    start_time = time.time()
    create_dirs()
    
    # 收集剧本路径（未修改）
    print(f"[2/4] 收集所有剧本路径...")
    role_scripts = {}
    total_scripts = 0
    
    if not os.path.exists(args.enhanced_script_path):
        print(f"错误：剧本目录不存在 → {args.enhanced_script_path}")
        return
    
    for role_name in os.listdir(args.enhanced_script_path):
        role_dir = os.path.join(args.enhanced_script_path, role_name)
        if not os.path.isdir(role_dir):
            continue
        
        script_files = [f for f in os.listdir(role_dir) if f.lower().endswith(".txt")]
        if not script_files:
            print(f"  角色【{role_name}】无txt剧本，跳过")
            continue
        
        total_scripts += len(script_files)
        role_scripts[role_name] = [
            {"title": os.path.splitext(f)[0], "path": os.path.join(role_dir, f)}
            for f in script_files
        ]
        print(f"  发现角色【{role_name}】，包含{len(script_files)}个剧本")
    
    if not role_scripts:
        print(f"[2/4] 未找到可用角色和剧本！")
        return
    print(f"[2/4] 剧本收集完成，共{len(role_scripts)}个角色，{total_scripts}个剧本\n")
    
    # 处理角色信息和数据
    print(f"[3/4] 处理角色信息和数据...")
    for role_idx, (role_name, scripts) in enumerate(role_scripts.items(), 1):
        print(f"\n===== 处理角色 {role_idx}/{len(role_scripts)}：{role_name} =====")
        role_start_time = time.time()
        
        # 角色信息存储目录（jingju/character/角色名）
        char_dir = os.path.join(args.character_path, role_name)
        os.makedirs(char_dir, exist_ok=True)
        profile_path = os.path.join(char_dir, "profile.json")
        
        # 角色数据存储目录（jingju/character_data/角色名）
        char_data_dir = os.path.join(args.character_data_path, role_name)
        os.makedirs(char_data_dir, exist_ok=True)
        data_path = os.path.join(char_data_dir, "data.json")
        
        all_data = []
        data_id = 1
        
        # 获取角色唯一ID（从jingju/character_id.txt读取或生成）
        char_id = get_unique_character_id(role_name)
        print(f"    角色唯一ID：{char_id}")
        
        # 加载现有profile（仅调整ID和script_data顺序）
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                # 处理script_data：若为字典则转为数组
                if isinstance(profile["data"]["script_data"], dict):
                    profile["data"]["script_data"] = [profile["data"]["script_data"]]
                # 修复历史数据：确保id和title在最前
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
                # 保存格式错误的内容
                save_failed_json(str(e), "profile_load_error", role_name)
                profile = copy.deepcopy(person_template)
                profile["id"] = char_id
                profile["name"] = role_name
                current_universal = copy.deepcopy(UNIVERSAL_INFO_TEMPLATE)
                existing_script_ids = []
        else:
            profile = copy.deepcopy(person_template)
            profile["id"] = char_id
            profile["name"] = role_name
            current_universal = copy.deepcopy(UNIVERSAL_INFO_TEMPLATE)
            existing_script_ids = []
        
        # 处理每个剧本（仅调整剧本ID逻辑）
        for script_idx, script in enumerate(scripts, 1):
            script_title = script["title"]
            script_path = script["path"]
            script_id = str(script_idx)  # 剧本内角色编号（按剧本顺序）
            
            if script_id in existing_script_ids:
                print(f"\n  剧本 {script_idx}/{len(scripts)}：《{script_title}》已处理，跳过")
                continue
            
            print(f"\n  处理剧本 {script_idx}/{len(scripts)}：《{script_title}》")
            
            # 读取剧本内容（未修改）
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                print(f"    ✅ 成功读取剧本（{len(script_content)}字符）")
                if "**" not in script_content:
                    print(f"    ⚠️ 剧本无**角色标记，跳过此剧本")
                    continue
            except Exception as e:
                print(f"    ❌ 读取失败：{str(e)}，跳过")
                # 保存读取失败的信息
                save_failed_json(str(e), "script_read_error", role_name, script_title)
                continue
            
            # 提取单剧本信息（未修改内容生成）
            single_script_info = extract_single_script_info(
                script_content=script_content,
                script_title=script_title,
                role_name=role_name,
                script_id=script_id
            )
            
            # 更新通用信息（未修改内容生成）
            current_universal = update_universal_info(
                role_name=role_name,
                new_script={"title": script_title, "content": script_content},
                current_universal=current_universal
            )
            print(f"    更新后通用信息：{json.dumps(current_universal, ensure_ascii=False)}")
            
            # 追加剧本信息到profile（未修改）
            profile["data"]["script_data"].append(single_script_info)
            profile["data"]["gender"] = current_universal["gender"]
            profile["data"]["catchphrases"] = current_universal["catchphrases"]
            profile["data"]["forbidden"] = current_universal["forbidden"]
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            print(f"    已保存角色信息（累计{len(profile['data']['script_data'])}个剧本）")
            
            # 抽取连续对话和表演（未修改内容生成）
            split_data = split_dialogue_performance(script_content, role_name, script_title)
            
            # 处理对话数据（未修改内容生成）
            for dialog in split_data["dialogues"]:
                dialog_entry = copy.deepcopy(dialogue_data_template)
                dialog_entry["id"] = str(data_id)
                dialog_entry["title"] = script_title
                dialog_entry["role"]["bot"] = {
                    "id": profile["id"],
                    "name": role_name,
                    "outline":single_script_info["outline"],
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
            
            # 处理表演数据（未修改内容生成）
            for perf in split_data["performances"]:
                perf_entry = copy.deepcopy(performance_data_template)
                perf_entry["id"] = str(data_id)
                perf_entry["title"] = script_title
                perf_entry["role"]["bot"] = {
                    "id": profile["id"],
                    "name": role_name,
                    "outline":single_script_info["outline"],
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
            
            print(f"    已处理《{script_title}》，累计{len(all_data)}条有效数据")
        
        # 保存角色所有数据（未修改）
        try:
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"    ❌ 保存角色数据失败: {str(e)}")
            # 保存保存失败的信息
            save_failed_json(str(e), "data_save_error", role_name)
        
        role_time = time.time() - role_start_time
        print(f"\n===== 角色【{role_name}】处理完成，耗时{role_time:.2f}秒 =====")
    
    total_time = time.time() - start_time
    print(f"\n[4/4] 所有处理完成！总耗时{total_time:.2f}秒")
    # 检查是否有错误JSON文件
    if os.path.exists(args.error_json_dir) and len(os.listdir(args.error_json_dir)) > 0:
        print(f"⚠️  注意：有{len(os.listdir(args.error_json_dir))}个JSON解析失败文件已保存到 {args.error_json_dir}")

if __name__ == "__main__":
    main()
