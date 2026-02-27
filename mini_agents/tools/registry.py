from .base import Tool
from typing import Any, Callable, Optional

class ToolRegistry:
    """
    Tool registry
    
    Support two modes:
    1. Tool object registration (recommended)
    2. Direct function registration (convenient)
    """
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: Tool, auto_expand: bool = True):
        """Register a tool in the registry.

        Args:
            tool (Tool): The tool to register.
            auto_expand (bool): Whether to automatically expand the tool if it is expandable. Default is True.
        """
        if auto_expand and hasattr(tool, "expandable") and tool.expandable:
            expanded_tools = tool.get_expanded_tools()
            if expanded_tools:
                for sub_tool in expanded_tools:
                    if sub_tool.name in self._tools:
                        print(f"Tool '{sub_tool.name}' is already registered and will be overwritten.")
                    self._tools[sub_tool.name] = sub_tool
                print(f"✅Tool '{tool.name}' is expandable and has been expanded into {len(expanded_tools)} sub-tools.")
                return
            
        if tool.name in self._tools:
            print(f"Tool '{tool.name}' is already registered and will be overwritten.")
        self._tools[tool.name] = tool
        print(f"✅Tool '{tool.name}' has been registered.")

    def register_function(self, name: str, description: str, func: Callable):
        """Register a function in the registry.

        Args:
            name (str): The name of the function.
            description (str): The description of the function.
            func (Callable): The function to register.
        """
        self._functions[name] = {
            "description": description,
            "function": func
        }
        print(f"✅Function '{name}' has been registered.")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get a function by name"""
        func_info = self._functions.get(name)
        return func_info if func_info else None
    
    def unregister(self, name: str):
        """Unregister a tool or function by name"""
        if name in self._tools:
            del self._tools[name]
            print(f"Tool '{name}' has been unregistered.")
        elif name in self._functions:
            del self._functions[name]
            print(f"Function '{name}' has been unregistered.")
        else:
            print(f"No tool or function named '{name}' found to unregister.")

    def execute_tool(self, name: str, input_text: str) -> str:
        """Execute a tool or function by name with the given parameters"""
        if name in self._tools:
            try:
                return self._tools[name].run(input_text)
            except Exception as e:
                return f"Error: executing tool '{name}': {e}"
        elif name in self._functions:
            try:
                func_info = self._functions[name]
                return func_info["function"](input_text)
            except Exception as e:
                return f"Error: executing function '{name}': {e}"
        else:
            return f"Error: No tool or function named '{name}' found to execute."
        
    def get_tools_description(self) -> str:
        """
        Get formatted descriptions for all available tools

        Returns:
            Tool description string, used to build prompts
        """
        descriptions = []
        # Tool descriptions
        for tool in self._tools.values():
            descriptions.append(f"{tool.name}: {tool.description}")
        # Function descriptions
        for name, info in self._functions.items():
            descriptions.append(f"{name}: {info['description']}")
        return "\n".join(descriptions) if descriptions else "No tools or functions registered."
    
    def list_all(self) -> list[str]:
        """List all registered tool and function names"""
        return list(self._tools.keys()) + list(self._functions.keys())
    
    def get_all_tools(self) -> list[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def clear(self):
        """Clear all registered tools and functions"""
        self._tools.clear()
        self._functions.clear()
        print("All tools and functions have been cleared.")
    

# Global tool registry
global_registry = ToolRegistry()