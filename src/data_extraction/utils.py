"""
工具函数 - 提供通用辅助功能
"""
import os
import json
import re
import time
import copy
from typing import Dict, List, Any
from ..config import Config
from .data_models import DataTemplates


class FileManager:
    """文件管理器"""
    
    @staticmethod
    def create_directories():
        """创建所有必要的目录"""
        print(f"[1/4] 初始化目录结构...")
        os.makedirs(Config.JINGJU_ROOT, exist_ok=True)
        os.makedirs(Config.CHARACTER_PATH, exist_ok=True)
        os.makedirs(Config.CHARACTER_DATA_PATH, exist_ok=True)
        os.makedirs(Config.ERROR_JSON_DIR, exist_ok=True)
        print(f"  - 京剧根目录: {Config.JINGJU_ROOT}")
        print(f"  - 角色信息目录: {Config.CHARACTER_PATH}")
        print(f"  - 角色数据目录: {Config.CHARACTER_DATA_PATH}")
        print(f"  - 错误JSON目录: {Config.ERROR_JSON_DIR}")
        print(f"[1/4] 目录初始化完成\n")
    
    @staticmethod
    def save_failed_json(content: str, error_type: str, role_name: str = "", script_title: str = ""):
        """保存JSON解析失败的内容"""
        try:
            os.makedirs(Config.ERROR_JSON_DIR, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename_parts = [timestamp, error_type]
            if role_name:
                filename_parts.append(role_name.replace(" ", "_"))
            if script_title:
                filename_parts.append(script_title.replace(" ", "_")[:50])
            
            filename = "_".join(filename_parts) + ".json"
            filepath = os.path.join(Config.ERROR_JSON_DIR, filename)
            
            error_data = {
                "timestamp": timestamp,
                "error_type": error_type,
                "role_name": role_name,
                "script_title": script_title,
                "raw_content": content,
                "error_message": "JSON解析失败"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)
            
            print(f"    💾 已保存解析失败的JSON到: {filepath}")
            return filepath
        except Exception as e:
            print(f"    ❌ 保存失败JSON时出错: {str(e)}")
            return None


class CharacterIDManager:
    """角色ID管理器"""
    
    @staticmethod
    def load_existing_ids() -> Dict[str, str]:
        """加载已存在的角色ID映射"""
        id_file = Config.get_character_id_path()
        if not os.path.exists(id_file):
            return {}
        
        try:
            with open(id_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            id_map = {}
            for line in lines:
                parts = line.split(maxsplit=1)
                if len(parts) == 2 and parts[0].isdigit():
                    id_map[parts[0]] = parts[1]
            return id_map
        except Exception as e:
            print(f"加载角色ID文件失败: {str(e)}，将重新创建")
            return {}
    
    @staticmethod
    def get_unique_id(role_name: str) -> str:
        """获取角色唯一ID"""
        id_map = CharacterIDManager.load_existing_ids()
        
        for char_id, name in id_map.items():
            if name == role_name:
                return char_id
        
        existing_ids = [int(id) for id in id_map.keys() if id.isdigit()]
        max_id = max(existing_ids) if existing_ids else 0
        new_id = str(max_id + 1)
        
        id_file = Config.get_character_id_path()
        with open(id_file, 'a', encoding='utf-8') as f:
            f.write(f"{new_id} {role_name}\n")
        
        return new_id


class JSONProcessor:
    """JSON处理器"""
    
    @staticmethod
    def clean_json_response(raw_content: str) -> str:
        """清理JSON响应内容"""
        if not raw_content:
            return "[]"
        
        cleaned = re.sub(r'^```json\s*', '', raw_content, flags=re.MULTILINE)
        cleaned = re.sub(r'```\s*$', '', cleaned, flags=re.MULTILINE)
        return cleaned
    
    @staticmethod
    def safe_json_loads(json_str: str, error_type: str, role_name: str, script_title: str):
        """安全的JSON解析"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                cleaned = JSONProcessor.clean_json_response(json_str)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                try:
                    repaired = re.sub(r'}{', '},{', cleaned)
                    return json.loads(repaired)
                except:
                    print(f"JSON解析失败，原始内容: {json_str[:100]}")
                    FileManager.save_failed_json(cleaned, error_type, role_name, script_title)
                    return []
        except Exception as e:
            print(f"JSON处理异常: {str(e)}")
            return []
    
    @staticmethod
    def escape_string_values(data: Any) -> Any:
        """递归转义字符串中的双引号"""
        if isinstance(data, dict):
            return {k: JSONProcessor.escape_string_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [JSONProcessor.escape_string_values(item) for item in data]
        elif isinstance(data, str):
            return data.replace('"', '\\"')
        else:
            return data
    
    @staticmethod
    def validate_and_supplement(json_data: Dict, template: Dict) -> Dict:
        """验证并补充JSON数据"""
        for key in template:
            if key not in json_data:
                json_data[key] = copy.deepcopy(template[key])
        
        return JSONProcessor.escape_string_values(json_data)


class ScriptProcessor:
    """剧本处理器"""
    
    @staticmethod
    def extract_marked_roles(script_content: str) -> List[str]:
        """提取剧本中标记的角色"""
        role_pattern = r'\*\*(.*?)\*\*'
        roles = re.findall(role_pattern, script_content)
        return list(set([role.strip() for role in roles if role.strip()]))
    
    @staticmethod
    def deduplicate_items(items: List[Dict]) -> List[Dict]:
        """去重对话/表演项"""
        seen = set()
        unique_items = []
        for item in items:
            if isinstance(item, dict) and "role" in item and "content" in item:
                key = f"{item['role']}||{item['content'][:100]}"
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
        return unique_items
    
    @staticmethod
    def collect_scripts(enhanced_script_path: str) -> Dict[str, List[Dict]]:
        """收集所有角色的剧本"""
        print(f"[2/4] 收集所有剧本路径...")
        role_scripts = {}
        total_scripts = 0
        
        if not os.path.exists(enhanced_script_path):
            print(f"错误：剧本目录不存在 → {enhanced_script_path}")
            return {}
        
        for role_name in os.listdir(enhanced_script_path):
            role_dir = os.path.join(enhanced_script_path, role_name)
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
        
        if role_scripts:
            print(f"[2/4] 剧本收集完成，共{len(role_scripts)}个角色，{total_scripts}个剧本\n")
        else:
            print(f"[2/4] 未找到可用角色和剧本！\n")
        
        return role_scripts
