"""Context builder for template rendering."""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass

from ..core.models import DiffAnalysis, FileChange, ChangeType
from ..utils.exceptions import TemplateError


@dataclass
class RepositoryInfo:
    """Repository information for templates."""

    name: str
    url: Optional[str]
    branch: str
    remote: str
    root_path: Path


@dataclass
class UserInfo:
    """User information for templates."""

    name: Optional[str]
    email: Optional[str]


@dataclass
class EnhancedFileChange:
    """Enhanced file change with additional context."""

    path: str
    change_type: str
    lines_added: int
    lines_deleted: int
    description: Optional[str] = None
    is_test: bool = False
    is_config: bool = False
    is_docs: bool = False
    language: Optional[str] = None


@dataclass
class EnhancedDiffAnalysis:
    """Enhanced diff analysis with template-friendly structure."""

    summary: str
    body: Optional[str] = None
    rationale: Optional[str] = None
    scope: Optional[str] = None
    breaking_change: Optional[str] = None

    # Change type flags
    is_feature: bool = False
    is_fix: bool = False
    is_refactor: bool = False
    is_docs: bool = False
    is_test: bool = False

    # File lists
    affected_files: List[EnhancedFileChange] = None
    added_files: List[EnhancedFileChange] = None
    modified_files: List[EnhancedFileChange] = None
    deleted_files: List[EnhancedFileChange] = None
    test_files: List[EnhancedFileChange] = None

    # Statistics
    lines_added: int = 0
    lines_deleted: int = 0

    # Related issues (extracted from content)
    related_issues: List[str] = None

    def __post_init__(self):
        if self.affected_files is None:
            self.affected_files = []
        if self.added_files is None:
            self.added_files = []
        if self.modified_files is None:
            self.modified_files = []
        if self.deleted_files is None:
            self.deleted_files = []
        if self.test_files is None:
            self.test_files = []
        if self.related_issues is None:
            self.related_issues = []


