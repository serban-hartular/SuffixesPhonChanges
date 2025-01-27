import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
import utils

from find_derivative_root import guess_source_by_edit_dist, vec_distance

import math

if __name__ == "__main__":
    print('Loading nouns')
    nouns : list[str] = utils.p_load('./nouns_doom1.p')
    print('Loading vectors')
    noun_vecs : dict[str, np.ndarray] = utils.p_load('./word_vectors/nouns_w2v.corola-big-clean.p')

    model_list : list[dict] = utils.p_load('./classifiers/is_derivative_models.p')
    model_list.sort(key=lambda d : -d['score'])

    suffix_list = ['uț', 'uleț', 'ior', 'ioară', 'ișor', 'ișoară', 'ușor', 'ușoară', 'ic', 'icel', 'ică', 'icică', 'ulică', 'uc', 'iță', 'uliță', 'ache', 'ușcă', 'ișcă', 'uș', 'ușă', 'uică', 'et', 'ete', 'oc']
    suffix_list.sort()
    suffix_list.sort(key=lambda s : -len(s))

    words_done = []

    for suffix in suffix_list:
        candidates = [n for n in nouns if n.endswith(suffix) and len(n) > len(suffix)]
        for word in candidates:
            if word in words_done:
                continue
            guesses = guess_source_by_edit_dist(word, suffix, nouns)
            source, edit_score = guesses[0] if guesses else (0, len(word))
            word_len = len(word)
            ln_word_len = math.log(word_len)
            word_vec = noun_vecs.get(word)
            source_vec = noun_vecs.get(source)
            vec_dist = vec_distance(word_vec, source_vec) if word_vec is not None and source_vec is not None else None
            data_dict = {'edit_score':edit_score, 'word_len':word_len, 'ln_word_len':ln_word_len,
                         'vec_dist':vec_dist}
            model_used = ''
            is_derivative = 'n/a'
            probability = -1
            for model_dict in model_list:
                if all([data_dict[arg] is not None for arg in model_dict['args']]):
                    model = model_dict['model']
                    data = [data_dict[arg] for arg in model_dict['args']]
                    is_derivative = model.predict([data])[0]
                    if is_derivative:
                        words_done.append(word)
                    probability = model.predict_proba([data])[0][1]
                    model_used = ', '.join(model_dict['args'])
                    break

            print('\t'.join([word, suffix, source, model_used, str(is_derivative), f'{probability:.3f}']))


