
import pandas as pd
import conllu_path as cp
import requests

import utils

from string_distance import simple_string_distance as str_dist

substitution_costs = {
    ('t', 'ț') : 0.1,
    ('a', 'ă') : 0.1,
}

if __name__ == "__main__":
    nouns = utils.p_load('./nouns_doom1.p')
    suffix = 'el'
    _el = [n for n in nouns if n.endswith(suffix)]
    base_nouns = {}
    for diminutive in _el:
        radical = diminutive[:-len(suffix)]
        if len(radical) < 2:
            base_nouns[diminutive] = []
            continue
        bases_sorted = [(n, str_dist(n, radical, substitution_costs)) for n in nouns if n != diminutive]
        bases_sorted.sort(key=lambda t : t[1]) # sort by distance
        score = bases_sorted[0][1]
        bases_sorted = [b for b in bases_sorted if b[1] == score]
        base_nouns[diminutive] = bases_sorted
        print(diminutive, '\t', radical, '\t', bases_sorted)


