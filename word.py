import dataclasses

from syllable import Syllable, StressTokenPosition, STRESS_TOK, Alphabet
import itertools

SYLL_TOK = "-"

@dataclasses.dataclass
class Word:
    syllables : list[Syllable]
    phonemes : list[str] = dataclasses.field(default_factory=list)
    ortho : list[str] = dataclasses.field(default_factory=list)
    meta : dict[str, str|int|bool] = dataclasses.field(default_factory=dict)

    def assign_stress(self, syllable_index : int):
        if syllable_index < 0:
            syllable_index += len(self.syllables)
        if syllable_index >= len(self.syllables):
            raise Exception('Trying to assign stress to nonexistent syllable %d in %s!' %
                            (syllable_index, str(self)))
        for i, syl in enumerate(self.syllables):
            syl.stressed = (i == syllable_index)


    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d['syllables'] = [syl.to_dict() for syl in self.syllables]
        return d
    @staticmethod
    def from_dict(d : dict) -> 'Word':
        d['syllables'] = [Syllable.from_dict(syl) for syl in d['syllables']]
        return Word(**d)
    def __post_init__(self):
        if not self.syllables:
            raise Exception('Empty word!')
        if not self.phonemes:
            self.phonemes = list(itertools.chain.from_iterable([s.phonemes for s in self.syllables]))
        if not self.ortho:
            self.ortho = list(itertools.chain.from_iterable([s.ortho for s in self.syllables]))
        stress_count = 0
        for i, syll in enumerate(self.syllables):
            if i == 0:
                syll.initial = True
            elif syll.initial:
                print('Warning, non-initial syllable marked as initial')
                syll.initial = False
            if i == len(self.syllables)-1:
                syll.final = True
            elif syll.final:
                print('Warning, non-final syllable marked as final')
                syll.final = False
            stress_count += int(syll.stressed)
        if len(self.syllables) > 1 and stress_count != 1:
            raise Exception('Error, word %s has %d stressed syllables!' % (str(self), stress_count))

    def to_tokens(self, syllable_separators : bool = True,
                  stress_token_position : StressTokenPosition = StressTokenPosition.BEFORE_SYLLABLE) -> list[str]:
        syllables = [syl.to_tokens(stress_token_position) + ([SYLL_TOK] if syllable_separators else [])
                     for syl in self.syllables]
        tokens = list(itertools.chain.from_iterable(syllables))
        if syllable_separators:
            tokens = tokens[:-1]
        return tokens

    @staticmethod
    def from_tokens(abc : Alphabet, tok_list : list[str]):
        syllable_chunks = [list(group) for flag, group in
                     itertools.groupby(tok_list, lambda s : s == SYLL_TOK) if not flag]
        syllable_list = []
        for i, syllable_toks in enumerate(syllable_chunks):
            stress_flag = False
            if syllable_toks[0] == STRESS_TOK:
                stress_flag = True
                syllable_toks = syllable_toks[1:]
            syllable = Syllable.from_phonemes(abc, syllable_toks, stressed=stress_flag,
                                initial=(i == 0), final=(i==len(syllable_chunks)-1))
            syllable_list.append(syllable)
        return Word(syllable_list)

    def to_ortho(self, syllable_separators : bool = True, with_stress : bool = True):
        sep = SYLL_TOK if syllable_separators else ''
        return sep.join([syl.to_ortho(with_stress) for syl in self.syllables])

    def __str__(self):
        return self.to_ortho()

    def __repr__(self):
        return str(self)
