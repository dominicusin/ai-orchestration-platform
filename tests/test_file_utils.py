"""Tests for File Utils"""

import os
import tempfile
from pathlib import Path

from orchestration.file_utils import (
    FileLock,
    atomic_write,
    clean_dir,
    ensure_dir,
    ensure_parent_dir,
    find_files,
    get_dir_size,
    get_file_hash,
    get_temp_dir,
    get_temp_file,
    safe_read,
    safe_write,
)


class TestEnsureDir:
    """Test ensure_dir"""

    def test_ensure_new_dir(self):
        """Test create new directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "new", "nested", "dir")
            result = ensure_dir(path)
            assert result.exists()
            assert result.is_dir()

    def test_ensure_existing_dir(self):
        """Test existing directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert result.exists()


class TestEnsureParentDir:
    """Test ensure_parent_dir"""

    def test_ensure_parent(self):
        """Test create parent directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "subdir", "file.txt")
            result = ensure_parent_dir(file_path)
            assert result.exists()


class TestSafeWriteRead:
    """Test safe write and read"""

    def test_write_read_text(self):
        """Test write and read text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = "Hello, World!"

            safe_write(file_path, content)
            result = safe_read(file_path)

            assert result == content

    def test_write_read_bytes(self):
        """Test write and read bytes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.bin")
            content = b"\x00\x01\x02\x03"

            safe_write(file_path, content, mode="wb")
            result = safe_read(file_path, mode="rb")

            assert result == content


class TestGetFileHash:
    """Test get_file_hash"""

    def test_sha256_hash(self):
        """Test SHA256 hash"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            safe_write(file_path, "test content")

            hash1 = get_file_hash(file_path, "sha256")
            hash2 = get_file_hash(file_path, "sha256")

            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 produces 64 hex chars


class TestGetDirSize:
    """Test get_dir_size"""

    def test_empty_dir(self):
        """Test empty directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            size = get_dir_size(tmpdir)
            assert size == 0

    def test_dir_with_files(self):
        """Test directory with files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            for i in range(3):
                safe_write(os.path.join(tmpdir, f"file{i}.txt"), "x" * 100)

            size = get_dir_size(tmpdir)
            assert size >= 300


class TestCleanDir:
    """Test clean_dir"""

    def test_clean_all(self):
        """Test clean all files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            for i in range(3):
                safe_write(os.path.join(tmpdir, f"file{i}.txt"), "content")

            count = clean_dir(tmpdir)
            assert count == 3

            # Directory should be empty
            assert len(os.listdir(tmpdir)) == 0

    def test_clean_with_keep(self):
        """Test clean with keep patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_write(os.path.join(tmpdir, "keep.txt"), "keep")
            safe_write(os.path.join(tmpdir, "delete.txt"), "delete")

            count = clean_dir(tmpdir, keep_patterns=["keep.txt"])
            assert count == 1
            assert Path(tmpdir, "keep.txt").exists()


class TestFindFiles:
    """Test find_files"""

    def test_find_all(self):
        """Test find all files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_write(os.path.join(tmpdir, "file1.txt"), "content")
            safe_write(os.path.join(tmpdir, "file2.txt"), "content")

            files = find_files(tmpdir, "*.txt", recursive=False)
            assert len(files) == 2

    def test_find_recursive(self):
        """Test find recursive"""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_write(os.path.join(tmpdir, "file1.txt"), "content")
            safe_write(os.path.join(tmpdir, "sub", "file2.txt"), "content")

            files = find_files(tmpdir, "*.txt", recursive=True)
            assert len(files) == 2


class TestTempDirFile:
    """Test temp dir and file"""

    def test_get_temp_dir(self):
        """Test get temp dir"""
        path = get_temp_dir()
        assert path.exists()
        assert path.is_dir()
        # Cleanup
        if path.exists():
            path.rmdir()

    def test_get_temp_file(self):
        """Test get temp file"""
        path = get_temp_file(suffix=".txt")
        assert path.exists()
        assert path.is_file()
        # Cleanup
        if path.exists():
            path.unlink()


class TestFileLock:
    """Test FileLock"""

    def test_lock(self):
        """Test file lock"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = os.path.join(tmpdir, "lock")
            lock = FileLock(lock_path)

            with lock:
                assert Path(lock_path).exists()

            assert not Path(lock_path).exists()


class TestAtomicWrite:
    """Test atomic_write"""

    def test_atomic_write(self):
        """Test atomic write"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "atomic.txt")
            content = "Atomic content"

            atomic_write(file_path, content)

            result = safe_read(file_path)
            assert result == content
