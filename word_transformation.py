import dataclasses
from enum import Enum
from typing import List, Tuple

def simple_string_distance(s : str, t : str) -> int:
    m = len(s)
    n = len(t)
    v0 = list(range(n+1))
    v1 = [0]*(n+1)
    for i in range(m):
        v1[0] = i + 1
        for j in range(n):
            # // calculating costs for A[i + 1][j + 1]
            deletionCost = v0[j + 1] + 1
            insertionCost = v1[j] + 1
            substitutionCost = v0[j] if s[i] == t[j] else v0[j]+1
            v1[j + 1] = min(deletionCost, insertionCost, substitutionCost)
        v0, v1 = v1, v0 # swap
    return v0[n]

Position = Tuple[int, int]

BOS = '^'
EOS = '$'
EMPTY = '∅'

class Operator(Enum):
    NOP = 'nop'
    INS = 'ins'
    DEL = 'del'
    SUB = 'sub'

@dataclasses.dataclass
class Operation:
    op : Operator
    d_in : str
    d_out : str
    str_rep : str = ''
    def __post_init__(self):
        self.str_rep = self.op.value
        if self.op == Operator.NOP:
            if self.d_in != self.d_out: raise Exception('NOP means no change!')
            return
        elif self.op == Operator.DEL:
            if self.d_out: raise Exception('DEL means no output!')
            self.str_rep += ' ' + self.d_in
        elif self.op == Operator.SUB:
            self.str_rep = '%s->%s' % (self.d_in, self.d_out)
        elif self.op == Operator.INS:
            if self.d_in != '': raise Exception('INS means no input!')
            self.str_rep = 'ins %s' % (self.d_out)
    @staticmethod
    def Nop(what : str = '') -> 'Operation':
        return Operation(Operator.NOP, what, what)
    @staticmethod
    def Del(what : str) -> 'Operation':
        return Operation(Operator.DEL, what, '')
    @staticmethod
    def Sub(what : str, withWhat : str) -> 'Operation':
        return Operation(Operator.SUB, what, withWhat)
    @staticmethod
    def Ins(what : str) -> 'Operation':
        return Operation(Operator.INS, '', what)
    def __str__(self):
        return self.str_rep
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        return self.op == other.op and self.d_in == other.d_in and self.d_out == other.d_out
@dataclasses.dataclass(frozen=True)
class Modification:
    op : Operation = dataclasses.field(default_factory=Operation.Nop)
    score : int = 0
    from_pos : Position = (-1, -1)
    def __str__(self):
        return '(%s -> %s)' % (str(self.from_pos), str(self.op))
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        return self.op == other.op and self.score == other.score


@dataclasses.dataclass
class MatrixCell:
    modifications : List[Modification] = dataclasses.field(default_factory=list)
    score : int = 0
    def __post_init__(self):
        if self.modifications:
            if min([m.score for m in self.modifications]) != max([m.score for m in self.modifications]):
                raise Exception('Unequal scores in cell!')
            self.score = self.modifications[0].score
    def __str__(self):
        return '%d %s' % (self.score, str(self.modifications))
    def __repr__(self):
        return str(self)

# ModMatrix = List[List[Mod]]
class ModMatrix(List[List[MatrixCell]]):
    def __init__(self, rows : int, cols : int):
        super().__init__([[MatrixCell() for j in range(cols)] for i in range(rows)])
        self.rows = rows
        self.cols = cols
    def at(self, *args): #pos : Tuple[int, int]):
        if len(args) == 1 and len(args[0]) == 2:
            pos = args[0]
        elif len(args) == 2:
            pos = (args[0], args[1])
        else:
            raise Exception('Number of args must be 1 or 2')
        return self[pos[0]][pos[1]]




def add_BOS_EOS(s : str | List[str]) -> str | List[str]:
    if isinstance(s, str):
        return BOS + s + EOS
    return [BOS] + s + [EOS]

