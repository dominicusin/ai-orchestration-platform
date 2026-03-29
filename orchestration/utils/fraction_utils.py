"""Fractions utilities"""

from fractions import Fraction


def fraction_from_float(value: float) -> Fraction:
    """Create fraction from float"""
    return Fraction(value).limit_denominator(1000)


def fraction_from_str(value: str) -> Fraction:
    """Create fraction from string"""
    return Fraction(value)


def fraction_add(a: Fraction, b: Fraction) -> Fraction:
    """Add fractions"""
    return a + b


def fraction_sub(a: Fraction, b: Fraction) -> Fraction:
    """Subtract fractions"""
    return a - b


def fraction_mul(a: Fraction, b: Fraction) -> Fraction:
    """Multiply fractions"""
    return a * b


def fraction_div(a: Fraction, b: Fraction) -> Fraction:
    """Divide fractions"""
    return a / b
