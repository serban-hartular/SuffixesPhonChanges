import copy
import dataclasses
import json
import re
from typing import List

import pandas as pd
# import matplotlib
# import matplotlib.pyplot as plt
# from sklearn.tree import DecisionTreeClassifier

import utils
from decision_tree import FeatureDecisionTreeClassifier


@dataclasses.dataclass
class Syllable:
    text : str
    phon : str = ''
    stressed : bool = False
    center : str = ''
    final : bool = False
    initial : bool = False
    open : bool = False
    null_onset : bool = False
    def __post_init__(self):
        self.stressed = '"' in self.text
        self.phon = self.text.replace('"', '')
        self.center = re.findall(r'[aeiouăîâ]+', self.phon)[0]
        self.open = self.phon.endswith(self.center)
        self.null_onset = self.phon.startswith(self.center)
    @staticmethod
    def to_syllables(word : str) -> list['Syllable']:
        word = word.split('-')
        sylls = [Syllable(s) for s in word]
        if len(sylls) == 1:
            sylls[0].stressed = True
        sylls[-1].final = True
        sylls[0].initial = True
        return sylls

    def __str__(self):
        return self.text
    def __repr__(self):
        return repr(str(self))

class Word(List[Syllable]):
    def __init__(self, l : list[Syllable]):
        super().__init__(l)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return Word(super().__getitem__(item))
        else:
            return super().__getitem__(item)
    def __str__(self):
        return '-'.join([str(s) for s in self])
    def __repr__(self):
        return repr(str(self))

    @staticmethod
    def from_string(word : str) -> 'Word':
        return Word(Syllable.to_syllables(word))

    def get_stressed(self) -> Syllable:
        if len(self) == 1:
            return self[0]
        stressed = [s for s in self if s.stressed]
        if len(stressed) != 1:
            raise Exception('None or too many stressed in sequence ' + str(self))
        return stressed[0]


def get_root_last_syll(word : Word, ending_changes : dict[str, str] = None) -> str:
    if ending_changes is None:
        ending_changes = {'e': '', 'ie': 'i', 'iu': 'i', 'ă': '', 'ău': 'ă'}
    final = word[-1]
    if not final.open or final.center not in ending_changes:
        return str(final)
    final = final.text.replace(final.center, ending_changes[final.center])
    return final

if __name__ == "__main__":
    data_df = pd.read_excel('./data/DexDiminutivesSyllabic.xlsx')
    dim_pairs = data_df.to_dict(orient='records')
    center_changes = []
    for d in dim_pairs:
        dim = d['diminutiv silabe']
        src = d['sursa silabe']
        suffix = d['base suffix']
        dim_sylls = Word.from_string(dim) #Syllable.to_syllables(dim)
        src_sylls = Word.from_string(src) #Syllable.to_syllables(src)
        src_final = get_root_last_syll(src_sylls)
        src_final = re.sub(r'[-"]', '', src_final + suffix)
        dim_final = str(dim_sylls[len(src_sylls) - 1:])
        dim_final = re.sub(r'[-"]', '', dim_final)
        print(dim, src, f'{src_final} > {dim_final}')

        # a_is_stressed = src_sylls.get_stressed().center == 'a'
        # for i, (src_syl, dim_syl) in enumerate(zip(src_sylls, dim_sylls)):
    #         center_chg = {'cSRC':src_syl.center, 'cDIM':dim_syl.center,
    #                       'change':src_syl.center != dim_syl.center,
    #                       'final': src_syl.final, 'initial': src_syl.initial,
    #                       'stressed':src_syl.stressed,
    #                       'open':src_syl.open, 'null-onset':src_syl.null_onset,
    #                       'word_final': src_syl.final and src_syl.open,
    #                       'word_initial': src_syl.initial and src_syl.null_onset,
    #                       'a_is_stressed' : a_is_stressed,
    #                       'SRC':src, 'DIM':dim, 'syl_nr' : i, 'suffix':suffix}
    #         # center_chg = {k:int(v) if isinstance(v, bool) else v for k,v in center_chg.items()}
    #         center_changes.append(center_chg)
    # center_chg_df = pd.DataFrame(center_changes)
    # center_chg_df.to_excel('./data/center_chg_df.xlsx')
