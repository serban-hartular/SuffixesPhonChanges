import dataclasses
import re
from collections import defaultdict


def string_to_list(s : str, multi_char_tokens : set[str]) -> list[str]:
    multi_char_dict = defaultdict(list)
    for tok in multi_char_tokens:
        multi_char_dict[len(tok)].append(tok)
    lens = list(set(multi_char_dict.keys()))
    lens.sort(reverse=True)
    tok_list = []
    while s:
        is_multi = False
        for tok_len in lens:
            if s[:tok_len] in multi_char_dict[tok_len]:
                is_multi = True
                break
        if not is_multi:
            tok_len = 1
        tok_list.append(s[:tok_len])
        s = s[tok_len:]
    return tok_list

@dataclasses.dataclass
class Syllable:
    onset : str
    center : str
    coda : str
    stressed : bool = False

    def is_open(self) -> bool:
        return not self.coda
    def no_onset(self) -> bool:
        return not self.onset

    def to_string(self) -> str:
        return self.onset + self.center + self.coda

    def __getitem__(self, item):
        return self.to_string()[item]

    def __contains__(self, item):
        return item in self.to_string()

    def __copy__(self):
        return Syllable(**dataclasses.asdict(self))

    @staticmethod
    def from_string(src : str, center_chars : set[str],
                    **kwargs) -> 'Syllable':
        m = re.search(rf'[{"".join(center_chars)}]+', src)
        if not m:
            raise Exception(f"Syllable {src} has no center.")
        onset = src[:m.start()]
        center = src[m.start():m.end()]
        coda = src[m.end():]
        d = {'onset':onset, 'center':center, 'coda':coda}
        d.update({k:bool(kwargs.get(k)) for k in ('stressed',)})
        return Syllable(**d)

@dataclasses.dataclass
class Sound:
    symbol : str
    word_index : int
    syllable_index : int
    syllable_part : str
    first_in_syllable : bool
    last_in_syllable : bool
    last_in_word : bool
    stressed_syllable : bool
    open_syllable : bool
    no_onset_syllable : bool
    final_syllable : bool
    is_center : bool

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return str(self)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

class Word(list[Sound]):
    def __init__(self, l : list[Sound]):
        super().__init__(l)
        if not l:
            raise Exception('Empty word!')
        l[-1].last_in_word = True

    def __str__(self):
        return ''.join([str(ph) for ph in self])

    def __repr__(self):
        return repr(str(self))

    def symbol_list(self) -> list[str]:
        return [ph.symbol for ph in self]
    @staticmethod
    def from_syllables(sylls : list[Syllable], mult_char_toks : set[str] = None) -> 'Word':
        sound_list = []
        phon_i = 0
        for s_i, syl in enumerate(sylls):
            syl_len = len(syl.to_string())
            index_in_syllable = 0
            for part_name, part in zip(['onset', 'center', 'coda'], [syl.onset, syl.center, syl.coda]):
                if mult_char_toks:
                    part = string_to_list(part, mult_char_toks)
                for ph in part:
                    sound = Sound(symbol=ph, word_index=phon_i, syllable_index=s_i,
                                  syllable_part=part_name,
                                  first_in_syllable=index_in_syllable==0,
                                  last_in_syllable=index_in_syllable==syl_len-1,
                                  last_in_word=False, # do this at the end
                                  stressed_syllable=syl.stressed,
                                  open_syllable=syl.is_open(),
                                  no_onset_syllable=syl.no_onset(),
                                  final_syllable=s_i==len(sylls)-1,
                                  is_center= part_name=='center' and len(part)==1)
                    sound_list.append(sound)
                    phon_i += 1
                    index_in_syllable += 1
        return Word(sound_list)

    @staticmethod
    def from_string(src : str, center_chars : set[str], mult_char_toks : set[str] = None,
                    **kwargs) -> 'Word':
        syl_split_token = kwargs.get('syl_split_token') if kwargs.get('syl_split_token') else '-'
        stress_token = kwargs.get('stress_token') if kwargs.get('stress_token') else '"'

        syl_strings = src.split(syl_split_token)
        syl_list = []
        for syl_str in syl_strings:
            is_stressed = stress_token in syl_str
            syl_str = syl_str.replace(stress_token, '')
            syl = Syllable.from_string(syl_str, center_chars)
            syl.stressed = is_stressed
            syl_list.append(syl)
        return Word.from_syllables(syl_list, mult_char_toks)
