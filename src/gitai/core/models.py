"""Data models for GitAI core functionality."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class ChangeType(Enum):
    """Types of changes in git diff."""

    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNKNOWN = "?"
    BROKEN = "B"


@dataclass
class FileChange:
    """Represents a single file change in git diff.

    Attributes:
        path: File path relative to repository root
        change_type: Type of change (A, M, D, R, C, U, ?, B)
        lines_added: Number of lines added
        lines_removed: Number of lines deleted
        content_preview: Sample of changed content for context
        old_path: Previous path for renamed/copied files
    """

    path: str
    change_type: ChangeType
    lines_added: int
    lines_removed: int
    content_preview: str = ""
    old_path: Optional[str] = None

    @property
    def is_binary(self) -> bool:
        """Check if file appears to be binary."""
        return (
            self.lines_added == 0
            and self.lines_removed == 0
            and self.content_preview == ""
        )

    @property
    def net_lines(self) -> int:
        """Net line change (positive for growth, negative for reduction)."""
        return self.lines_added - self.lines_removed

    @property
    def change_description(self) -> str:
        """Human-readable description of the change."""
        if self.change_type == ChangeType.ADDED:
            return f"Added {self.path}"
        elif self.change_type == ChangeType.DELETED:
            return f"Deleted {self.path}"
        elif self.change_type == ChangeType.MODIFIED:
            return f"Modified {self.path} (+{self.lines_added}, -{self.lines_removed})"
        elif self.change_type == ChangeType.RENAMED:
            return f"Renamed {self.old_path} → {self.path}"
        elif self.change_type == ChangeType.COPIED:
            return f"Copied {self.old_path} → {self.path}"
        else:
            return f"Changed {self.path}"


@dataclass
class DiffAnalysis:
    """Analysis results of git differences.

    Attributes:
        files_changed: List of file changes
        total_additions: Total lines added across all files
        total_deletions: Total lines deleted across all files
        change_summary: High-level summary of changes
        commit_context: Additional context for commit message generation
        repository_info: Information about the repository
    """

    files_changed: List[FileChange]
    total_additions: int
    total_deletions: int
    change_summary: str
    commit_context: Dict[str, Any]
    repository_info: Dict[str, Any]

    @property
    def file_count(self) -> int:
        """Number of files changed."""
        return len(self.files_changed)

    @property
    def net_lines(self) -> int:
        """Net line change across all files."""
        return self.total_additions - self.total_deletions

    @property
    def files_by_type(self) -> Dict[ChangeType, List[FileChange]]:
        """Group files by change type."""
        grouped = {}
        for file_change in self.files_changed:
            change_type = file_change.change_type
            if change_type not in grouped:
                grouped[change_type] = []
            grouped[change_type].append(file_change)
        return grouped

    @property
    def file_extensions(self) -> List[str]:
        """Unique file extensions in changes."""
        extensions = set()
        for file_change in self.files_changed:
            if "." in file_change.path:
                ext = file_change.path.split(".")[-1].lower()
                extensions.add(ext)
        return sorted(list(extensions))

    @property
    def affected_directories(self) -> List[str]:
        """Directories containing changed files."""
        directories = set()
        for file_change in self.files_changed:
            dir_path = "/".join(file_change.path.split("/")[:-1])
            if dir_path:
                directories.add(dir_path)
        return sorted(list(directories))

    def get_change_scope(self) -> str:
        """Determine the scope of changes for commit message."""
        if len(self.affected_directories) == 1:
            return self.affected_directories[0]
        elif len(self.file_extensions) == 1:
            ext = self.file_extensions[0]
            if ext in ["py", "js", "ts", "java", "cpp", "c"]:
                return ext

        # Fallback to generic scope based on directories
        common_scopes = ["src", "lib", "tests", "docs", "config"]
        for scope in common_scopes:
            if any(scope in dir_path for dir_path in self.affected_directories):
                return scope

        return "core" if self.file_count > 1 else ""

    def is_likely_feature(self) -> bool:
        """Check if changes suggest a new feature."""
        # Heuristic: mostly additions, multiple files, new files
        return (
            self.total_additions > self.total_deletions * 2
            and self.file_count > 1
            and any(fc.change_type == ChangeType.ADDED for fc in self.files_changed)
        )

    def is_likely_fix(self) -> bool:
        """Check if changes suggest a bug fix."""
        # Heuristic: mix of additions/deletions, few files, no new files
        return (
            self.file_count <= 3
            and not any(fc.change_type == ChangeType.ADDED for fc in self.files_changed)
            and self.total_additions > 0
            and self.total_deletions > 0
        )

    def is_likely_refactor(self) -> bool:
        """Check if changes suggest refactoring."""
        # Heuristic: similar additions/deletions, renames/moves
        return abs(self.total_additions - self.total_deletions) < max(
            self.total_additions, self.total_deletions
        ) * 0.3 and any(
            fc.change_type in [ChangeType.RENAMED, ChangeType.COPIED]
            for fc in self.files_changed
        )
