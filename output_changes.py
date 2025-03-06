import re
from typing import Callable

import pandas as pd

import ro_phon
from word import Word
from word_transformation import WordTransformation, ChangeSequence, Transition, assign_indices

vowels = list(ro_phon.vowels)
semivowels = list(ro_phon.glide_dict.values())
vocalic = vowels + semivowels
def cost_fn(d_in: str, d_out: str) -> float:

    if d_in == '+' and d_out != '':  # plus can only be deleted
        return 10
    pairs = [('t', 'ț'), ('s', 'ș'), ('d', 'z'), ('g', 'j'), ('c', 'č'), ('g', 'ǧ'),
             ('a', 'ă')] + list(ro_phon.glide_dict.items())
    if (d_in == '-' and d_out not in ('', '-')) or (d_out == '-' and d_in not in ('', '-')):
        return 10
    if d_in and d_out and (d_in in vocalic) != (d_out in vocalic):
        return 1.5
    if (d_in, d_out) in pairs or (d_out, d_in) in pairs:
        return 0.9
    if d_in not in vocalic and d_out not in vocalic:  # we don't like changing consonants just like that
        return 1.1
    return 1


def group_edits_by(c_seq : ChangeSequence, criteria_fn : Callable[[Transition, Transition], bool], **kwargs) -> ChangeSequence:
    new_seq : ChangeSequence = []
    for chg in c_seq:
        if new_seq and criteria_fn(new_seq[-1], chg): # merge changes
            new_seq[-1].d_in += chg.d_in
            new_seq[-1].d_out += chg.d_out
        else:
            new_seq.append(chg)
    for i, chg in enumerate(new_seq):
        if i > 0:
            chg.before = new_seq[i-1]
        if i < len(new_seq)-1:
            chg.after = new_seq[i+1]
    return new_seq

def are_inserts(t1 : Transition, t2 : Transition) -> bool:
    return t1.d_in == '' and t2.d_in == ''

def vocalic_chg(t1 : Transition, t2 : Transition) -> bool:
    if t1.d_in == t1.d_out or t2.d_in == t2.d_out: # no change
        return False
    return {t1.d_in, t1.d_out, t2.d_in, t2.d_out}.issubset(set(vocalic + ['']))

def merge_ci(t1 : Transition, t2 : Transition):
    return t1.d_out == 'č' and t2.d_in == '' and t2.d_out in ('i', 'i̯')

def truncate_afix(word : Word, affix_list : list[str], sorted : bool = False) -> (Word, str):
    if not sorted:
        affix_list = list(affix_list)
        affix_list.sort(key=lambda s : -len(s)) # longest first
    for affix in affix_list:
        affix_len = len(affix)
        affix = ''.join(affix)
        word_term = ''.join([ph.symbol for ph in word[-affix_len:]])
        if word_term == affix:
            return Word(word[:-affix_len]), affix
    return word, ''

if __name__ == "__main__":
    data_df = pd.read_excel('./data/DexDiminutivesSyllabic.xlsx')
    dim_pairs = data_df.to_dict(orient='records')
    dim_changes = []
    for d in dim_pairs:
        dim = d['diminutiv silabe']
        src = d['sursa silabe']
        suffix = d['base suffix']
        suffix_len = len(suffix.replace('-',''))
        if not dim.endswith(suffix):
            print(f'Warning: {dim} does not end with {suffix}!')

        dim_sylls = ro_phon.orthosyll_to_phon_word(dim, vocalic)
        src_sylls = ro_phon.orthosyll_to_phon_word(src, vocalic)
        dim_word = Word.from_string(dim_sylls, vocalic, set(ro_phon.glide_dict.values()))
        src_word = Word.from_string(src_sylls, vocalic, set(ro_phon.glide_dict.values()))

        dim_trunc = Word(dim_word[:-suffix_len])
        affixes = ['e', 'ă', 'u', 'u̯', 'i u̯', 'i ̯e']
        affixes = [a.split(' ') for a in affixes]
        affixes.sort(key=lambda s : -len(s))
        src_trunc, dropped = truncate_afix(src_word, affixes, True)

        wt = WordTransformation(src_trunc.symbol_list(), dim_trunc.symbol_list(), cost_fn)
        changes = wt.change_sequences
        for c_seq in changes:
            assign_indices(c_seq)
        for i in range(len(changes)):
            for fn in (are_inserts, vocalic_chg, merge_ci):
                changes[i] = group_edits_by(changes[i], fn)
        changes.sort(key=lambda l : len(l))
        changes = changes[0] if changes else []
        changes = [chg for chg in changes if chg]
        # split by position
        radical_end_position = len(src_trunc)-1
        edit_dict = {'chg_before':[], 'chg_at':[], 'chg_after':[]}
        for chg in changes:
            key = 'chg_before' if chg.i_in-1 < radical_end_position else 'chg_at' if chg.i_in-1 == radical_end_position else 'chg_after'
            edit_dict[key].append(chg)
        chg_rec = {'src':src_word, 'dim':dim_word, 'src_trunc': src_trunc, 'dim_trunc':dim_trunc,
                   'dropped':dropped} | edit_dict
        print('\t'.join([str(i) for i in [src_word, dim_word, src_trunc, dim_trunc, dropped, edit_dict ] ]))
        dim_changes.append(chg_rec)

    chg_dict = {str(chg['dim']):chg for chg in dim_changes}
    # # generate change dataframe
    # edit_table = []
    # for chg in dim_changes:
    #     for i, pos in enumerate(('before', 'at', 'after')):
    #         for edit in chg['edits'][i]:
    #             edit_dict = {
    #                 'Position':pos,
    #                 'Edit': str(edit),
    #                 'Before': edit.before,
    #                 'After':edit.after,
    #                 'NumSylls':chg['num_sylls'], 'LastStressed':chg['last_stressed'],
    #                 'FinDropped':chg['dropped'],
    #                 'Suffix':chg['suffix'],
    #                 'Src':chg['src'], 'Dim':chg['dim']
    #
    #             }
    #             edit_table.append(edit_dict)
    # edit_df = pd.DataFrame(edit_table)
