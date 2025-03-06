from word import Syllable

import re

vowels = ('a', 'e', 'i', 'o', 'u', 'ă', 'î')

glide_dict = {
    'e':'e̯' ,
    'i':'i̯',
    'o':'o̯',
    'u':'u̯',
}

vocalic = list(vowels) + list(glide_dict.values())

N_phthongs =\
    {'ai': ['ai̯'], 'au': ['au̯'], 'ei': ['ei̯'], 'eu': ['eu̯'], 'ii': ['ii̯'], 'iu': ['iu̯', 'i̯u'], 'oi': ['oi̯'],
     'ou': ['ou̯'], 'ui': ['ui̯'], 'ăi': ['ăi̯'], 'ău': ['ău̯'], 'îi': ['îi̯'], 'îu': ['îu̯'], 'ea': ['e̯a'],
     'eo': ['e̯o'], 'ia': ['i̯a'], 'ie': ['i̯e'], 'io': ['i̯o'], 'oa': ['o̯a'], 'ua': ['u̯a'], 'uă': ['u̯ă'],
     'eai': ['e̯ai̯'], 'eau': ['e̯au̯'], 'iai': ['i̯ai̯'], 'iau': ['i̯au̯'], 'iei': ['i̯ei̯'], 'ieu': ['i̯eu̯'],
     'iou': ['i̯ou̯'], 'uai': ['u̯ai̯'], 'uau': ['u̯au̯'], 'uăi': ['u̯ăi̯'], 'oai': ['o̯ai̯'], 'eoa': ['e̯o̯a'],
     'ioa': ['i̯o̯a'], 'ioai': ['i̯o̯ai̯'], 'ioi': ['i̯oi̯']}

def orthosyll_to_phon_syllable(syl : str, center_chars : set[str],
                               is_final : bool, is_stressed : bool, is_unique : bool) -> str:
    if 'â' in syl:
        syl = syl.replace('â', 'î')
    if 'c' in syl or 'g' in syl:
        syl = re.sub(r'c([ei])', r'č\1', syl)
        syl = re.sub(r'g([ei])', r'ǧ\1', syl)
        syl = re.sub(r'ch?', 'k', syl)
        syl = syl.replace('gh', 'g')
    m = re.search(rf'[{"".join(center_chars)}]+', syl)
    if not m:
        raise Exception(f"Syllable {syl} has no center.")
    center = syl[m.start():m.end()]
    is_open = m.end() == len(syl)
    if len(center)!=1: # do N_phthongs
        if center not in N_phthongs:
            raise Exception(f'Center {center} not found in diphthong dict!')
        phon = N_phthongs[center]
        if len(phon) == 1:
            phon = phon[0]
        elif center == 'iu':
            if is_final and is_open and (is_stressed or is_unique): # rachiu, fiu, pustiu
                phon = 'iu̯'
            else:
                phon = 'i̯u' # iubit, uliu, consiliu, măciucă
        else:
            raise Exception(f"Don't know what to do with center {center}")
        syl = syl.replace(center, phon, 1)
    if not is_open and is_final and syl[-1] == 'i': # final i, short
        syl = syl[:-1] + 'i̯'

    return syl

def orthosyll_to_phon_word(word : str, center_chars : set[str], syll_sep_tok = '-', syll_stress_tok = '"') -> str:
    sylls = word.split(syll_sep_tok)
    syl_list = []
    for i, syl_src in enumerate(sylls):
        is_stressed = syll_stress_tok in syl_src
        is_final = i == len(sylls)-1
        is_unique = len(sylls)==1
        syl_list.append(orthosyll_to_phon_syllable(syl_src, center_chars, is_final, is_stressed, is_unique))
    return syll_sep_tok.join(syl_list)


if __name__ == "__main__":
    import pandas as pd

    data_df = pd.read_excel('./data/DexDiminutivesSyllabic.xlsx')
    dim_pairs = data_df.to_dict(orient='records')

    for d in dim_pairs:
        dim = d['diminutiv silabe']
        src = d['sursa silabe']
        for word in (src, dim):
            phon = orthosyll_to_phon_word(word, vowels)
            print(word, phon)

