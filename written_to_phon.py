import itertools

import utils
from syllable import SymbolString, Syllable, Alphabet, ro_abc
# import pandas as pd
import re
import json

from word import Word


def match_phon_to_ortho(phon : str, ortho : str, abc : Alphabet) -> bool:
    phon = SymbolString(phon, ' ')
    ortho = SymbolString(ortho)
    return phon.to_ortho(abc) == ortho

def syllables_to_phonsyllables(syllables : str, phon : str, abc : Alphabet) -> list[str]:
    phon = phon.split(' ')
    # check that all phons are in alphabet
    for ph in phon:
        if ph not in abc._phon_2_ortho:
            print('Error in word %s, phoneme %s not found!' % (syllables, ph))
            return None
    syllables.replace("''", "'")
    syllables = syllables.replace('â', 'î')
    syllables = re.sub(r'ch([ei])', r'k\1', syllables)
    syllables = re.sub(r'c([^ei]|$)', r'k\1', syllables)
    syllables = re.sub(r'gh([ei])', r'G\1', syllables)
    syllables = re.sub(r'g([^ei]|$)', r'G\1', syllables)
    ortho = syllables.replace('-', '').replace("'", '')
    # check if the ortho matches the phonetic sound for sound
    for o, ph in zip(ortho, phon):
        if abc._phon_2_ortho[ph] != o:
            print('Error in word %s, sound %s does not match letter %s.' % (syllables, ph, o))
            return None
    phonsyllables = []
    ph_index = 0
    for o in syllables:
        if o == abc._phon_2_ortho[phon[ph_index]]:
            phonsyllables.append(phon[ph_index])
            ph_index += 1
        else:
            phonsyllables.append(o)
    if ph_index != len(phon):
        print('Error in word %s, still have phonemes to use: %s' % (syllables, str(phon[ph_index:])))
    return phonsyllables

def syllable_sanity_check(syl : Syllable) -> bool:
    return syl.center() and syl.vowel() and syl.onset() + syl.center() + syl.coda() == syl.phonemes\
        and syl.vowel() in syl.center()

if __name__ == "__main__":
    word_list_json = utils.p_load('./word_list0.json.p')
    word_list = [Word.from_dict(d) for d in json.loads(word_list_json)]
    word_list_correct = []
    for word in word_list:
        syls = [Syllable.from_phonemes(ro_abc, syl.phonemes,
                                       stressed=syl.stressed,
                                       initial=syl.initial,
                                       final=syl.final) for syl in word.syllables]
        new_word = Word(syls)
        new_word.meta = dict(word.meta)
        if not all([syllable_sanity_check(syl) for syl in new_word.syllables]):
            print('Error word ', new_word)
        word_list_correct.append(new_word)

    # df = pd.read_csv('./data/subst_phon_syll.csv', sep='\t', encoding='utf-8')
    # df = df.fillna('')
    # word_dict = {}
    # for row in df.to_dict(orient='records'):
    #     form, syl, phon, is_deriv, pos = (row[k] for k in df.columns)
    #     ortho = syl.replace("-", "").replace("'", "")
    #     if ortho != form:
    #         print('%s does not match %s' % (form, syl))
    #     phoneme_list = syllables_to_phonsyllables(syl, phon, ro_abc)
    #     word_dict[(form, pos, is_deriv)] = [list(group) for flag, group in itertools.groupby(phoneme_list, lambda s : s=='-') if not flag]
    #
    # word_rep_dict = {}
    # for k, syl_list in word_dict.items():
    #     syllables = []
    #     for syl_str in syl_list:
    #         stress_flag = False
    #         if syl_str[0] == "'":
    #             stress_flag = True
    #             syl_str = syl_str[1:]
    #         syl = Syllable.from_phonemes(ro_abc, syl_str, stressed=stress_flag)
    #         syllables.append(syl)
    #     try:
    #         word = Word(syllables)
    #         word_rep_dict[k] = word
    #     except Exception as e:
    #         print(f'Error: f{str(k)}: f{str(e)}')
    # for k, word in word_rep_dict.items():
    #     word.meta = {'dict_form':k[0], 'upos':k[1], 'is_der':k[2]}
    #     if word.meta['is_der']:
    #         word.assign_stress(-1)
    #
    #
