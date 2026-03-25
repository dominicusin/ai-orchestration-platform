"""IO tools2 utilities"""

import io


def stringio_3(s=""):
    """StringIO"""
    return io.StringIO(s)


def bytesio_3(b=b""):
    """BytesIO"""
    return io.BytesIO(b)
