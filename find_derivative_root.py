import itertools
import math

import numpy as np
import pandas as pd
from numpy.linalg import norm

import utils

from string_distance import simple_string_distance as w_dist
import sklearn


substitution_costs = {
    ('t', 'ț') : 0.1,
    ('s', 'ș'): 0.1,
    ('a', 'ă') : 0.1,
    ('â', 'i') : 0.2,
    ('ă', 'e') : 0.2,
}

substitution_costs = substitution_costs | {(b,a):v for (a,b), v in substitution_costs.items()}

def remove_final_vowels(s : str, count : int = -1) -> str:
    while s and s[-1] in 'aeiouăîâ' and count != 0:
        s = s[:-1]
        count -= 1
    return s

def vec_distance(a : np.ndarray, b : np.ndarray) -> float:
    return float(norm(a - b))

def cos_distance(a : np.ndarray, b : np.ndarray) -> float:
    return 1 - float(np.dot(a,b)/(norm(a)*norm(b)))

def guess_source_by_edit_dist(deriative : str, suffix : str, candidates : list[str],
                 dist_cutoff : float = 1) -> list[tuple[str, float]]:
    if not deriative.endswith(suffix):
        raise Exception('Derivative does not end in suffix')
    der_root = deriative[:-(len(suffix))]
    der_root = remove_final_vowels(der_root, 1)
    candidates = [c for c in candidates if c[0] == deriative[0]] # ?!?
    candidates = [(c, w_dist(der_root, remove_final_vowels(c, 1), substitution_costs))
                   for c in candidates if c != deriative]
    if not candidates:
        return []
    scores = list(set([t[-1] for t in candidates]))
    scores.sort()
    scores = scores[:dist_cutoff]
    candidates = [t for t in candidates if t[-1] in scores]
    candidates.sort(key=lambda t : t[-1])
    return candidates

def guess_source_by_wordvec(derivative : str, candidates : list[str],
                            distance_metric : dict[tuple[str, str], float]) -> list[str]:
                            # , wordvecs : dict[str, np.ndarray]) -> list[str]:
    candidate_scores = [(c, distance_metric[(derivative, c)]) for c in candidates
                        if distance_metric.get((derivative, c)) is not None]
    candidate_scores.sort(key=lambda t: t[-1])
    return [t[0] for t in candidate_scores]

MAX_DIST = 10

if __name__ == "__main__":
    print('Loading nouns')
    nouns : list[str] = utils.p_load('./nouns_doom1.p')
    print('Loading pairs')
    df_master = pd.read_csv('./data/derived_nouns_master.csv', sep='\t', encoding='utf-8')
    df_master = df_master.fillna('')
    print('Loading vectors')
    noun_vecs : dict[str, np.ndarray] = utils.p_load('./word_vectors/nouns_w2v.corola-big.p')
    # wordpair_dist : dict[tuple[str, str], float] = utils.p_load('./word_vectors/noun_vec_distances.corola-big.p')
    # wordpair_cos: dict[tuple[str, str], float] = utils.p_load('./word_vectors/noun_cos_distances.corola-big.p')

    data_rows = []

    for row in df_master.to_dict(orient='records'):
        source, deriv_word = row['Sursa'].strip(), row['Cuvant'].strip()
        if source.startswith('a '): # verbs
            source = source[2:]
        is_good = 1.0 if source else 0.0
        # chop off suffix
        if deriv_word[-2:] in ('el', 'aș'):
            suffix = deriv_word[-2:]
        elif deriv_word[-3:] in ('șor'):
            suffix = deriv_word[-3:]
        else:
            raise Exception(f'Unknown suffix for {deriv_word}!')
        if suffix == deriv_word: # not the suffix itself
            continue
        if not source: # guess something
            guesses = guess_source_by_edit_dist(deriv_word, suffix, nouns)
            source, edit_score = guesses[0] if guesses else ('', len(deriv_word))
        else: # get the edit score of the correct option
            der_root = deriv_word[:-(len(suffix))]
            der_root = remove_final_vowels(der_root, 1)
            src_root = remove_final_vowels(source, 1)
            edit_score = w_dist(der_root, src_root, substitution_costs)
        data_dict = {'word':deriv_word, 'is_derivative':is_good, 'source':source,
                     'edit_score':float(edit_score),
                     'word_len':len(deriv_word), 'word_len_nosuffix':len(deriv_word)-len(suffix),
                     'ln_word_len':math.log(len(deriv_word)),
                     'ln_word_len_nosuffix':math.log(len(deriv_word)-len(suffix))}
        deriv_word_vec, source_vec = noun_vecs.get(deriv_word), noun_vecs.get(source)
        if deriv_word_vec is None or source_vec is None:
            vec_dist, cos_dist = None, None
        else:
            vec_dist, cos_dist = vec_distance(deriv_word_vec, source_vec), cos_distance(deriv_word_vec, source_vec)
        data_dict.update({'vec_dist':vec_dist, 'cos_dist':cos_dist})
        print(deriv_word, is_good, source)
        data_rows.append(data_dict)

    df = pd.DataFrame(data_rows)





