import dataclasses
from typing import List, Callable


@dataclasses.dataclass
class Alphabet:
    vowels : list[str]
    semi_vowels : list[str]
    non_vowels : list[str]
    phon_2_ortho : dict[str, str] = dataclasses.field(default_factory=dict)
    post_phon2ortho : Callable[[list[str]], list[str]] = None
    symbols : list[str] = None
    def __post_init__(self):
        self.symbols = self.vowels + self.semi_vowels + self.non_vowels
        for sym in self.symbols:
            if sym not in self.phon_2_ortho:
                self.phon_2_ortho[sym] = sym

def ro_k_to_kh(ss :list[str]) -> list[str]:
    out = list()
    kg_dict = {'k':'c', 'gg':'g'}
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
    phon_2_ortho={'@':'ă', 'a@':'î', 'j':'i', 'w':'u', 'e@' : 'e', 'o@' : 'o',
                  'sh':'ș', 'ts':'ț', 'zh':'j',
                  'ch':'c', 'k' : 'k', 'dz':'g', 'g' : 'gg'},
    post_phon2ortho = ro_k_to_kh,
)

Slice = tuple[int, int]
class SymbolString(List[str]):
    def __init__(self, src : str|List[str], sep : str = ''):
        super().__init__(src.split(sep) if isinstance(src, str) and sep else list(src))
    def slice(self, slice : Slice) -> 'SymbolString':
        return SymbolString(self[slice[0]:slice[1]+1])
    def to_string(self, sep : str = ' '):
        return sep.join(self)
    def to_ortho(self, abc : Alphabet) -> 'SymbolString':
        ortho = [abc.phon_2_ortho[sym] for sym in self]
        if abc.post_phon2ortho is not None:
            ortho = abc.post_phon2ortho(ortho)
        return SymbolString(ortho)
    def __str__(self):
        return self.to_string()
    def __repr__(self):
        return '/'+self.to_string()+'/'

@dataclasses.dataclass
class Syllable:
    abc : Alphabet
    phonemes : SymbolString
    stressed : bool = False
    initial: bool = False
    final : bool = False
    ortho : SymbolString = None #dataclasses.field(default_factory=list)
    _onset : Slice = (0, 0)
    _center : Slice = (0, 0)
    _vowel : int = -1
    _coda : Slice = (0, 0)
    def __post_init__(self):
        if self.ortho is None:
            self.ortho = self.phonemes.to_ortho(self.abc)
        state = 'onset'
        for i, sym in enumerate(self.phonemes):
            if sym not in self.abc.symbols:
                print('Error! Symbol %s in syllable %s not in alphabet!' % (sym, str(self)))
                return
            if state == 'onset':
                if sym in self.abc.non_vowels:
                    continue
                else:
                    self._onset = (0, i - 1)
                    state = 'center'
            if state == 'center':
                if sym in self.abc.semi_vowels:
                    continue
                elif sym in self.abc.vowels:
                    if self._vowel != -1:
                        print('Error! Syllable %s has two vowels' % str(self))
                        return
                    self._vowel = i
                    continue
                else:
                    self._center = (self._onset[1] + 1, i - 1)
                    if self._vowel == -1:
                        print('Error! Syllable %s has no vowel in its center!' % str(self))
                        return
                    state = 'coda'
            if state == 'coda':
                if sym in self.abc.vowels:
                    print('Error! Syllable %s has two vowels!' % str(self))
                    return
                continue
        self._coda = (self._center[1] + 1, len(self.phonemes) - 1)
    def __str__(self):
        return str(self.phonemes)
    def __repr__(self):
        return str(self)
    def onset(self) -> SymbolString:
        return self.phonemes.slice(self._onset)
    def center(self) -> SymbolString:
        return self.phonemes.slice(self._center)
    def coda(self) -> SymbolString:
        return self.phonemes.slice(self._coda)
    def vowel(self) -> str:
        return self.phonemes[self._vowel]

