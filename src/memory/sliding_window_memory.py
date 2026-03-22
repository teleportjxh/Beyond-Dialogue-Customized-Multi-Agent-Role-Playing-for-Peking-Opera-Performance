"""
滑动窗口短期记忆
保留最近N轮对话，超出窗口的消息自动摘要压缩
"""
from typing import List, Dict, Optional
from datetime import datetime


class SlidingWindowMemory:
    """
    滑动窗口短期记忆
    
    - 保留最近 window_size 条消息
    - 超出窗口的消息生成摘要存入 summary
    - 支持按角色过滤消息
    """
    
    def __init__(self, window_size: int = 10):
        """
        Args:
            window_size: 滑动窗口大小（保留的最近消息数）
        """
        self.window_size = window_size
        self.messages: List[Dict] = []
        self.summary: str = ""  # 超出窗口的消息摘要
        self._overflow_buffer: List[Dict] = []  # 溢出缓冲区
    
    def add(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        添加一条消息到记忆
        
        Args:
            role: 消息角色 ("user"/"assistant"/"system"/"character_name")
            content: 消息内容
            metadata: 附加元数据（如场景编号、情绪等）
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.messages.append(message)
        
        # 如果超出窗口大小，将最早的消息移入溢出缓冲区
        while len(self.messages) > self.window_size:
            overflow_msg = self.messages.pop(0)
            self._overflow_buffer.append(overflow_msg)
            
            # 当溢出缓冲区积累到一定量时，生成摘要
            if len(self._overflow_buffer) >= 5:
                self._compress_overflow()
    
    def get_context(self) -> List[Dict]:
        """
        获取当前窗口内的消息上下文
        
        Returns:
            消息列表，格式为 [{"role": str, "content": str}, ...]
        """
        context = []
        
        # 如果有摘要，先添加摘要作为系统消息
        if self.summary:
            context.append({
                'role': 'system',
                'content': f"[之前的对话摘要]\n{self.summary}"
            })
        
        # 添加窗口内的消息
        for msg in self.messages:
            context.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        return context
    
    def get_context_string(self) -> str:
        """获取上下文的字符串形式"""
        parts = []
        
        if self.summary:
            parts.append(f"[之前的对话摘要] {self.summary}")
        
        for msg in self.messages:
            role = msg['role']
            content = msg['content']
            parts.append(f"[{role}] {content}")
        
        return "\n".join(parts)
    
    def get_messages_by_role(self, role: str) -> List[Dict]:
        """按角色过滤消息"""
        return [msg for msg in self.messages if msg['role'] == role]
    
    def get_last_n(self, n: int) -> List[Dict]:
        """获取最近n条消息"""
        return self.messages[-n:] if n <= len(self.messages) else self.messages[:]
    
    def _compress_overflow(self):
        """压缩溢出缓冲区为摘要"""
        if not self._overflow_buffer:
            return
        
        # 简单摘要：提取关键信息
        overflow_summary_parts = []
        for msg in self._overflow_buffer:
            role = msg['role']
            content = msg['content'][:100]  # 截取前100字
            overflow_summary_parts.append(f"{role}: {content}")
        
        new_summary = "；".join(overflow_summary_parts)
        
        if self.summary:
            # 合并旧摘要和新摘要，保持总长度可控
            self.summary = f"{self.summary[:500]}；{new_summary}"
        else:
            self.summary = new_summary
        
        # 清空溢出缓冲区
        self._overflow_buffer.clear()
    
    def set_summary(self, summary: str):
        """手动设置摘要（可由LLM生成更好的摘要）"""
        self.summary = summary
    
    def clear(self):
        """清空所有记忆"""
        self.messages.clear()
        self._overflow_buffer.clear()
        self.summary = ""
    
    def get_stats(self) -> Dict:
        """获取记忆统计信息"""
        return {
            'window_size': self.window_size,
            'current_messages': len(self.messages),
            'has_summary': bool(self.summary),
            'summary_length': len(self.summary),
            'overflow_buffer_size': len(self._overflow_buffer)
        }
