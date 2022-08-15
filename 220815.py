from pprint import pprint
from typing import Dict, Tuple, List


class LRParser:
    class Transitions:
        def __init__(self):
            self.forward = str
            pass

    class State:
        def __init__(self, mutations: List[Tuple[str, List[str]]]):
            self.mutations: List[Tuple[str, List[str]]] = mutations
            self.transitions = []

    def __init__(self):
        self.states: Dict[int, LRParser.State] = {}
        self.__state_seq__ = 0
        self.original_grammar = [
            ('E', ['E', '+', 'T']),
            ('E', ['T']),
            ('T', ['T', '*', 'F']),
            ('T', ['F']),
            ('F', ['(', 'E', ')']),
            ('F', ['id']),
        ]
        pprint(self.original_grammar)

        self.add_initial_state()

        self.make_transitions(self.states[0])

    @property
    def state_seq(self) -> int:
        return self.__state_seq__

    def increase_state_seq(self):
        self.__state_seq__ += 1

    def add_initial_state(self):
        mutations = []
        for left_hand, right_hand in self.original_grammar:
            mutations.append(
                (left_hand, ['·'] + right_hand)
            )

        self.states[self.state_seq] = LRParser.State(mutations=mutations)
        self.increase_state_seq()

    def make_transitions(self, state: 'LRParser.State'):
        pass
        pprint(state.mutations)
        for left_hand, right_hand in state.mutations:
            print('left_hand =', left_hand)
            print('right_hand=', right_hand)

    '''
    goto_table =====================
     the net state after a shift
    
    action_table parser will do one of these
    - shift(S)
    - reduce(R)
    - accept(A)
    - error(E)
    
    dot symbol(·) marks how much of the production has already been matched.
    grammar G ============================
               | => | E' -> ·E
    E -> E+T   | => | E -> ·E+T   
    E -> T     | => | E -> ·T     
    T -> T*F   | => | T -> ·T*F   
    T -> F     | => | T -> ·F     
    F -> (E)   | => | F -> ·(E)   
    F -> id    | => | F -> ·id    
    E' means the start state of G

    ref ============================
    https://www.youtube.com/watch?v=iBb3Dfx695I
    
    '''

    def parsing(self):
        self.inputs = ['id', '*', 'id', '$']


if __name__ == '__main__':
    LRParser()
