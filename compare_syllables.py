import dataclasses

import pandas as pd

@dataclasses.dataclass
class SylCenter:
    center : str
    stress : str = ''
    def veq(self, other : 'SylCenter') -> bool:
        return self.center == other.center
    def __str__(self):
        return self.stress + self.center
    def __repr__(self):
        return str(self)

def get_vowels(syl : str)-> SylCenter:
    stress = "'" if "'" in syl else ''
    vowels = 'aeiouăîâ'
    state = 'onset'
    center = ''
    for s in syl:
        if state == 'onset':
            if s not in vowels:
                continue
            else:
                state = 'vowels'
                center += s
        elif state == 'vowels':
            if s in vowels:
                center += s
            else:
                return SylCenter(center, stress)
    return SylCenter(center, stress)

if __name__ == "__main__":
    df_phon = pd.read_csv('./data/subst_phon_syll.csv', sep='\t', encoding='utf-8')
    word_dictionary = {row['Forma'] : row['Sylabe'] for row in df_phon.to_dict(orient='records')}
    df_dimins = pd.read_csv('./data/diminutives_el.csv', sep='\t', encoding='utf-8')
    dimin_dict = {row['Diminutiv']:
                      {'Src':row['Sursa'], 'SrcSyl' : word_dictionary.get(row['Sursa']), 'DimSyl':word_dictionary.get(row['Diminutiv'])}
        for row in df_dimins.to_dict(orient='records')}

    for dim, ddict in dimin_dict.items():
        if None in list(ddict.values()):
            print(dim, ddict)

    dimin_dict = {d:ddict for d,ddict in dimin_dict.items() if None not in list(ddict.values())}

    for dim, ddict in dimin_dict.items():
        ddict['SrcSyl'] = ddict['SrcSyl'].split('-')
        ddict['DimSyl'] = ddict['DimSyl'].split('-')

    for dim, ddict in dimin_dict.items():
        ddict['SrcCenters'] = [get_vowels(syl) for syl in ddict['SrcSyl']]
        ddict['DimCenters'] = [get_vowels(syl) for syl in ddict['DimSyl']]