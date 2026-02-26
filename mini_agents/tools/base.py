"""Tool base class"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None

class Tool(ABC):
    def __init__(self, name: str, description: str, expandable: bool = False):
        self.name = name
        self.description = description
        self.expandable = expandable
    
    @abstractmethod
    def run(self, parameters: dict[str, Any]) -> str:
        """Run the tool"""
        pass

    @abstractmethod
    def get_parameters(self) -> list[ToolParameter]:
        """Get the parameters for the tool"""
        pass