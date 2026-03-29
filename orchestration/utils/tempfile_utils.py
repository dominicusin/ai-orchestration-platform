"""Tempfile utilities"""

import os
import tempfile


def temp_file(suffix: str = "", prefix: str = "tmp") -> str:
    """Create temporary file"""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


def temp_dir(prefix: str = "tmp") -> str:
    """Create temporary directory"""
    return tempfile.mkdtemp(prefix=prefix)


def temp_named_file(mode: str = 'w', suffix: str = "", prefix: str = "tmp"):
    """Create named temporary file"""
    return tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, prefix=prefix, delete=False)


def cleanup_temp_files(pattern: str = "tmp*"):
    """Clean up temporary files"""
    import glob
    for f in glob.glob(f"/tmp/{pattern}"):
        try:
            os.remove(f)
        except OSError:
            pass
