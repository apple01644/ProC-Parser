import sys
from typing import List


class Tree:
    def __init__(self, token: str):
        self.token = token
        self.child: List[Tree] = []
        self.hold = False

    def __repr__(self):
        if self.hold:
            return f'#T[{self.token!r}]'
        else:
            return f'#T<{self.token!r}>'


class Compiler:
    def __init__(self):
        self.content = [
            Tree(x) for x in 'S'
        ]
        self.target = [
            x for x in 'aabbcc'
        ]
        print('=' * 60)
        self.print_tree(self.content)
        self.keep_going = True
        c = 0
        while self.keep_going:
            c += 1
            self.run_epoch()
            print('=' * 60)
            self.print_tree(self.content)
            if c > 10:
                break
        pass

    def print_tree(self, data_list: List[Tree], depth: int = 0):
        for i, data in enumerate(data_list):
            prefix = ' '
            if depth == 0 and i < len(self.target):
                prefix = self.target[i]
            print(prefix, ' -> ' * depth, data)
            if data.child:
                self.print_tree(data.child, depth=depth + 1)

    def run_epoch(self):
        self.keep_going = True
        continuous_hold = True
        for i, x in enumerate(self.content):
            able_to_target = [i + a < len(self.target) for a in range(10)]
            able_to_token = [i + a < len(self.content) for a in range(10)]

            if continuous_hold and able_to_target[0] and x.token == self.target[i]:
                x.hold = True

            if x.hold:
                pass
            else:
                continuous_hold = False

            # 2. S => a b c
            print(self.target[i:i + 3])
            if x.token == 'S' and able_to_target[2] and self.target[i:i + 2] == ['a', 'b']:
                print('ggg', file=sys.stderr)
                self.content = \
                    self.content[0:i] + \
                    [Tree(s) for s in ['a', 'b', 'c']] + \
                    self.content[i + 1:]
                print(self.content, file=sys.stderr)
                break

            # 1. S => a S Q
            if x.token == 'S' and able_to_target[0] and self.target[i] == 'a':
                print('ggg', file=sys.stderr)
                self.content = \
                    self.content[0:i] + \
                    [Tree(s) for s in ['a', 'S', 'Q']] + \
                    self.content[i + 1:]
                print(self.content, file=sys.stderr)
                break

            # 3. b Q c => b b c c
            if able_to_token[2] and [self.content[i + a].token for a in range(3)] == ['b', 'Q', 'c'] and \
                    able_to_target[2] and self.target[i] == 'b':
                self.content = \
                    self.content[0:i] + \
                    [Tree(s) for s in ['b', 'b', 'c', 'c']] + \
                    self.content[i + 3:]
                print(self.content, file=sys.stderr)
                break

            # 4. c Q => Q c
            if able_to_token[1] and [self.content[i + a].token for a in range(2)] == ['c', 'Q'] and \
                    able_to_target[1] and self.target[i + 1] == 'c':
                self.content = \
                    self.content[0:i] + \
                    [Tree(s) for s in ['Q', 'c']] + \
                    self.content[i + 2:]
                print(self.content, file=sys.stderr)
                break
        else:
            self.keep_going = False


if __name__ == '__main__':
    Compiler()
