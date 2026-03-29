"""Decimal utilities"""

from decimal import ROUND_HALF_UP, Decimal


def dec(value: str | int | float) -> Decimal:
    """Create decimal"""
    return Decimal(str(value))


def dec_add(a: Decimal, b: Decimal) -> Decimal:
    """Add decimals"""
    return a + b


def dec_sub(a: Decimal, b: Decimal) -> Decimal:
    """Subtract decimals"""
    return a - b


def dec_mul(a: Decimal, b: Decimal) -> Decimal:
    """Multiply decimals"""
    return a * b


def dec_div(a: Decimal, b: Decimal) -> Decimal:
    """Divide decimals"""
    return a / b


def dec_quantize(value: Decimal, places: int) -> Decimal:
    """Quantize decimal"""
    quantize_str = '0.' + '0' * places
    return value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
