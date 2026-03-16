"""Git integration for version control"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("orchestration.git_integration")


@dataclass
class GitStatus:
    """Git status"""
    branch: str
    modified: List[str]
    staged: List[str]
    untracked: List[str]
    ahead: int
    behind: int


@dataclass
class GitCommit:
    """Git commit"""
    hash: str
    message: str
    author: str
    date: str
    files: List[str]


class GitIntegration:
    """Git operations integration"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
    
    def _run(self, *args) -> tuple:
        """Run git command"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except Exception as e:
            return "", str(e), 1
    
    def is_repo(self) -> bool:
        """Check if directory is a git repo"""
        _, _, code = self._run("rev-parse", "--git-dir")
        return code == 0
    
    def get_status(self) -> Optional[GitStatus]:
        """Get git status"""
        if not self.is_repo():
            return None
        
        # Branch
        branch_out, _, _ = self._run("branch", "--show-current")
        branch = branch_out or "main"
        
        # Modified
        mod_out, _, _ = self._run("status", "--porcelain", "--short")
        modified = []
        staged = []
        untracked = []
        
        for line in mod_out.split("\n"):
            if not line:
                continue
            
            status = line[:2]
            file = line[3:]
            
            if "M" in status:
                modified.append(file)
            if status.startswith("M"):
                staged.append(file)
            if "?" in status:
                untracked.append(file)
        
        # Ahead/behind
        ahead = 0
        behind = 0
        
        revs_out, _, _ = self._run("rev-list", "--left-right", "--count", f"{branch}...origin/{branch}")
        if revs_out:
            parts = revs_out.split()
            if len(parts) == 2:
                ahead = int(parts[0])
                behind = int(parts[1])
        
        return GitStatus(
            branch=branch,
            modified=modified,
            staged=staged,
            untracked=untracked,
            ahead=ahead,
            behind=behind,
        )
    
    def get_log(self, max_count: int = 10) -> List[GitCommit]:
        """Get commit log"""
        if not self.is_repo():
            return []
        
        out, _, _ = self._run(
            "log",
            f"--max-count={max_count}",
            "--pretty=format:%H|%s|%an|%ad|%P",
            "--date=iso",
        )
        
        commits = []
        
        for line in out.split("\n"):
            if not line:
                continue
            
            parts = line.split("|")
            
            if len(parts) >= 4:
                # Get files for this commit
                files_out, _, _ = self._run("show", "--pretty=format:", "--name-only", parts[0])
                files = files_out.split("\n") if files_out else []
                
                commits.append(GitCommit(
                    hash=parts[0][:8],
                    message=parts[1],
                    author=parts[2],
                    date=parts[3],
                    files=[f for f in files if f],
                ))
        
        return commits
    
    def add(self, *paths) -> bool:
        """Stage files"""
        if not paths:
            return False
        
        _, _, code = self._run("add", *paths)
        return code == 0
    
    def commit(self, message: str) -> Optional[str]:
        """Create commit"""
        _, _, code = self._run("commit", "-m", message)
        
        if code == 0:
            out, _, _ = self._run("rev-parse", "HEAD")
            return out[:8] if out else None
        
        return None
    
    def push(self, remote: str = "origin", branch: str = None) -> bool:
        """Push to remote"""
        if branch:
            _, _, code = self._run("push", remote, branch)
        else:
            _, _, code = self._run("push", remote)
        
        return code == 0
    
    def pull(self, remote: str = "origin", branch: str = None) -> bool:
        """Pull from remote"""
        if branch:
            _, _, code = self._run("pull", remote, branch)
        else:
            _, _, code = self._run("pull", remote)
        
        return code == 0
    
    def create_branch(self, name: str, checkout: bool = True) -> bool:
        """Create branch"""
        if checkout:
            _, _, code = self._run("checkout", "-b", name)
        else:
            _, _, code = self._run("branch", name)
        
        return code == 0
    
    def checkout(self, branch: str) -> bool:
        """Checkout branch"""
        _, _, code = self._run("checkout", branch)
        return code == 0
    
    def get_diff(self, target: str = "HEAD") -> str:
        """Get diff"""
        out, _, _ = self._run("diff", target)
        return out
    
    def get_branches(self) -> List[str]:
        """Get all branches"""
        out, _, _ = self._run("branch", "-a")
        
        branches = []
        for line in out.split("\n"):
            line = line.strip()
            if line and not line.startswith("->"):
                branch = line.lstrip("* ").strip()
                branches.append(branch)
        
        return branches


class AutoCommit:
    """Auto-commit converted files"""
    
    def __init__(self, repo_path: str = "."):
        self.git = GitIntegration(repo_path)
        self.auto_commit = os.getenv("AUTO_COMMIT", "false").lower() == "true"
        self.commit_message = os.getenv("COMMIT_MESSAGE", "feat: auto-generated files")
    
    def should_commit(self) -> bool:
        """Check if should auto-commit"""
        if not self.auto_commit:
            return False
        
        status = self.git.get_status()
        
        if not status:
            return False
        
        return len(status.modified) > 0 or len(status.untracked) > 0
    
    def auto_commit_changes(self) -> Optional[str]:
        """Auto-commit changes"""
        if not self.should_commit():
            return None
        
        status = self.git.get_status()
        
        # Add all new files
        all_files = status.modified + status.untracked
        self.git.add(*all_files)
        
        # Commit
        message = f"{self.commit_message}\n\nFiles: {len(all_files)}"
        
        return self.git.commit(message)


# Global instance
_git_integration: Optional[GitIntegration] = None


def get_git_integration(repo_path: str = ".") -> GitIntegration:
    """Get git integration"""
    global _git_integration
    if _git_integration is None:
        _git_integration = GitIntegration(repo_path)
    return _git_integration