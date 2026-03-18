"""
Agent基类 - 定义所有Agent的通用接口和功能
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from src.config import Config


class AgentBase:
    """Agent基类，所有Agent都继承此类"""
    
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        temperature: float = 0.7,
        model_name: Optional[str] = None
    ):
        """
        初始化Agent
        
        Args:
            name: Agent名称
            role: Agent角色（actor/director/screenwriter）
            system_prompt: 系统提示词
            temperature: 温度参数
            model_name: 模型名称，默认使用配置中的模型
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.model_name = model_name or Config.MODEL_NAME
        
        # 初始化LLM客户端
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
            max_tokens=Config.MAX_TOKENS
        )
        
        # 消息历史
        self.message_history: List[Dict[str, str]] = []
        
        # Agent状态
        self.state: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.message_history.append({
            "role": role,
            "content": content
        })
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取完整的消息历史（包含系统提示）"""
        return [
            {"role": "system", "content": self.system_prompt}
        ] + self.message_history
    
    def clear_history(self):
        """清空消息历史"""
        self.message_history = []
    
    def generate_response(self, user_input: str) -> str:
        """
        生成响应
        
        Args:
            user_input: 用户输入
            
        Returns:
            Agent的响应
        """
        # 添加用户消息
        self.add_message("user", user_input)
        
        # 调用LLM
        messages = self.get_messages()
        response = self.llm.invoke(messages)
        
        # 提取响应内容
        response_content = response.content
        
        # 添加助手响应到历史
        self.add_message("assistant", response_content)
        
        return response_content
    
    def update_state(self, key: str, value: Any):
        """更新Agent状态"""
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取Agent状态"""
        return self.state.get(key, default)
    
    def reset(self):
        """重置Agent状态"""
        self.clear_history()
        self.state = {}
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', role='{self.role}')"
