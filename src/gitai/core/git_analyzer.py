"""Git analysis functionality for extracting meaningful information from repositories."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import git
from git.exc import GitCommandError, InvalidGitRepositoryError

from gitai.core.models import ChangeType, DiffAnalysis, DiffHunk, FileChange
from gitai.utils.exceptions import (
    GitAnalysisError,
    GitOperationError,
    InvalidRepositoryError,
    NoStagedChangesError,
)
from gitai.utils.logger import log_with_context, setup_logger


class GitAnalyzer:
    """Analyzes git repositories to extract meaningful change information.

    This class provides methods to analyze staged changes for commit messages
    and branch changes for PR descriptions.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize GitAnalyzer.

        Args:
            repo_path: Path to git repository. If None, uses current directory.

        Raises:
            InvalidRepositoryError: If path is not a valid git repository.
        """
        self.logger = setup_logger(__name__)
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
            self.repo_root = Path(self.repo.working_dir)
        except InvalidGitRepositoryError as e:
            raise InvalidRepositoryError(
                f"Not a git repository: {self.repo_path}"
            ) from e

        log_with_context(
            self.logger,
            "info",
            "GitAnalyzer initialized",
            repo_path=str(self.repo_root),
        )

    def get_staged_changes(self, include_untracked: bool = False) -> DiffAnalysis:
        """Analyze staged changes for commit message generation.

        Args:
            include_untracked: Whether to include untracked files

        Returns:
            DiffAnalysis object containing staged changes

        Raises:
            NoStagedChangesError: If no staged changes found
            GitOperationError: If git operations fail
        """
        try:
            # Get staged changes with patch content for detailed analysis
            staged_diff = self.repo.index.diff("HEAD", create_patch=True)

            # Get untracked files if requested
            untracked_files = []
            if include_untracked:
                untracked_files = self.repo.untracked_files

            if not staged_diff and not untracked_files:
                raise NoStagedChangesError("No staged changes found")

            # Parse changes
            file_changes = []
            total_additions = 0
            total_deletions = 0

            # Process staged changes
            for diff_item in staged_diff:
                file_change = self._parse_diff_item(diff_item)
                file_changes.append(file_change)
                total_additions += file_change.lines_added
                total_deletions += file_change.lines_removed

            # Process untracked files
            for untracked_file in untracked_files:
                try:
                    file_path = Path(untracked_file)
                    if file_path.exists() and file_path.is_file():
                        # Count lines in new file
                        lines = len(
                            file_path.read_text(
                                encoding="utf-8", errors="ignore"
                            ).splitlines()
                        )
                        file_change = FileChange(
                            path=untracked_file,
                            change_type=ChangeType.ADDED,
                            lines_added=lines,
                            lines_removed=0,
                            content_preview=self._get_file_preview(file_path),
                        )
                        file_changes.append(file_change)
                        total_additions += lines
                except Exception as e:
                    self.logger.warning(
                        f"Could not analyze untracked file {untracked_file}: {e}"
                    )

            # Build context
            commit_context = self._build_commit_context()
            repository_info = self._get_repository_info()
            change_summary = self._generate_change_summary(file_changes)

            analysis = DiffAnalysis(
                files_changed=file_changes,
                total_additions=total_additions,
                total_deletions=total_deletions,
                change_summary=change_summary,
                commit_context=commit_context,
                repository_info=repository_info,
            )

            log_with_context(
                self.logger,
                "info",
                "Staged changes analyzed",
                file_count=len(file_changes),
                total_additions=total_additions,
                total_deletions=total_deletions,
            )

            return analysis

        except GitCommandError as e:
            raise GitOperationError(f"Git command failed: {e}") from e
        except Exception as e:
            raise GitAnalysisError(f"Failed to analyze staged changes: {e}") from e

    def get_branch_changes(
        self, base_branch: str = "main", include_detailed_diff: bool = False
    ) -> DiffAnalysis:
        """Analyze changes between current branch and base branch for PR generation.

        Args:
            base_branch: Base branch to compare against
            include_detailed_diff: Include detailed diff hunks and full diff content

        Returns:
            DiffAnalysis object containing branch changes

        Raises:
            GitOperationError: If git operations fail
        """
        try:
            # Ensure we have the latest base branch
            try:
                self.repo.git.fetch("origin", base_branch)
            except GitCommandError:
                # If fetch fails, continue with local branch
                pass

            # Get current branch name
            current_branch = self.repo.active_branch.name

            # Get diff between base and current branch
            try:
                base_ref = f"origin/{base_branch}"
                diff = self.repo.git.diff(f"{base_ref}...HEAD", "--numstat").strip()
            except GitCommandError:
                # Fallback to local base branch
                base_ref = base_branch
                diff = self.repo.git.diff(f"{base_ref}...HEAD", "--numstat").strip()

            if not diff:
                # No changes found
                return DiffAnalysis(
                    files_changed=[],
                    total_additions=0,
                    total_deletions=0,
                    change_summary="No changes found",
                    commit_context={
                        "current_branch": current_branch,
                        "base_branch": base_branch,
                    },
                    repository_info=self._get_repository_info(),
                )

            # Parse numstat output
            file_changes = []
            total_additions = 0
            total_deletions = 0

            for line in diff.split("\n"):
                if not line.strip():
                    continue

                parts = line.split("\t")
                if len(parts) >= 3:
                    additions_str, deletions_str, file_path = (
                        parts[0],
                        parts[1],
                        parts[2],
                    )

                    # Handle binary files
                    if additions_str == "-" or deletions_str == "-":
                        additions, deletions = 0, 0
                    else:
                        additions = int(additions_str) if additions_str.isdigit() else 0
                        deletions = int(deletions_str) if deletions_str.isdigit() else 0

                    # Determine change type
                    change_type = self._determine_change_type_from_diff(
                        base_ref, file_path
                    )

                    # Get diff content
                    diff_preview = self._get_diff_preview(base_ref, file_path)

                    # Parse hunks if detailed diff is requested
                    hunks: List[DiffHunk] = []
                    full_diff: Optional[str] = None
                    if include_detailed_diff:
                        try:
                            full_diff = self.repo.git.diff(
                                f"{base_ref}...HEAD", "--", file_path
                            )
                            if full_diff:
                                hunks = self._parse_diff_hunks(full_diff)
                        except Exception as e:
                            self.logger.warning(
                                f"Could not parse hunks for {file_path}: {e}"
                            )

                    file_change = FileChange(
                        path=file_path,
                        change_type=change_type,
                        lines_added=additions,
                        lines_removed=deletions,
                        content_preview=diff_preview,
                        hunks=hunks,
                        full_diff=full_diff if include_detailed_diff else None,
                    )

                    file_changes.append(file_change)
                    total_additions += additions
                    total_deletions += deletions

            # Build context for PR
            commit_context = {
                "current_branch": current_branch,
                "base_branch": base_branch,
                "commit_count": len(list(self.repo.iter_commits(f"{base_ref}..HEAD"))),
            }

            repository_info = self._get_repository_info()
            change_summary = self._generate_change_summary(file_changes)

            analysis = DiffAnalysis(
                files_changed=file_changes,
                total_additions=total_additions,
                total_deletions=total_deletions,
                change_summary=change_summary,
                commit_context=commit_context,
                repository_info=repository_info,
            )

            log_with_context(
                self.logger,
                "info",
                "Branch changes analyzed",
                current_branch=current_branch,
                base_branch=base_branch,
                file_count=len(file_changes),
                total_additions=total_additions,
                total_deletions=total_deletions,
            )

            return analysis

        except GitCommandError as e:
            raise GitOperationError(f"Git command failed: {e}") from e
        except Exception as e:
            raise GitAnalysisError(f"Failed to analyze branch changes: {e}") from e

    def _parse_diff_item(self, diff_item: git.Diff) -> FileChange:
        """Parse a GitPython diff item into FileChange object."""
        # Determine change type
        if diff_item.new_file:
            change_type = ChangeType.ADDED
        elif diff_item.deleted_file:
            change_type = ChangeType.DELETED
        elif diff_item.renamed_file:
            change_type = ChangeType.RENAMED
        elif diff_item.copied_file:
            change_type = ChangeType.COPIED
        else:
            change_type = ChangeType.MODIFIED

        # Get file paths
        file_path = diff_item.b_path or diff_item.a_path or "unknown"
        old_path = diff_item.a_path if diff_item.renamed_file else None

        # Count lines (approximation from diff)
        lines_added, lines_removed = self._count_diff_lines(diff_item)

        # Get content preview and full diff
        content_preview = self._get_diff_item_preview(diff_item, max_lines=15)

        # Parse hunks from diff for detailed analysis
        hunks: List[DiffHunk] = []
        full_diff: Optional[str] = None
        try:
            diff_data = diff_item.diff
            if diff_data:
                full_diff = (
                    diff_data.decode("utf-8", errors="ignore")
                    if isinstance(diff_data, bytes)
                    else diff_data
                )
                if full_diff:
                    hunks = self._parse_diff_hunks(full_diff)
        except Exception:
            pass

        return FileChange(
            path=file_path,
            change_type=change_type,
            lines_added=lines_added,
            lines_removed=lines_removed,
            content_preview=content_preview,
            old_path=old_path,
            hunks=hunks,
            full_diff=full_diff,
        )

    def _count_diff_lines(self, diff_item: git.Diff) -> tuple[int, int]:
        """Count added and removed lines from diff item."""
        try:
            diff_data = diff_item.diff
            if diff_data is None:
                return 0, 0
            diff_text = (
                diff_data.decode("utf-8", errors="ignore")
                if isinstance(diff_data, bytes)
                else diff_data
            )
            additions = len(re.findall(r"^\+[^+]", diff_text, re.MULTILINE))
            deletions = len(re.findall(r"^-[^-]", diff_text, re.MULTILINE))
            return additions, deletions
        except Exception:
            return 0, 0

    def _get_diff_item_preview(self, diff_item: git.Diff, max_lines: int = 15) -> str:
        """Get a preview of the diff content.

        Args:
            diff_item: GitPython diff item
            max_lines: Maximum number of changed lines to include (default 15)

        Returns:
            String with diff preview showing added/removed lines
        """
        try:
            diff_data = diff_item.diff
            if diff_data is None:
                return ""
            diff_text = (
                diff_data.decode("utf-8", errors="ignore")
                if isinstance(diff_data, bytes)
                else diff_data
            )
            lines = diff_text.split("\n")

            # Find meaningful lines (skip headers)
            content_lines: List[str] = []
            for line in lines:
                if (
                    line.startswith("@@")
                    or line.startswith("+++")
                    or line.startswith("---")
                ):
                    continue
                if line.startswith(("+", "-")) and len(content_lines) < max_lines:
                    content_lines.append(line[:150])  # Allow longer lines for context

            return "\n".join(content_lines)
        except Exception:
            return ""

    def _determine_change_type_from_diff(
        self, base_ref: str, file_path: str
    ) -> ChangeType:
        """Determine change type from git diff status."""
        try:
            status = self.repo.git.diff(
                "--name-status", f"{base_ref}...HEAD", "--", file_path
            )
            if status:
                status_char = status.split("\t")[0][0]
                return ChangeType(status_char)
        except Exception:
            pass
        return ChangeType.MODIFIED

    def _get_diff_preview(
        self, base_ref: str, file_path: str, max_lines: int = 15
    ) -> str:
        """Get a preview of file diff.

        Args:
            base_ref: Base reference to compare against
            file_path: Path to the file
            max_lines: Maximum number of changed lines to include

        Returns:
            String with diff preview
        """
        try:
            diff_output = self.repo.git.diff(f"{base_ref}...HEAD", "--", file_path)
            lines = diff_output.split("\n")

            content_lines: List[str] = []
            for line in lines:
                if (
                    line.startswith("@@")
                    or line.startswith("+++")
                    or line.startswith("---")
                ):
                    continue
                if line.startswith(("+", "-")) and len(content_lines) < max_lines:
                    content_lines.append(line[:150])

            return "\n".join(content_lines)
        except Exception:
            return ""

    def _get_file_preview(self, file_path: Path, max_lines: int = 15) -> str:
        """Get a preview of file content for new files.

        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to include

        Returns:
            String with file content preview (prefixed with + for new content)
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")[:max_lines]
            # Prefix with + to indicate new content
            return "\n".join(f"+{line[:150]}" for line in lines)
        except Exception:
            return ""

    def _build_commit_context(self) -> Dict[str, Any]:
        """Build context for commit message generation."""
        context = {
            "branch": self.repo.active_branch.name,
            "last_commit": "",
            "author": "",
        }

        try:
            # Get last commit info
            last_commit = self.repo.head.commit
            message = last_commit.message
            # Ensure message is a string (it might be bytes in some git implementations)
            if isinstance(message, bytes):
                message = message.decode("utf-8", errors="ignore")
            context["last_commit"] = message.strip()
            context["author"] = str(last_commit.author)
        except Exception:
            pass

        return context

    def _get_repository_info(self) -> Dict[str, Any]:
        """Get general repository information."""
        info = {
            "name": self.repo_root.name,
            "path": str(self.repo_root),
            "remote_url": "",
        }

        try:
            # Get remote URL
            if self.repo.remotes:
                url = self.repo.remotes.origin.url
                info["remote_url"] = str(url)  # Ensure it's always a string
        except Exception:
            pass

        return info

    def _generate_change_summary(self, file_changes: List[FileChange]) -> str:
        """Generate a high-level summary of changes."""
        if not file_changes:
            return "No changes"

        file_count = len(file_changes)

        # Categorize changes
        by_type = {}
        for change in file_changes:
            change_type = change.change_type
            if change_type not in by_type:
                by_type[change_type] = 0
            by_type[change_type] += 1

        # Build summary
        parts = []
        if ChangeType.ADDED in by_type:
            parts.append(f"{by_type[ChangeType.ADDED]} added")
        if ChangeType.MODIFIED in by_type:
            parts.append(f"{by_type[ChangeType.MODIFIED]} modified")
        if ChangeType.DELETED in by_type:
            parts.append(f"{by_type[ChangeType.DELETED]} deleted")
        if ChangeType.RENAMED in by_type:
            parts.append(f"{by_type[ChangeType.RENAMED]} renamed")

        if file_count == 1:
            return f"1 file {', '.join(parts)}"
        else:
            return f"{file_count} files ({', '.join(parts)})"

    def _parse_diff_hunks(self, diff_text: str, max_hunks: int = 10) -> List[DiffHunk]:
        """Parse diff text into structured hunks.

        Args:
            diff_text: Raw diff text
            max_hunks: Maximum number of hunks to parse (to avoid overwhelming output)

        Returns:
            List of DiffHunk objects
        """
        hunks: List[DiffHunk] = []
        if not diff_text:
            return hunks

        lines = diff_text.split("\n")
        current_hunk: Optional[DiffHunk] = None
        current_line = 0

        for line in lines:
            # Detect hunk header (e.g., @@ -10,5 +10,6 @@ def my_function():)
            if line.startswith("@@"):
                if current_hunk and len(hunks) < max_hunks:
                    hunks.append(current_hunk)

                # Parse hunk header to get line numbers and function context
                match = re.search(r"@@ -(\d+),?\d* \+(\d+),?\d* @@\s*(.*)", line)
                if match:
                    start_line = int(match.group(2))
                    function_context = match.group(3).strip()
                    current_line = start_line
                    current_hunk = DiffHunk(
                        start_line=start_line,
                        end_line=start_line,
                        header=line,
                        function_context=function_context,
                    )

            elif current_hunk:
                if line.startswith("+") and not line.startswith("+++"):
                    current_hunk.added_lines.append(line[1:])
                    current_hunk.unified_lines.append(line)
                    current_line += 1
                    current_hunk.end_line = current_line
                elif line.startswith("-") and not line.startswith("---"):
                    current_hunk.removed_lines.append(line[1:])
                    current_hunk.unified_lines.append(line)
                elif line.startswith(" "):
                    # Context line
                    if not current_hunk.added_lines and not current_hunk.removed_lines:
                        current_hunk.context_before.append(line[1:])
                    else:
                        current_hunk.context_after.append(line[1:])
                    current_hunk.unified_lines.append(line)
                    current_line += 1
                    current_hunk.end_line = current_line

        # Add the last hunk
        if current_hunk and len(hunks) < max_hunks:
            hunks.append(current_hunk)

        return hunks[:max_hunks]
