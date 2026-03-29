"""Hashlib utilities"""

import hashlib


def md5(data: str | bytes, hex: bool = True) -> str:
    """MD5 hash"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest() if hex else hashlib.md5(data).digest()


def sha1(data: str | bytes, hex: bool = True) -> str:
    """SHA1 hash"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha1(data).hexdigest() if hex else hashlib.sha1(data).digest()


def sha256(data: str | bytes, hex: bool = True) -> str:
    """SHA256 hash"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest() if hex else hashlib.sha256(data).digest()


def sha512(data: str | bytes, hex: bool = True) -> str:
    """SHA512 hash"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha512(data).hexdigest() if hex else hashlib.sha512(data).digest()


def blake2b(data: str | bytes, hex: bool = True) -> str:
    """BLAKE2b hash"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.blake2b(data).hexdigest() if hex else hashlib.blake2b(data).digest()
