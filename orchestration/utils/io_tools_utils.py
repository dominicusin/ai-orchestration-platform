"""IO tools utilities"""

import io


def stringio_2(s=""):
    """StringIO"""
    return io.StringIO(s)


def bytesio_2(b=b""):
    """BytesIO"""
    return io.BytesIO(b)
