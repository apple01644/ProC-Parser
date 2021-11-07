from syntax.common import AnyChar


class NonDigit(AnyChar):
    lazy = False
    whitelist = '_' + \
                'abcdefghijklmnopqrstuvwxyz' + \
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    size = 1


class Digit(AnyChar):
    lazy = False
    whitelist = '0123456789'
    size = 1


class HexademicalDigit(AnyChar):
    lazy = False
    whitelist = '0123456789ABCDEFabcdef'
    size = 1


class OneOf:
    def __init__(self, *args, name:str=None):
        self.branches = args
        self.name = name

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.branches!r}>'

    def __str__(self):
        return self.__repr__()


class Identifier:
    hex_quad = tuple([HexademicalDigit] * 4)
    universal_character_name = OneOf(
        ('\\u', hex_quad),
        ('\\U', hex_quad, hex_quad),
    )

    identifier_nondigit = OneOf(
        NonDigit,
        universal_character_name
    )

    identifier = [
        identifier_nondigit,
        ('tag=identifier', identifier_nondigit),
        ('tag=identifier', Digit)
    ]
