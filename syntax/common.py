import string
from itertools import tee
from typing import Sequence, Iterator

from defs import Token


class AnyChar:
    lazy = True
    whitelist: Sequence[str] = None
    blacklist: Sequence[str] = None
    size = 0


class IgnoreCase:
    def __init__(self, value: str):
        self.value = value


class Whitespace(AnyChar):
    whitelist = string.whitespace
    lazy = False


class CompilerError(BaseException):
    pass


class NotFit(CompilerError):
    pass


class NotSupportedType(CompilerError):
    pass


def str_cursor(cursor: Iterator[Token]):
    cursor, _ = tee(cursor)
    return str(next(_))