class ContextBuilder:
    """Builds rich context for template rendering."""

    def __init__(self, repository_root: Optional[Path] = None):
        """Initialize the context builder.

        Args:
            repository_root: Root directory of the git repository
        """
        self.repository_root = repository_root or self._find_git_root()

        # File classification patterns
        self.test_patterns = [
            r"test_.*\.py$",
            r".*_test\.py$",
            r".*\.test\.js$",
            r".*\.spec\.js$",
            r"tests?/.*",
            r"spec/.*",
            r"__tests__/.*",
        ]

        self.config_patterns = [
            r".*\.config\.(js|ts|json|yaml|yml)$",
            r".*\.env.*",
            r"Dockerfile.*",
            r".*\.ini$",
            r".*\.cfg$",
            r"pyproject\.toml$",
            r"package\.json$",
            r"requirements.*\.txt$",
            r"Gemfile$",
            r"pom\.xml$",
        ]

        self.docs_patterns = [
            r".*\.md$",
            r".*\.rst$",
            r".*\.txt$",
            r"docs?/.*",
            r"README.*",
            r"CHANGELOG.*",
            r"LICENSE.*",
        ]

        # Language detection by extension
        self.language_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "h": "c",
            "rs": "rust",
            "go": "go",
            "php": "php",
            "rb": "ruby",
            "swift": "swift",
            "kt": "kotlin",
            "cs": "csharp",
            "html": "html",
            "css": "css",
            "scss": "scss",
            "json": "json",
            "yaml": "yaml",
            "yml": "yaml",
            "xml": "xml",
            "sql": "sql",
            "sh": "shell",
        }

    def _find_git_root(self) -> Optional[Path]:
        """Find the git repository root directory."""
        current = Path.cwd()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        return None

    def build_commit_context(
        self,
        diff_analysis: DiffAnalysis,
        user_info: Optional[UserInfo] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build context for commit message templates.

        Args:
            diff_analysis: Git diff analysis
            user_info: User information
            additional_context: Additional context variables

        Returns:
            Template context dictionary
        """
        context = {
            "changes": self._enhance_diff_analysis(diff_analysis),
            "repository": self._get_repository_info(),
            "user": user_info or self._get_user_info(),
            "timestamp": datetime.now().isoformat(),
        }

        if additional_context:
            context.update(additional_context)

        return context

    def build_pr_context(
        self,
        diff_analysis: DiffAnalysis,
        base_branch: str,
        head_branch: str,
        user_info: Optional[UserInfo] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build context for PR description templates.

        Args:
            diff_analysis: Git diff analysis
            base_branch: Base branch name
            head_branch: Head branch name
            user_info: User information
            additional_context: Additional context variables

        Returns:
            Template context dictionary
        """
        context = {
            "changes": self._enhance_diff_analysis(diff_analysis),
            "repository": self._get_repository_info(),
            "user": user_info or self._get_user_info(),
            "base_branch": base_branch,
            "head_branch": head_branch,
            "timestamp": datetime.now().isoformat(),
        }

        if additional_context:
            context.update(additional_context)

        return context

    def _enhance_diff_analysis(
        self, diff_analysis: DiffAnalysis
    ) -> EnhancedDiffAnalysis:
        """Convert DiffAnalysis to enhanced template-friendly format."""
        enhanced_files = []
        added_files = []
        modified_files = []
        deleted_files = []
        test_files = []

        for file_change in diff_analysis.files_changed:
            enhanced_file = self._enhance_file_change(file_change)
            enhanced_files.append(enhanced_file)

            # Categorize files
            if enhanced_file.change_type == "added":
                added_files.append(enhanced_file)
            elif enhanced_file.change_type == "modified":
                modified_files.append(enhanced_file)
            elif enhanced_file.change_type == "deleted":
                deleted_files.append(enhanced_file)

            if enhanced_file.is_test:
                test_files.append(enhanced_file)

        # Generate summary if not provided
        summary = self._generate_change_summary(diff_analysis, enhanced_files)

        # Detect change type
        is_feature = diff_analysis.is_likely_feature()
        is_fix = diff_analysis.is_likely_fix()
        is_refactor = diff_analysis.is_likely_refactor()
        is_docs = self._is_docs_change(enhanced_files)
        is_test = self._is_test_change(enhanced_files)

        # Extract related issues
        related_issues = self._extract_related_issues(diff_analysis.change_summary)

        return EnhancedDiffAnalysis(
            summary=summary,
            scope=diff_analysis.get_change_scope(),
            is_feature=is_feature,
            is_fix=is_fix,
            is_refactor=is_refactor,
            is_docs=is_docs,
            is_test=is_test,
            affected_files=enhanced_files,
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            test_files=test_files,
            lines_added=diff_analysis.total_additions,
            lines_deleted=diff_analysis.total_deletions,
            related_issues=related_issues,
        )

    def _enhance_file_change(self, file_change: FileChange) -> EnhancedFileChange:
        """Convert FileChange to enhanced format with additional context."""
        # Map change types to readable strings
        change_type_map = {
            ChangeType.ADDED: "added",
            ChangeType.MODIFIED: "modified",
            ChangeType.DELETED: "deleted",
            ChangeType.RENAMED: "renamed",
            ChangeType.COPIED: "copied",
        }

        change_type = change_type_map.get(file_change.change_type, "changed")

        # Classify file
        is_test = self._is_test_file(file_change.path)
        is_config = self._is_config_file(file_change.path)
        is_docs = self._is_docs_file(file_change.path)

        # Detect language
        language = self._detect_language(file_change.path)

        # Generate description
        description = self._generate_file_description(
            file_change, is_test, is_config, is_docs
        )

        return EnhancedFileChange(
            path=file_change.path,
            change_type=change_type,
            lines_added=file_change.lines_added,
            lines_deleted=file_change.lines_removed,
            description=description,
            is_test=is_test,
            is_config=is_config,
            is_docs=is_docs,
            language=language,
        )

    def _is_test_file(self, path: str) -> bool:
        """Check if file is a test file."""
        return any(
            re.search(pattern, path, re.IGNORECASE) for pattern in self.test_patterns
        )

    def _is_config_file(self, path: str) -> bool:
        """Check if file is a configuration file."""
        return any(
            re.search(pattern, path, re.IGNORECASE) for pattern in self.config_patterns
        )

    def _is_docs_file(self, path: str) -> bool:
        """Check if file is a documentation file."""
        return any(
            re.search(pattern, path, re.IGNORECASE) for pattern in self.docs_patterns
        )

    def _detect_language(self, path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        if "." not in path:
            return None

        extension = path.split(".")[-1].lower()
        return self.language_map.get(extension)

    def _generate_file_description(
        self, file_change: FileChange, is_test: bool, is_config: bool, is_docs: bool
    ) -> Optional[str]:
        """Generate a description for a file change."""
        if is_test:
            return "Test file"
        elif is_config:
            return "Configuration file"
        elif is_docs:
            return "Documentation"
        elif file_change.change_type == ChangeType.ADDED:
            return "New file"
        elif file_change.lines_added > file_change.lines_removed * 3:
            return "Major additions"
        elif file_change.lines_removed > file_change.lines_added * 3:
            return "Major deletions"
        else:
            return "Updated"

    def _is_docs_change(self, files: List[EnhancedFileChange]) -> bool:
        """Check if change is primarily documentation."""
        if not files:
            return False

        docs_files = sum(1 for f in files if f.is_docs)
        return docs_files > len(files) * 0.7

    def _is_test_change(self, files: List[EnhancedFileChange]) -> bool:
        """Check if change is primarily test-related."""
        if not files:
            return False

        test_files = sum(1 for f in files if f.is_test)
        return test_files > len(files) * 0.7

    def _generate_change_summary(
        self, diff_analysis: DiffAnalysis, enhanced_files: List[EnhancedFileChange]
    ) -> str:
        """Generate a summary of changes if not provided."""
        if diff_analysis.change_summary and diff_analysis.change_summary.strip():
            return diff_analysis.change_summary

        # Generate based on file analysis
        if self._is_docs_change(enhanced_files):
            return "Update documentation"
        elif self._is_test_change(enhanced_files):
            return "Update tests"
        elif diff_analysis.is_likely_feature():
            return "Add new feature"
        elif diff_analysis.is_likely_fix():
            return "Fix bug"
        elif diff_analysis.is_likely_refactor():
            return "Refactor code"
        else:
            return "Update code"

    def _extract_related_issues(self, text: str) -> List[str]:
        """Extract issue references from text."""
        if not text:
            return []

        # Common patterns for issue references
        patterns = [
            r"#(\d+)",  # #123
            r"closes?\s+#(\d+)",  # closes #123
            r"fixes?\s+#(\d+)",  # fixes #123
            r"resolves?\s+#(\d+)",  # resolves #123
        ]

        issues = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.add(f"#{match}")

        return sorted(list(issues))

    def _get_repository_info(self) -> RepositoryInfo:
        """Get repository information."""
        if not self.repository_root:
            return RepositoryInfo(
                name="unknown",
                url=None,
                branch="main",
                remote="origin",
                root_path=Path.cwd(),
            )

        repo_name = self.repository_root.name

        # Try to get git info
        branch = "main"
        remote = "origin"
        url = None

        try:
            import git

            repo = git.Repo(self.repository_root)
            branch = repo.active_branch.name

            # Get remote URL
            if repo.remotes:
                remote_obj = repo.remotes[0]  # Use first remote
                remote = remote_obj.name
                url = list(remote_obj.urls)[0] if remote_obj.urls else None
        except:
            # Fall back to defaults if git operations fail
            pass

        return RepositoryInfo(
            name=repo_name,
            url=url,
            branch=branch,
            remote=remote,
            root_path=self.repository_root,
        )

    def _get_user_info(self) -> UserInfo:
        """Get user information from git config or environment."""
        name = None
        email = None

        try:
            import git

            if self.repository_root:
                repo = git.Repo(self.repository_root)
                config = repo.config_reader()

                try:
                    name = config.get_value("user", "name")
                except:
                    pass

                try:
                    email = config.get_value("user", "email")
                except:
                    pass
        except:
            pass

        # Fall back to environment variables
        if not name:
            name = os.environ.get("GIT_AUTHOR_NAME") or os.environ.get("USER")

        if not email:
            email = os.environ.get("GIT_AUTHOR_EMAIL")

        return UserInfo(name=name, email=email)


def create_context_builder(repository_root: Optional[Path] = None) -> ContextBuilder:
    """Create a context builder instance.

    Args:
        repository_root: Root directory of git repository (auto-detected if None)

    Returns:
        Configured ContextBuilder instance
    """
    return ContextBuilder(repository_root=repository_root)


def build_commit_context(
    diff_analysis: DiffAnalysis, 
    config: Any,
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build context for commit message templates.
    
    Args:
        diff_analysis: Git diff analysis
        config: GitAI configuration
        additional_context: Additional context variables
        
    Returns:
        Template context dictionary
    """
    builder = create_context_builder()
    
    # Get user info from config if available
    user_info = None
    if hasattr(config, 'user') and config.user:
        user_info = UserInfo(
            name=getattr(config.user, 'name', None),
            email=getattr(config.user, 'email', None)
        )
    
    return builder.build_commit_context(
        diff_analysis=diff_analysis,
        user_info=user_info,
        additional_context=additional_context,
    )


def build_pr_context(
    diff_analysis: DiffAnalysis,
    config: Any,
    base_branch: str,
    head_branch: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build context for PR description templates.
    
    Args:
        diff_analysis: Git diff analysis
        config: GitAI configuration
        base_branch: Base branch name
        head_branch: Head branch name (auto-detected if None)
        additional_context: Additional context variables
        
    Returns:
        Template context dictionary
    """
    builder = create_context_builder()
    
    # Get user info from config if available
    user_info = None
    if hasattr(config, 'user') and config.user:
        user_info = UserInfo(
            name=getattr(config.user, 'name', None),
            email=getattr(config.user, 'email', None)
        )
    
    # Auto-detect head branch if not provided
    if not head_branch:
        try:
            import git
            if builder.repository_root:
                repo = git.Repo(builder.repository_root)
                head_branch = repo.active_branch.name
        except:
            head_branch = "current"
    
    return builder.build_pr_context(
        diff_analysis=diff_analysis,
        base_branch=base_branch,
        head_branch=head_branch or "current",
        user_info=user_info,
        additional_context=additional_context,
    )