def distance(w1 : str|List[str], w2 : str|List[str]) -> ModMatrix:
    w1, w2 = add_BOS_EOS(w1), add_BOS_EOS(w2)
    rows = len(w1)
    cols = len(w2)
    matrix = ModMatrix(rows, cols)
    # init edges of matrix
    for i in range(1, rows):
        # matrix[i][0] = MatrixCell([Modification('del %s' % w1[i], i, (i - 1, 0))])
        matrix[i][0] = MatrixCell([Modification(Operation.Del(w1[i]), i, (i - 1, 0))])
    for j in range(1, cols):
        # matrix[0][j] = MatrixCell([Modification('ins %s' % w2[j], j, (0, j - 1))])
        matrix[0][j] = MatrixCell([Modification(Operation.Ins(w2[j]), j, (0, j - 1))])
    # populate matrix
    for j in range(1, cols):
        for i in range(1, rows):
            substitution_cost = 0 if w1[i] == w2[j] else 1
            # substition_string = '%s->%s' % (w1[i], w2[j]) if substitution_cost else 'nop'
            substition_op = Operation.Sub(w1[i], w2[j]) if substitution_cost else Operation.Nop(w1[i])
            options = [#Modification('del %s' % w1[i], matrix[i - 1][j].score + 1, (i - 1, j)),  # deletion
                       #Modification('ins %s' % w2[j], matrix[i][j - 1].score + 1, (i, j - 1)),  # insertion
                       Modification(Operation.Del(w1[i]), matrix[i - 1][j].score + 1, (i - 1, j)),  # deletion
                       Modification(Operation.Ins(w2[j]), matrix[i][j - 1].score + 1, (i, j - 1)),  # insertion
                       Modification(substition_op, matrix[i - 1][j - 1].score + substitution_cost, (i - 1, j - 1))  # substitution
                       ]
            min_score = min([m.score for m in options])
            options = [m for m in options if m.score == min_score]
            matrix[i][j] = MatrixCell(options)
    return matrix

@dataclasses.dataclass
class Transition:
    d_in : str
    d_out : str
    before : 'Transition' = None
    after : 'Transition' = None
    @staticmethod
    def _to_output(s : str):
        return s if s else EMPTY
    def __hash__(self):
        return hash((self.d_in, self.d_out))
    def __str__(self):
        return '%s->%s' % (Transition._to_output(self.d_in), Transition._to_output(self.d_out))
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        return self.d_in == other.d_in and self.d_out == other.d_out
    def __bool__(self):
        return self.d_in != self.d_out


ChangeSequence = List[Transition]
def _change_sequence_score(c_seq : ChangeSequence) -> int:
    c_seq = [c for c in c_seq if c]
    return len(set(c_seq))


def find_change_sequences(matrix : ModMatrix, pos : Position = None) -> List[ChangeSequence]:
    if pos is None:
        pos = (matrix.rows-1, matrix.cols-1)
    if pos == (0, 0):
        return [[Transition(BOS, BOS)]] # beginning of string
    mod_paths : List[ChangeSequence] = []
    for mod in matrix.at(pos).modifications:
        new_paths = find_change_sequences(matrix, mod.from_pos)
        for path in new_paths:
            # path.append((pos[0], mod))
            path.append(Transition(mod.op.d_in, mod.op.d_out))
        mod_paths.extend(new_paths)
    return mod_paths

class WordTransformation:
    def __init__(self, initial : str, final : str):
        self.initial = initial
        self.final = final
        self.min_changes = simple_string_distance(self.initial, self.final)
        self.change_sequences = None

    def compute_change_sequences(self):
        matrix = distance(self.initial, self.final)
        self.change_sequences = find_change_sequences(matrix)
        for change_seq in self.change_sequences: # assign befores and afters
            for i, change in enumerate(change_seq):
                if i != 0:
                    change.before = change_seq[i-1]
                if i != len(change_seq)-1:
                    change.after = change_seq[i+1]
        # self.min_changes = min([_change_sequence_score(cs) for cs in self.change_sequences])
    def __str__(self):
        return '%s->%s' % (str(self.initial), str(self.final))
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        return (isinstance(other, WordTransformation)
                and self.initial == other.initial and self.final == other.final)
    def __hash__(self):
        return hash(str(self))
