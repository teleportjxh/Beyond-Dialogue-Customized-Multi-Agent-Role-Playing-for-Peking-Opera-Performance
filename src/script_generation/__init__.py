"""
多Agent剧本生成系统
基于编剧、导演、演员Agent协作生成京剧剧本
"""

from .agent_base import AgentBase
from .context_builder import ContextBuilder
from .costume_designer_agent import CostumeDesignerAgent
from .screenwriter_agent import ScreenwriterAgent
from .actor_agent import ActorAgent
from .director_agent import DirectorAgent
from .dialogue_manager import DialogueManager
from .script_formatter import ScriptFormatter
from .main import ScriptGenerationSystem

__all__ = [
    'AgentBase',
    'ContextBuilder',
    'CostumeDesignerAgent',
    'ScreenwriterAgent',
    'ActorAgent',
    'DirectorAgent',
    'DialogueManager',
    'ScriptFormatter',
    'ScriptGenerationSystem',
]

__version__ = '1.0.0'
