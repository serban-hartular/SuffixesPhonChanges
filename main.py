from collections import defaultdict

import pandas as pd
import conllu_path as cp
import requests

import utils

from string_distance import simple_string_distance as str_dist

substitution_costs = {
    ('t', 'ț') : 0.1,
    ('a', 'ă') : 0.1,
}

def remove_final_vowels(s : str) -> str:
    while s and s[-1] in 'aeiouăîâ':
        s = s[:-1]
    return s

if __name__ == "__main__":
    df = pd.read_csv('./data/diminutives_el.csv', sep='\t', encoding='utf-8')
    df['Radical_0'] = df.apply(lambda row : remove_final_vowels(row['Sursa']).strip(), axis=1)
    df['Radical_D'] = df.apply(lambda row : row['Diminutiv'][:-len(row['Sufix'])], axis=1)
    radical_pairs = df[['Radical_0', 'Radical_D']].to_dict(orient='records')
    radical_pairs = [(d['Radical_0'], d['Radical_D']) for d in radical_pairs]
    final_diff = [t for t in radical_pairs if t[0][-1] != t[1][-1]]
    final_change = defaultdict(list)
    for t in final_diff:
        final_change[(t[0][-1], t[1][-1])].append(t)
    for k, v in final_change.items():
        print(k, '\t', v)
