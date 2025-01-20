
from word import SymbolString, Syllable, Alphabet, ro_abc
import pandas as pd

def match_phon_to_ortho(phon : str, ortho : str, abc : Alphabet) -> bool:
    phon = SymbolString(phon, ' ')
    ortho = SymbolString(ortho)
    return phon.to_ortho(abc) == ortho


if __name__ == "__main__":
    df = pd.read_csv('./data/subst_phon_syll.csv', sep='\t', encoding='utf-8')
    forms = list(df['Forma'])
    phon = list(df['Phonetic'])
    forms = [f.replace('â', 'î') for f in forms]
    for o, ph in zip(forms, phon):
        if not match_phon_to_ortho(ph, o, ro_abc):
            print(ph, o, SymbolString(ph, ' ').to_ortho(ro_abc))

