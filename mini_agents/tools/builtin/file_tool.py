"""File read/write tool."""

from pathlib import Path
from typing import Any, List

from ..base import Tool, ToolParameter, tool_action


class FileTool(Tool):
    """Tool that supports reading and writing files."""

    def __init__(self, base_dir: str | None = None):
        """Initialize the file tool with an optional base directory.

        Args:
            base_dir: Base directory for resolving paths. If provided, paths must
                stay within this directory.
        """
        super().__init__(
            name="file_tool",
            description="Read and write local files.",
            expandable=True,
        )
        self.base_dir = Path(base_dir).expanduser().resolve() if base_dir else None

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate the target path."""
        target = Path(path)
        if self.base_dir:
            target = self.base_dir / target
        target = target.expanduser().resolve()
        if self.base_dir:
            try:
                target.relative_to(self.base_dir)
            except ValueError:
                raise ValueError(f"Path outside base_dir: {target}")
        return target

    def run(self, parameters: dict[str, Any]) -> str:
        """Execute tool action (read/write).

        Args:
            parameters: Tool parameters including action, path, content, encoding.

        Returns:
            Read content for read action, or status string for write action.
        """
        action = str(parameters.get("action", "")).lower()
        path = parameters.get("path") or parameters.get("file")
        encoding = parameters.get("encoding", "utf-8")
        if action == "read":
            if not path:
                return "Error: file path is required"
            return self._read_file(path=path, encoding=encoding)
        if action == "write":
            if not path:
                return "Error: file path is required"
            content = parameters.get("content", "")
            return self._write_file(path=path, content=content, encoding=encoding)
        return "Error: unsupported action"

    def get_parameters(self) -> List[ToolParameter]:
        """Return tool parameter definitions."""
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform: read or write",
                required=True,
            ),
            ToolParameter(
                name="path",
                type="string",
                description="File path",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write",
                required=False,
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="Text encoding",
                required=False,
                default="utf-8",
            ),
        ]

    @tool_action("file_read", "Read a file")
    def _read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file content.

        Args:
            path: File path relative to base_dir when set.
            encoding: Text encoding.
            
        Returns:
            The content of the file.
        """
        target = self._resolve_path(path)
        if not target.exists():
            return f"Error: file not found: {target}"
        return target.read_text(encoding=encoding)

    @tool_action("file_write", "Write to a file")
    def _write_file(self, path: str, content: str, encoding: str = "utf-8") -> str:
        """Write file content.

        Args:
            path: File path relative to base_dir when set.
            content: Text content to write.
            encoding: Text encoding.
            
        Returns:
            The status of the write operation.
        """
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content or "", encoding=encoding)
        return f"OK: wrote {target}"
