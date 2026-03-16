"""Code diff and patch system"""

import difflib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

logger = logging.getLogger("orchestration.diff")


@dataclass
class DiffResult:
    """Diff result"""
    original: str
    modified: str
    changes: List[str]
    stats: Dict[str, int]


@dataclass
class Patch:
    """Patch information"""
    original_hash: str
    modified_hash: str
    diff: str
    created_at: str


class CodeDiffer:
    """Compare and generate patches for code"""
    
    def __init__(self, context_lines: int = 3):
        self.context_lines = context_lines
    
    def diff_strings(self, original: str, modified: str) -> DiffResult:
        """Diff two strings"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile='original',
            tofile='modified',
            lineterm='',
            n=self.context_lines,
        )
        
        changes = list(diff)
        
        stats = {
            "additions": sum(1 for l in changes if l.startswith('+') and not l.startswith('+++')),
            "deletions": sum(1 for l in changes if l.startswith('-') and not l.startswith('---')),
            "total": len(changes),
        }
        
        return DiffResult(
            original=original,
            modified=modified,
            changes=changes,
            stats=stats,
        )
    
    def diff_files(self, file1: Path, file2: Path) -> DiffResult:
        """Diff two files"""
        original = file1.read_text() if file1.exists() else ""
        modified = file2.read_text() if file2.exists() else ""
        
        return self.diff_strings(original, modified)
    
    def apply_patch(self, original: str, patch: str) -> str:
        """Apply a patch to original text"""
        # Simple patch application (basic implementation)
        lines = original.splitlines(keepends=True)
        result = []
        
        i = 0
        while i < len(lines):
            # Check if this is a patch line
            if i < len(patch.splitlines()):
                patch_line = patch.splitlines()[i]
                
                if patch_line.startswith('+'):
                    result.append(patch_line[1:])
                elif patch_line.startswith('-'):
                    i += 1  # Skip original line
                    continue
                else:
                    result.append(lines[i])
            else:
                result.append(lines[i])
            
            i += 1
        
        return ''.join(result)


class PatchManager:
    """Manage code patches"""
    
    def __init__(self, patches_dir: str = "./patches"):
        self.patches_dir = Path(patches_dir)
        self.patches_dir.mkdir(parents=True, exist_ok=True)
    
    def create_patch(
        self,
        original: str,
        modified: str,
        name: str,
        metadata: Dict = None,
    ) -> Patch:
        """Create a patch"""
        differ = CodeDiffer()
        diff_result = differ.diff_strings(original, modified)
        
        patch = Patch(
            original_hash=hashlib.md5(original.encode()).hexdigest(),
            modified_hash=hashlib.md5(modified.encode()).hexdigest(),
            diff=''.join(diff_result.changes),
        )
        
        # Save patch
        patch_file = self.patches_dir / f"{name}.patch"
        patch_file.write_text(patch.diff)
        
        logger.info(f"Created patch: {name}")
        
        return patch
    
    def apply_patch(self, original: str, patch_name: str) -> Optional[str]:
        """Apply a named patch"""
        patch_file = self.patches_dir / f"{patch_name}.patch"
        
        if not patch_file.exists():
            logger.error(f"Patch not found: {patch_name}")
            return None
        
        patch = patch_file.read_text()
        
        differ = CodeDiffer()
        return differ.apply_patch(original, patch)
    
    def list_patches(self) -> List[str]:
        """List all patches"""
        return [p.stem for p in self.patches_dir.glob("*.patch")]


class VersionControl:
    """Simple version control for converted files"""
    
    def __init__(self, versions_dir: str = "./versions"):
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_version(
        self,
        file_path: str,
        content: str,
        metadata: Dict = None,
    ) -> str:
        """Save a version of a file"""
        import json
        from datetime import datetime
        
        file_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        version_name = f"{Path(file_path).stem}_{timestamp}_{file_hash}"
        version_file = self.versions_dir / f"{version_name}.txt"
        
        version_file.write_text(content)
        
        # Save metadata
        meta_file = self.versions_dir / f"{version_name}.meta.json"
        meta = {
            "original_path": file_path,
            "hash": file_hash,
            "timestamp": timestamp,
            "size": len(content),
            "metadata": metadata or {},
        }
        meta_file.write_text(json.dumps(meta, indent=2))
        
        return version_name
    
    def get_versions(self, file_path: str) -> List[Dict]:
        """Get all versions of a file"""
        import json
        
        stem = Path(file_path).stem
        versions = []
        
        for meta_file in self.versions_dir.glob(f"{stem}_*.meta.json"):
            try:
                meta = json.loads(meta_file.read_text())
                versions.append(meta)
            except Exception:
                continue
        
        return sorted(versions, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    def restore_version(self, version_name: str) -> Optional[str]:
        """Restore a specific version"""
        version_file = self.versions_dir / f"{version_name}.txt"
        
        if version_file.exists():
            return version_file.read_text()
        
        return None


class ConflictResolver:
    """Resolve conflicts in converted code"""
    
    def __init__(self):
        self.resolution_strategies = {
            "ours": self._keep_ours,
            "theirs": self._keep_theirs,
            "both": self._keep_both,
            "manual": None,
        }
    
    def detect_conflicts(
        self,
        original: str,
        modified: str,
        base: str,
    ) -> List[Tuple[int, str, str]]:
        """Detect conflicting sections"""
        # Simple conflict detection
        # In real implementation would use proper 3-way merge
        conflicts = []
        
        orig_lines = original.splitlines()
        mod_lines = modified.splitlines()
        base_lines = base.splitlines()
        
        for i, (orig, mod, bs) in enumerate(zip(orig_lines, mod_lines, base_lines)):
            if orig != bs and mod != bs and orig != mod:
                conflicts.append((i, orig, mod))
        
        return conflicts
    
    def resolve(
        self,
        original: str,
        modified: str,
        base: str,
        strategy: str = "ours",
    ) -> str:
        """Resolve conflicts using strategy"""
        conflicts = self.detect_conflicts(original, modified, base)
        
        if not conflicts:
            return modified
        
        resolve_func = self.resolution_strategies.get(strategy)
        
        if resolve_func is None:
            # Manual resolution required
            return f"<<<<<<< ORIGINAL\n{original}\n=======\n{modified}\n>>>>>>> MODIFIED"
        
        return resolve_func(original, modified, conflicts)
    
    def _keep_ours(self, original: str, modified: str, conflicts: List) -> str:
        """Keep our changes (modified)"""
        return modified
    
    def _keep_theirs(self, original: str, modified: str, conflicts: List) -> str:
        """Keep their changes (original)"""
        return original
    
    def _keep_both(self, original: str, modified: str, conflicts: List) -> str:
        """Keep both versions"""
        lines = modified.splitlines()
        
        for idx, orig_line, mod_line in conflicts:
            lines[idx] = f"# CONFLICT: original={orig_line} modified={mod_line}"
        
        return "\n".join(lines)
