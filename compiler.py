import sys
import traceback
from itertools import tee
from typing import Optional, Tuple, Type, Union, Iterator

from defs import Token, Pos
from syntax.common import str_cursor, CompilerError, NotFit, IgnoreCase, AnyChar, Whitespace
from syntax.identifier import Identifier, OneOf


class Opt:
    def __init__(self, value, name: str):
        self.name = name
        self.value = value


class Constant:
    hexadecimal_prefix = OneOf('0x', '0X')
    nonzero_digit = OneOf(*'123456789')
    digit = OneOf(*'0123456789')
    octal_digit = OneOf(*'1234567')
    hexadecimal_digit = OneOf(*'0123456789abcdefABCDEF')
    decimal_constant = OneOf(
        nonzero_digit,
        ('tag=decimal_constant', digit),
    )
    octal_constant = OneOf(
        '0',
        ('tag=octal_constant', octal_digit),
    )

    hexadecimal_constant = OneOf(
        (hexadecimal_prefix, hexadecimal_digit),
        ('tag=hexadecimal_constant', hexadecimal_digit),
    )

    unsigned_suffix = OneOf(*'uU')
    long_suffix = OneOf(*'lL')
    long_long_suffix = OneOf('ll', 'LL')
    integer_suffix = OneOf(
        [unsigned_suffix, Opt(long_suffix, name='long_suffix')],
        [unsigned_suffix, long_long_suffix],
        [long_suffix, Opt(unsigned_suffix, name='unsigned_suffix')],
        [long_long_suffix, Opt(unsigned_suffix, name='unsigned_suffix')],
    )

    integer_constant = OneOf(
        [decimal_constant, Opt(integer_suffix, name='integer_suffix')],
        [octal_constant, Opt(integer_suffix, name='integer_suffix')],
        [hexadecimal_constant, Opt(integer_suffix, name='integer_suffix')],
        name='integer_constant'
    )

    digit_sequence = OneOf(
        digit,
        ('tag=digit_sequence', digit),
    )
    fractional_constant = [
        [Opt(digit_sequence, name='digit_sequence'), '.', digit_sequence],
        [digit_sequence, '.'],
    ]
    sign = OneOf(*"+-")
    exponent_part = OneOf(
        ['e', Opt(sign, name='sign'), digit_sequence],
        ['E', Opt(sign, name='sign'), digit_sequence],
    )

    hexadecimal_digit_sequence = OneOf(
        hexadecimal_digit,
        ('tag=hexadecimal_digit_sequence', hexadecimal_digit),
    )
    binary_exponent_part = OneOf(
        ['p', Opt(sign, name='sign'), digit_sequence],
        ['P', Opt(sign, name='sign'), digit_sequence],
    )

    hexadecimal_fractional_constant = [
        [Opt(hexadecimal_digit_sequence, name='hexadecimal_digit_sequence'), '.', hexadecimal_digit_sequence],
        [hexadecimal_digit_sequence, '.'],
    ]
    floating_suffix = OneOf(*'flFL')

    enumeration_constant = Identifier

    decimal_floating_constant = OneOf(
        [fractional_constant, Opt(exponent_part, name='exponent_part'), Opt(floating_suffix, name='floating_suffix')],
        [digit_sequence, exponent_part, Opt(floating_suffix, name='floating_suffix')],
    )
    hexadecimal_floating_constant = OneOf(
        [hexadecimal_prefix, hexadecimal_fractional_constant, Opt(binary_exponent_part, name='exponent_part'),
         Opt(floating_suffix, name='floating_suffix')],
        [hexadecimal_prefix, hexadecimal_digit_sequence, binary_exponent_part,
         Opt(floating_suffix, name='floating_suffix')],
    )
    floating_constant = OneOf(
        decimal_floating_constant,
        hexadecimal_floating_constant,
        name='floating_constant'
    )

    class AnyCharInCChar(AnyChar):
        blacklist = '\'\\\n'
        size = 1
        lazy = False

    simple_escape_sequence = OneOf(r'\'', r'\*', r'\?', r'\\', r'\a', r'\b', r'\f', r'\n', r'\r', r'\t', r'\v', )
    octal_escape_sequence = OneOf(
        ('\\', octal_digit),
        ('\\', octal_digit, octal_digit),
        ('\\', octal_digit, octal_digit, octal_digit),
    )
    hexadecimal_escape_sequence = OneOf(
        ('\\x', hexadecimal_digit),
        ('tag=hexadecimal_escape_sequence', hexadecimal_digit),
    )
    escape_sequence = OneOf(
        octal_escape_sequence,
        simple_escape_sequence,
        hexadecimal_escape_sequence,
        Identifier.universal_character_name,
    )

    c_char = OneOf(
        AnyCharInCChar,
        escape_sequence
    )
    c_char_sequence = OneOf(
        c_char,
        ('tag=c_char_sequence', c_char)
    )

    character_constant = OneOf(
        ["'", c_char_sequence, "'"],
        ["L'", c_char_sequence, "'"],
        ["u'", c_char_sequence, "'"],
        ["U'", c_char_sequence, "'"],
        name='character_constant'
    )

    constant = [OneOf(
        integer_constant,
        floating_constant,
        character_constant,
    )]


