"""Configurations for Mini-Agents, including LLM settings and system parameters."""

from typing import Optional
from pydantic import BaseModel

class Config(BaseModel):
    # LLM configure
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    # System configure
    debug: bool = False
    log_level: str = "INFO"

    # Others
    max_history_length: int = 100