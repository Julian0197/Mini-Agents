"""Message handling for Mini-Agents."""

from typing import Literal, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

MessageRole = Literal["user", "assistant", "system"]

class Message(BaseModel):
    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the Message to a OpenAI-format dictionary."""
        return {
            "role": self.role,
            "content": self.content,  
        }

    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"
