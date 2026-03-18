"""
LLM客户端 - 封装大模型API调用
"""
import openai
from typing import Optional, List, Dict, Any
from langchain_core.language_models.llms import BaseLLM as LLM
from ..config import Config


class CustomOpenAILLM(LLM):
    """自定义OpenAI LLM类"""
    
    api_key: str
    base_url: str
    model_name: str = Config.MODEL_NAME
    temperature: float = Config.EXTRACT_TEMPERATURE
    max_tokens: int = Config.MAX_TOKENS

    @property
    def _llm_type(self) -> str:
        return "custom-openai"

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> Any:
        """生成响应（langchain_core要求的方法）"""
        from langchain_core.outputs import LLMResult, Generation
        
        generations = []
        for prompt in prompts:
            text = self._call_single(prompt, stop)
            generations.append([Generation(text=text)])
        
        return LLMResult(generations=generations)
    
    def _call_single(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """调用LLM API（单个prompt）"""
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
        """调用LLM（兼容接口）"""
        return self._call_single(prompt, stop)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """返回识别参数"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


class LLMClientManager:
    """LLM客户端管理器"""
    
    def __init__(self):
        """初始化LLM客户端"""
        Config.validate_api_key()
        
        self.extract_llm = CustomOpenAILLM(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
            temperature=Config.EXTRACT_TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
        
        self.judge_llm = CustomOpenAILLM(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL,
            temperature=Config.JUDGE_TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
    
    def get_extract_llm(self) -> CustomOpenAILLM:
        """获取提取用LLM"""
        return self.extract_llm
    
    def get_judge_llm(self) -> CustomOpenAILLM:
        """获取判断用LLM"""
        return self.judge_llm
