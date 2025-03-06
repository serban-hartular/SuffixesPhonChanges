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

from word_transformation import WordTransformation, ChangeSequence, Transition


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
        self.open = self.phon.endswith(self.center) and self.text.find(self.center) == self.text.rfind(self.center)
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


def get_root_last_syll(word : Word, ending_changes : dict[str, str] = None) -> (str, str):
    if ending_changes is None:
        ending_changes = {'e': '', 'ie': 'i', 'iu': 'i', 'ă': ''}
    final = word[-1]
    if not final.open or final.center not in ending_changes:
        return str(final), ''
    dropped = final.center[-1]
    final = final.text.replace(final.center, ending_changes[final.center])
    return final, dropped

def group_changes(chg_seq : ChangeSequence) -> (ChangeSequence, ChangeSequence, ChangeSequence):
    new_chg_seq = []
    skip_next = False
    input_index = -1
    for chg in chg_seq:
        if skip_next:
            skip_next = False
            continue
        if chg.d_in != 'c' and chg.d_out == 'c' and chg.after and (chg.after.d_in, chg.after.d_out) == ('', 'i'): # inserting 'ci'
            new_chg_seq.append(Transition(chg.d_in, chg.d_out + 'i'))
            skip_next = True
            continue
        if chg.d_in != '': # is not insertion
            new_chg_seq.append(Transition(chg.d_in, chg.d_out))
        else: # is insertion1
            if not new_chg_seq or new_chg_seq[-1].d_in != '': # append insertion
                new_chg_seq.append(Transition(chg.d_in, chg.d_out))
            else: # add to insertion
                new_chg_seq[-1].d_out += chg.d_out
        skip_next = False

    for i, chg in enumerate(new_chg_seq):
        if i > 0:
            chg.before = new_chg_seq[i-1]
        if i < len(new_chg_seq)-1:
            chg.after = new_chg_seq[i+1]

    return new_chg_seq

def extract_edits(chg_seq : ChangeSequence, last_input_index : int = -1) -> (ChangeSequence, ChangeSequence, ChangeSequence):
    edit_lists = [[], [], []]
    input_index = -1
    for chg in chg_seq:
        if chg.d_in != '' or input_index >= last_input_index: # not insertion, or past end
            input_index += 1
        destination_index = 0 if input_index < last_input_index else 1 if input_index == last_input_index else 2
        destination = edit_lists[destination_index]
        if chg.d_in == chg.d_out: # no change
            continue
        destination.append(Transition(chg.d_in, chg.d_out,
                                chg.before.d_in if chg.before is not None else '',
                                chg.after.d_in if chg.after is not None else ''))
    return edit_lists

