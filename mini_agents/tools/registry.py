from .base import Tool

class ToolRegistry:
    """Registry for tools that can be used by agents."""
    def __init__(self):
        self._tools: dict[str, Tool] = {}