class LexConfig:
    multi_comment = OneOf(
        ('/*', AnyChar, '*/'),
    )
    whitespaces = OneOf(
        Whitespace,
        ('tag=whitespaces', Whitespace)
    )
    exec_sql = OneOf(
        (IgnoreCase('EXEC'), AnyChar, ';')
    )
    identifier = Identifier.identifier

    constant = Constant.constant


class Compiler:
    def __init__(self, content: str):
        self.verbose = False
        self.curr_tokens = []
        self.next_tokens = []
        pos = Pos(1, 1)
        for ch in content:
            self.curr_tokens.append(Token('ch', ch, pos))
            if ch == '\n':
                pos.line += 1
                pos.col = 1
            else:
                pos.col += 1
        self.run_epoch()

    def run_epoch(self):

        matched = 0
        while True:
            curr = iter(self.curr_tokens)
            curr, forward = tee(curr)
            try:
                forward_token = next(forward)
                if forward_token.pos.line == 37:
                    self.verbose = True
                else:
                    self.verbose = False
            except StopIteration:
                if matched > 0:
                    matched = 0
                    self.curr_tokens = self.next_tokens
                    self.next_tokens = []
                    continue
                else:
                    break
            print('●' * 3, f'START PARSE[{forward_token.pos.line};{forward_token.pos.col}]]', str_cursor(curr))
            new_token: Optional[Token] = None
            new_cursor: Optional[Iterator[Token]] = None
            for attr_name in LexConfig.__dict__:
                if attr_name in {'__dict__', '__weakref__', '__module__', '__doc__'}:
                    continue

                lex_conf = getattr(LexConfig, attr_name)

                try:
                    new_token, new_cursor = self.run_lex_item(lex_item=lex_conf, cursor=curr)
                    new_token.tag = attr_name
                except StopIteration as e:
                    print('●' * 3, 'BREAK by', 'Unexpected EOF')
                    pass
                except CompilerError as e:
                    if attr_name in {'1'}:
                        print('●' * 3, 'BREAK ' * 5, e)
                        traceback.print_exc(file=sys.stdout)
                    pass

                if new_token is not None:
                    print('●' * 3, 'COMMIT')
                    matched += 1
                    new_cursor, dup = tee(new_cursor)
                    new_forward_token = next(dup)
                    n = 0
                    for token in curr:
                        if token == new_forward_token:
                            break
                        n += 1

                    print('●' * 3, f'del[{n}]', self.curr_tokens[:n])
                    self.curr_tokens = [new_token] + self.curr_tokens[n:]
                    print('●' * 3, 'curr', self.curr_tokens[:5])
                    break
            else:
                print('●' * 3, 'PASS')
                assert new_token is None
                self.next_tokens.append(forward_token)
                print('●' * 3, 'prev', self.curr_tokens[:5])
                if forward_token == self.curr_tokens[0]:
                    self.curr_tokens = self.curr_tokens[1:]
                print('●' * 3, 'passed', forward_token)
                print('●' * 3, 'curr', self.curr_tokens[:5])

        buffer = None
        for token in self.next_tokens:
            if token.tag == 'ch':
                if buffer is None:
                    buffer = ''
                buffer += token.value
            else:
                if buffer is not None:
                    print(repr(buffer))
                    buffer = None
                print(token)
        if buffer:
            print(repr(buffer))

    def run_lex_item(self, *, lex_item: Union[str, Type, list], cursor: Iterator[Token], lex_next: Optional = None,
                     depth: int = 0) -> \
            Tuple[Token, Iterator[Token]]:

        _, cursor = tee(cursor, 2)
        indent = '  ' * depth + '├'
        try:
            if self.verbose:
                print(indent)
                print(indent, '>' * 20, 'cursor', str_cursor(cursor))
                print(indent, '=' * 20, f'lex_item={lex_item!r}')

            result: Optional[Token] = None
            last_cursor: Optional[Iterator[Token]] = None
            if type(lex_item) in (str, IgnoreCase):
                if type(lex_item) == str and lex_item.startswith('tag='):
                    tag_name = lex_item[4:]
                    new_token = next(cursor)
                    if new_token.tag == tag_name:
                        result = new_token
                        last_cursor = cursor
                    else:
                        raise NotFit(f'{new_token} is not {tag_name!r}')
                else:
                    if type(lex_item) is str:
                        text = lex_item
                    else:
                        text = lex_item.value

                    for lex_ch in text:
                        new_token = next(cursor)
                        if new_token.tag != 'ch':
                            raise NotFit(f'{new_token.tag!r} != ch')
                        new_ch = new_token.value
                        if type(lex_item) is IgnoreCase:
                            new_ch = new_ch.upper()
                        if new_ch != lex_ch:
                            raise NotFit(f'{new_token} != {lex_ch!r}')
                        else:
                            if self.verbose:
                                print(indent, 'Fit', new_token, '==', f'{lex_ch!r}')
                        if result is None:
                            result = Token(tag='str', pos=new_token.pos, value=new_token.value)
                        else:
                            result.value += new_token.value
                        cursor, last_cursor = tee(cursor)
                    last_cursor = cursor
            elif type(lex_item) is type:
                if lex_item is AnyChar or AnyChar in lex_item.__bases__:
                    lex_item: Type[AnyChar] = lex_item
                    result = None
                    if lex_item.lazy:
                        if lex_next is None:
                            raise NotFit(f'lazy={lex_item.lazy}, lex_next={lex_next!r}')
                    cursor, dup = tee(cursor)
                    for new_token in cursor:
                        if new_token.tag != 'ch':
                            raise NotFit(f'{new_token.tag!r} != ch')
                        if lex_item.lazy:
                            try:
                                new_token, new_cursor = self.run_lex_item(lex_item=lex_next, cursor=dup,
                                                                          depth=depth + 1)
                                last_cursor = dup
                                if self.verbose:
                                    print(indent, 'AnyChar Break')
                                break
                            except CompilerError as e:
                                if self.verbose:
                                    print(indent, 'AnyChar Continue', e)
                                next(dup)
                                pass

                        if lex_item.whitelist is not None:
                            if new_token.value not in lex_item.whitelist:
                                if result is None:
                                    raise NotFit(f'{new_token.value!r} not in {lex_item.whitelist!r}')
                                else:
                                    break
                        if lex_item.blacklist is not None:
                            if new_token.value in lex_item.blacklist:
                                if result is None:
                                    raise NotFit(f'{new_token.value!r} in {lex_item.blacklist!r}')
                                else:
                                    break
                        if result is None:
                            result = Token(tag='str', pos=new_token.pos, value=new_token.value)
                        else:
                            result.value += new_token.value
                        cursor, last_cursor = tee(cursor)
                        if len(result.value) == lex_item.size:
                            break
                    else:
                        raise CompilerError('Unexpected EOF')
                else:
                    raise NotImplementedError(f'Not expected {lex_item}')
            elif isinstance(lex_item, OneOf):
                for lex_conf in lex_item.branches:
                    try:
                        cursor, dup = tee(cursor)
                        result, last_cursor = self.run_lex_item(lex_item=lex_conf, cursor=dup, depth=depth + 1)
                        if lex_item.name is not None:
                            result.tag = lex_item.name
                        break
                    except CompilerError as e:
                        pass
                else:
                    raise NotFit(f'{lex_item} cannot match')
            elif isinstance(lex_item, Opt):
                try:
                    cursor, dup = tee(cursor)
                    result, last_cursor = self.run_lex_item(lex_item=lex_item.value, cursor=dup, depth=depth + 1)
                    result.tag = lex_item.name
                except CompilerError as e:
                    cursor, dup = tee(cursor)
                    new_token = next(dup)
                    result, last_cursor = Token(tag=lex_item.name, pos=new_token.pos, value=None), cursor
            elif type(lex_item) in (list, tuple):
                for k, child_lex_item in enumerate(lex_item):
                    if k + 1 < len(lex_item):
                        next_child_lex_item = lex_item[k + 1]
                    else:
                        next_child_lex_item = None
                    try:
                        new_token, new_cursor = self.run_lex_item(
                            lex_item=child_lex_item,
                            cursor=cursor,
                            lex_next=next_child_lex_item,
                            depth=depth + 1
                        )
                        if type(lex_item) == list:
                            if result is None:
                                result = Token(tag='list', pos=new_token.pos, value=[new_token])
                            else:
                                result.value.append(new_token)
                        elif type(lex_item) == tuple:
                            if result is None:
                                result = Token(tag='str', pos=new_token.pos, value=new_token.value)
                            else:
                                assert new_token.tag in ('ch', 'str'), new_token
                                assert result.tag in ('ch', 'str'), result
                                result.value += new_token.value
                        cursor = new_cursor
                    except CompilerError:
                        # traceback.print_exc()
                        raise NotFit('child_lex_item')
                last_cursor = cursor

            else:
                raise NotImplementedError(f'{lex_item.__class__.__name__} -> {lex_item!r}')

            assert last_cursor is not None, (lex_item.__class__, lex_item)
            assert result is not None, (lex_item.__class__, lex_item)
            if self.verbose:
                print(indent, 'RESULT     ', f'{lex_item!r}', result)
                print(indent, 'LAST_CURSOR', f'{lex_item!r}', str_cursor(last_cursor))
            return result, last_cursor
        finally:
            if self.verbose:
                print(indent, 'EXITED     ', f'{lex_item!r}')
