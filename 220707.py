from collections import defaultdict
from dataclasses import dataclass
from pprint import pprint
from typing import List

tokens = [
    'int',
    '*',
    'int',
    '+',
    'int',
    '*',
    '(',
    'int',
    '+',
    'int',
    ')',
    '$'
]


# E -> T + E
# E -> T
# T -> int * T
# T -> int
@dataclass
class Expr:
    pronoun: str
    word: List[str]


expr_list = [
    Expr('E', ['T', '+', 'E']),
    Expr('E', ['T']),
    Expr('T', ['int', '*', 'T']),
    Expr('T', ['int', ]),
    Expr('T', ['(', 'E', ')']),
]


def is_symbol(text: str):
    return text in ('int', '*', '(', ')', '+')


first_map = defaultdict(lambda: set())
changed = True
for expr in expr_list:
    first_map[expr.pronoun].add(expr.word[0])
unestablished = set(first_map.keys())
while changed:
    changed = False

    for expr_name in set(unestablished):
        for token in first_map[expr_name]:
            if is_symbol(token) is False:
                break
        else:
            unestablished.discard(expr_name)
            changed = True
            first_map[expr_name].discard(expr_name)
            for x in unestablished:
                if x != expr_name:
                    first_map[x].discard(expr_name)
                    first_map[x] |= first_map[expr_name]

    pprint(first_map)
changed = True
stack = []
buffer = []
while changed:
    changed = False
    head = tokens[-1]
    print('=' * 80)
    print(f'left: {tokens}')
    print(f'head: {head!r}')
    print(f'stck: {stack!r}')
    print(f'buff: {buffer!r}')

    for expr in expr_list:
        first = expr.word[0]
        if is_symbol(first) is False:
            first_set = first_map[first]
        else:
            first_set = {first}
        follow = expr.word[-1]
        print(f'expr[{expr.pronoun}]: {first_set!r} ··· {follow!r}')

