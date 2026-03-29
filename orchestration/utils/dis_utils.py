"""Dis utilities"""

import dis
from collections.abc import Callable


def disassemble(func: Callable) -> str:
    """Disassemble function"""
    import io
    output = io.StringIO()
    dis.dis(func, file=output)
    return output.getvalue()


def get_bytecode(func: Callable) -> list:
    """Get bytecode instructions"""
    return list(dis.get_instructions(func))


def bytecode_info(func: Callable) -> dict:
    """Get bytecode info"""
    instructions = dis.get_instructions(func)
    return {
        "argcount": func.__code__.co_argcount,
        "varnames": func.__code__.co_varnames,
        "names": func.__code__.co_names,
        "instructions": [str(i) for i in instructions]
    }
