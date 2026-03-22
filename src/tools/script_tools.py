"""
剧本工具 - JSON解析和剧本格式化工具
"""
import json
import re
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class ParseJSONInput(BaseModel):
    """JSON解析输入"""
    text: str = Field(..., description="包含JSON的文本内容")


class ParseJSONTool(BaseTool):
    """JSON解析工具 - 从LLM响应中提取并解析JSON"""
    name: str = "parse_json"
    description: str = (
        "从LLM生成的文本中提取并解析JSON内容。"
        "能处理被markdown代码块包裹的JSON，以及混合文本中的JSON。"
    )
    args_schema: Type[BaseModel] = ParseJSONInput
    
    def _run(self, text: str) -> str:
        """解析JSON"""
        try:
            # 尝试直接解析
            result = json.loads(text)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass
        
        # 尝试从markdown代码块中提取
        if '```json' in text:
            try:
                json_str = text.split('```json')[1].split('```')[0].strip()
                result = json.loads(json_str)
                return json.dumps(result, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, IndexError):
                pass
        
        if '```' in text:
            try:
                json_str = text.split('```')[1].split('```')[0].strip()
                result = json.loads(json_str)
                return json.dumps(result, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, IndexError):
                pass
        
        # 尝试提取花括号内容
        try:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                result = json.loads(json_match.group())
                return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取方括号内容（JSON数组）
        try:
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                result = json.loads(json_match.group())
                return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass
        
        return json.dumps({"error": "无法解析JSON", "raw_text": text[:500]}, ensure_ascii=False)


class FormatScriptInput(BaseModel):
    """剧本格式化输入"""
    title: str = Field(..., description="剧本标题")
    scenes_text: str = Field(..., description="场景对话的原始文本")


class FormatScriptTool(BaseTool):
    """剧本格式化工具 - 将对话内容格式化为标准京剧剧本"""
    name: str = "format_script"
    description: str = (
        "将原始对话内容格式化为标准的京剧剧本格式，"
        "包括场景标题、出场角色、表演流程等。"
    )
    args_schema: Type[BaseModel] = FormatScriptInput
    
    def _run(self, title: str, scenes_text: str) -> str:
        """格式化剧本"""
        try:
            from src.script_generation.script_formatter import ScriptFormatter
            formatter = ScriptFormatter()
            # 简单格式化
            script = f"## 标题：《{title}》\n\n{scenes_text}"
            return script
        except Exception as e:
            return f"格式化失败: {str(e)}\n\n原始内容:\n{scenes_text}"
