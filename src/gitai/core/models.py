"""Data models for GitAI core functionality."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
class DiffHunk:
    """Represents a single hunk (block of changes) in a diff.

    Attributes:
        start_line: Starting line number in the file
        end_line: Ending line number in the file
        context_before: Lines before the change for context
        added_lines: Lines that were added
        removed_lines: Lines that were removed
        context_after: Lines after the change for context
        header: The hunk header (e.g., '@@ -10,5 +10,6 @@')
        function_context: Function/class name extracted from the @@ header
        unified_lines: Interleaved diff lines with +/-/space prefixes
    """

    start_line: int
    end_line: int
    context_before: List[str] = field(default_factory=list)
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    header: str = ""
    function_context: str = ""
    unified_lines: List[str] = field(default_factory=list)

    @property
    def has_function_context(self) -> bool:
        """Check if this hunk has function/class context."""
        return bool(self.function_context)

    @property
    def summary(self) -> str:
        """Generate a summary of this hunk."""
        prefix = f"in {self.function_context}: " if self.function_context else ""
        if self.added_lines and not self.removed_lines:
            return f"{prefix}Added {len(self.added_lines)} line(s)"
        elif self.removed_lines and not self.added_lines:
            return f"{prefix}Removed {len(self.removed_lines)} line(s)"
        else:
            return f"{prefix}Modified {len(self.added_lines) + len(self.removed_lines)} line(s)"


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
        hunks: List of diff hunks for detailed analysis
        full_diff: Complete diff content (optional, for detailed mode)
    """

    path: str
    change_type: ChangeType
    lines_added: int
    lines_removed: int
    content_preview: str = ""
    old_path: Optional[str] = None
    hunks: List[DiffHunk] = field(default_factory=list)
    full_diff: Optional[str] = None

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
        grouped: Dict[ChangeType, List[FileChange]] = {}
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
