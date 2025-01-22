import dataclasses
import enum
from typing import List, Callable

SymbolString = list[str]


@dataclasses.dataclass
class Alphabet:
    vowels : list[str]
    semi_vowels : list[str]
    non_vowels : list[str]
    _phon_2_ortho : dict[str, str] = dataclasses.field(default_factory=dict)
    post_phon2ortho : Callable[[list[str]], list[str]] = None
    symbols : list[str] = None
    def __post_init__(self):
        self.symbols = self.vowels + self.semi_vowels + self.non_vowels
        for sym in self.symbols:
            if sym not in self._phon_2_ortho:
                self._phon_2_ortho[sym] = sym
    def phon_2_ortho(self, phon : SymbolString) -> SymbolString:
        ortho = [self._phon_2_ortho.get(ph) for ph in phon]
        if None in ortho:
            raise Exception('Symbol not found in string %s' % str(phon))
        if self.post_phon2ortho is not None:
            ortho = self.post_phon2ortho(ortho)
        return ortho


def ro_k_to_kh(ss :list[str]) -> list[str]:
    out = list()
    kg_dict = {'k':'c', 'G':'g'}
    for i, s in enumerate(ss):
        if s in kg_dict:
            out.append(kg_dict[s])
            if i < len(ss)-1 and ss[i+1] in ('e', 'i'):
                out.append('h')
        else:
            out.append(s)
    return out

ro_abc = Alphabet(
    vowels=['a', 'e', 'i', 'o', 'u', '@', 'a@'],
    semi_vowels=['j', 'w', 'e@', 'o@'],
    non_vowels=list('bdfghklmnprstvz') + ['ch', 'sh', 'ts', 'dz', 'zh'],
    _phon_2_ortho={'@': 'ă', 'a@': 'î', 'j': 'i', 'w': 'u', 'e@' : 'e', 'o@' : 'o',
                  'sh':'ș', 'ts':'ț', 'zh':'j',
                  'ch':'c', 'k' : 'k', 'dz':'g', 'g' : 'G'},
    post_phon2ortho = ro_k_to_kh,
)

# class SymbolString(List[str]):
#     def __init__(self, src : str|List[str], sep : str = ''):
#         super().__init__(src.split(sep) if isinstance(src, str) and sep else list(src))
#     def slice(self, slice : Slice) -> 'list[str]':
#         return list[str](self[slice[0]:slice[1]+1])
#     def to_string(self, sep : str = ' '):
#         return sep.join(self)
#     def to_ortho(self, abc : Alphabet) -> 'list[str]':
#         ortho = [abc.phon_2_ortho[sym] for sym in self]
#         if abc.post_phon2ortho is not None:
#             ortho = abc.post_phon2ortho(ortho)
#         return list[str](ortho)
#     def __str__(self):
#         return self.to_string()
#     def __repr__(self):
#         return '/'+self.to_string()+'/'

STRESS_TOK = "'"

class StressTokenPosition(enum.Enum):
    NONE = -1
    BEFORE_SYLLABLE = 0
    BEFORE_CENTER = 1
    AFTER_CENTER = 2
    AFTER_SYLLABLE = 3
    NUM_POSITIONS_ = 4

@dataclasses.dataclass
class Syllable:
    # abc : Alphabet
    phonemes : SymbolString
    stressed : bool = False
    initial: bool = False
    final : bool = False
    ortho : SymbolString = dataclasses.field(default_factory=list)
    _onset : tuple[int, int] = (-1, -1)
    _center : tuple[int, int] = (-1, -1)
    _vowel : int = -1
    _coda : tuple[int, int] = (-1, -1)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(d : dict) -> 'Syllable':
        return Syllable(**d)

    @staticmethod
    def from_phonemes(abc : Alphabet, phonemes : list[str], **kwargs) -> 'Syllable':
        syl = Syllable(SymbolString(phonemes))
        syl.stressed = bool(kwargs.get('stressed'))
        syl.initial = bool(kwargs.get('initial'))
        syl.final = bool(kwargs.get('final'))
        # ortho
        if not syl.ortho:
            syl.ortho = abc.phon_2_ortho(syl.phonemes) #syl.phonemes.to_ortho(abc)
        state = 'onset'
        for i, sym in enumerate(syl.phonemes):
            if sym not in abc.symbols:
                print('Error! Symbol %s in syllable %s not in alphabet!' % (sym, str(syl)))
                return None
            if state == 'onset':
                if sym in abc.non_vowels:
                    continue
                else:
                    # syl._onset = (0, i - 1)
                    syl._onset = (0, i)
                    state = 'center'
            if state == 'center':
                if sym in abc.semi_vowels:
                    continue
                elif sym in abc.vowels:
                    if syl._vowel != -1:
                        print('Error! Syllable %s has two vowels' % str(syl))
                        return None
                    syl._vowel = i
                    continue
                else:
                    # syl._center = (syl._onset[1] + 1, i - 1)
                    syl._center = (syl._onset[1], i)
                    if syl._vowel == -1:
                        print('Error! Syllable %s has no vowel in its center!' % str(syl))
                        return None
                    state = 'coda'
            if state == 'coda':
                if sym in abc.vowels:
                    print('Error! Syllable %s has two vowels!' % str(syl))
                    return None
                continue
        if syl._center == (-1, -1):
            syl._center = (syl._onset[1], len(syl.phonemes))
        # syl._coda = (syl._center[1] + 1, len(syl.phonemes) - 1)
        syl._coda = (syl._center[1], len(syl.phonemes))
        return syl
    def __str__(self):
        return str(' '.join(self.phonemes))
    def __repr__(self):
        return str(self)
    def onset(self) -> SymbolString:
        return self.phonemes[slice(*self._onset)]
    def center(self) -> SymbolString:
        return self.phonemes[slice(*self._center)]
    def coda(self) -> SymbolString:
        return self.phonemes[slice(*self._coda)]
    def vowel(self) -> str:
        return self.phonemes[self._vowel]

    def to_tokens(self, stress_token_position = StressTokenPosition.NONE) -> list[str]:
        if not self.stressed:
            return list(self.phonemes)
        stress_tokens = [[STRESS_TOK] if i == stress_token_position.value else [] for i in range(StressTokenPosition.NUM_POSITIONS_.value)]
        tokens = stress_tokens[0] + self.onset() + stress_tokens[1] + self.center() +\
            stress_tokens[2] + self.coda() + stress_tokens[3]
        return tokens

    def to_ortho(self, with_stress : bool = True, sep : str = '') -> str:
        return (STRESS_TOK if self.stressed and with_stress else '') + sep.join(self.ortho)
