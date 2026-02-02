"""Tool definitions for agentic diff inspection."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from gitai.core.models import DiffAnalysis


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool."""

    tool_call_id: str
    name: str
    content: str
    is_error: bool = False


class DiffInspectionTools:
    """Read-only tools for inspecting git diffs.

    The LLM uses these to explore staged changes iteratively
    before generating a commit message.
    """

    def __init__(
        self, diff_analysis: DiffAnalysis, max_diff_lines: int = 200
    ) -> None:
        self._diff = diff_analysis
        self._max_diff_lines = max_diff_lines

    def list_changed_files(self) -> str:
        """List all changed files with metadata (no content)."""
        if not self._diff.files_changed:
            return "No files changed."

        lines = [
            f"Changed files ({len(self._diff.files_changed)}):\n"
        ]

        for fc in self._diff.files_changed:
            lines.append(
                f"- {fc.path} [{fc.change_type.value}] "
                f"(+{fc.lines_added}, -{fc.lines_removed})"
            )
            if fc.old_path:
                lines.append(f"  Renamed from: {fc.old_path}")

        return "\n".join(lines)

    def get_file_diff(self, file_path: str) -> str:
        """Get the diff for a specific file, truncated if too large."""
        for fc in self._diff.files_changed:
            if fc.path == file_path:
                diff_text = fc.full_diff
                if not diff_text:
                    if fc.content_preview:
                        return (
                            f"Full diff not available for {file_path}. "
                            f"Content preview:\n{fc.content_preview}"
                        )
                    return f"No diff content available for {file_path}."

                diff_lines = diff_text.split("\n")
                total = len(diff_lines)

                if total <= self._max_diff_lines:
                    return diff_text

                head = self._max_diff_lines // 2 + self._max_diff_lines % 2
                tail = self._max_diff_lines // 2
                truncated = (
                    diff_lines[:head]
                    + [
                        f"\n... TRUNCATED ({total} lines total, "
                        f"showing first {head} and last {tail}) ...\n"
                    ]
                    + diff_lines[-tail:]
                )
                return "\n".join(truncated)

        return f"File not found in staged changes: {file_path}"

    def get_change_summary(self) -> str:
        """Get high-level change summary with statistics."""
        lines = [
            f"Summary: {self._diff.change_summary}",
            f"Total additions: +{self._diff.total_additions}",
            f"Total deletions: -{self._diff.total_deletions}",
            f"Net change: {self._diff.net_lines:+d} lines",
            f"Files: {self._diff.file_count}",
        ]

        exts = self._diff.file_extensions
        if exts:
            lines.append(f"File types: {', '.join(exts)}")

        dirs = self._diff.affected_directories
        if dirs:
            lines.append(f"Directories: {', '.join(dirs)}")

        scope = self._diff.get_change_scope()
        if scope:
            lines.append(f"Scope: {scope}")

        if self._diff.is_likely_feature():
            lines.append("Heuristic: likely a new feature")
        elif self._diff.is_likely_fix():
            lines.append("Heuristic: likely a bug fix")
        elif self._diff.is_likely_refactor():
            lines.append("Heuristic: likely a refactor")

        ctx = self._diff.commit_context
        if ctx.get("branch"):
            lines.append(f"Branch: {ctx['branch']}")
        if ctx.get("last_commit"):
            lines.append(f"Last commit: {ctx['last_commit'][:80]}")

        return "\n".join(lines)

    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """Return tool definitions in OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_changed_files",
                    "description": (
                        "List all changed files with their change type and lines "
                        "added/removed. Call this first to understand the scope "
                        "of changes, then use get_file_diff for details."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_diff",
                    "description": (
                        "Get the detailed diff for a specific file. Use this "
                        "to inspect the actual code changes in important files. "
                        "Large diffs are truncated."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": (
                                    "The file path as returned by list_changed_files"
                                ),
                            },
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_change_summary",
                    "description": (
                        "Get a high-level summary of all changes including "
                        "statistics, affected directories, file types, scope, "
                        "and heuristic classification (feature/fix/refactor)."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result."""
        handlers = {
            "list_changed_files": lambda args: self.list_changed_files(),
            "get_file_diff": lambda args: self.get_file_diff(
                args.get("file_path", "")
            ),
            "get_change_summary": lambda args: self.get_change_summary(),
        }

        handler = handlers.get(tool_call.name)
        if not handler:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"Unknown tool: {tool_call.name}",
                is_error=True,
            )

        try:
            content = handler(tool_call.arguments)
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=content,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"Tool execution error: {e}",
                is_error=True,
            )
