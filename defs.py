from typing import Union


class Pos:
    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col


class Token:
    def __init__(self, tag: str, value: Union[str, list, None], pos: Pos):
        self.tag = tag
        self.value = value
        self.pos = Pos(line=pos.line, col=pos.col)

    def __str__(self):
        return f'<{self.__class__.__name__}({self.tag!r}) {self.value!r} at line {self.pos.line}:{self.pos.col}>'

    def __repr__(self):
        return self.__str__()
