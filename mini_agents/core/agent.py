"""Agent base class"""

from abc import ABC, abstractmethod
from typing import Optional

from .message import Message
from .llm import MiniAgentsLLM
from .config import Config


class Agent(ABC):
    """Base class for agents"""

    def __init__(
        self,
        name: str,
        llm: MiniAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config
        self._history: list[Message] = []

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """Run agent"""
        pass

    def add_to_history(self, message: Message):
        """Add message to history"""
        self._history.append(message)

    def clear_history(self):
        """Clear history"""
        self._history = []

    def get_history(self) -> list[Message]:
        """Get history"""
        return self._history.copy()
    
    def __str__(self):
        return f"Agent(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()



