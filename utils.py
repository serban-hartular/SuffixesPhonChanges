
import json
import pandas as pd


import pickle
def p_load(filename: str):
    with open(filename, "rb") as handle:
        o = pickle.load(handle)
    return o

def p_save(obj, filename : str):
    with open(filename, "wb") as handle:
        pickle.dump(obj, handle)


def import_jsonl(filename : str) -> list[dict]:
    with open(filename, 'r', encoding='utf-8') as handle:
        lines = handle.readlines()
    data = []
    for i, line in enumerate(lines):
        try:
            data.append(json.loads(line))
        except Exception as e:
            raise Exception(f'Error parsing line {i}, "{line}":{str(e)}')
    return data

def csv_to_word_pairs(filename : str, initial_label : str, final_label) -> list[tuple[str, str]]:
    data = pd.read_csv(filename, sep='\t', encoding='utf-8')
    data = data.fillna('')
    data = data.to_dict(orient='records')
    return [(d[initial_label], d[final_label]) for d in data]

nodiacritics_dict = {
    'ă':'a', 'î':'i', 'â':'a',
    'ș':'s', 'ț':'t',
}
def to_no_diacritics(s : str) -> str:
    for k,v in nodiacritics_dict.items():
        s = s.replace(k, v)
    return s