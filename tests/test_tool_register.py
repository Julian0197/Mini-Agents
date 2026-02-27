from pathlib import Path
from re import sub
import sys

from mini_agents.tools import FileTool, ToolRegistry, SearchTool


def main():
    base_dir = Path(__file__).resolve().parent.parent / "skills"
    print(f"Base directory: {base_dir}")
    fileTool = FileTool(base_dir=base_dir)
    # Test fileTool read action
    print(f"FileTool read action:s {fileTool.run({"action": "read", "path": "test.md"})}")
    register = ToolRegistry()
    register.register_tool(fileTool, auto_expand=True)
    register.register_tool(SearchTool(), auto_expand=False)

    # Test tool registration
    print(f"Tool registered: {register.get_tool('file_tool')}")
    print(f"Tool description: \n{register.get_tools_description()}")
    print(f"Tool list all: {register.list_all()}")
    print(f"Tool get all tools: {register.get_all_tools()}")

    # Test sub-tools
    print(f"Tool expanded tools: {fileTool.get_expanded_tools()}")
    sub_write = register.get_tool("file_write")
    sub_read = register.get_tool("file_read")
    # Test sub-tools execution
    print(f"Sub-tools write execution: {sub_write.run({"path": "test.md", "content": "Hello from sub-tool!"})}")
    print(f"Sub-tools read execution after write: {sub_read.run({"path": "test.md"})}")

    # Test unregister
    register.unregister("file_tool")
    print(f"Tool after unregister: {register.get_tool('file_tool')}")

    # Test clear
    register.clear()
    print(f"Tool list all after clear: {register.list_all()}")


if __name__ == "__main__":
    main()
