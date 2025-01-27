import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
import random
import utils
from gensim.models.keyedvectors import KeyedVectors

if __name__ == "__main__":
    # data_df = pd.read_csv('./data/is_derivative_data.csv', sep='\t', encoding='utf-8')

    data_combos_all = [['edit_score', 'word_len'], ['edit_score', 'word_len_nosuffix'], ['edit_score', 'ln_word_len'],
                       ['edit_score', 'ln_word_len_nosuffix'], ['edit_score', 'word_len', 'vec_dist'],
                       ['edit_score', 'word_len_nosuffix', 'vec_dist'], ['edit_score', 'ln_word_len', 'vec_dist'],
                       ['edit_score', 'ln_word_len_nosuffix', 'vec_dist'], ['edit_score', 'word_len', 'cos_dist'],
                       ['edit_score', 'word_len_nosuffix', 'cos_dist'], ['edit_score', 'ln_word_len', 'cos_dist'],
                       ['edit_score', 'ln_word_len_nosuffix', 'cos_dist']]

    # sem_ml_data = ['edit_score', 'word_len', 'vec_dist']
    # non_sem_data = ['edit_score', 'ln_word_len']

    df = pd.read_csv('./data/derivatives_data.csv', sep='\t', encoding='utf-8')
    data_df = df[['Sursa', 'Cuvant', 'Diminutiv']]
    data_df = data_df.dropna()
    print('Loading vectors')
    word_vectors : KeyedVectors = utils.p_load('./language_models/corola.300.20.p')

    src_vecs, der_vecs, delta_vecs, y = [], [], [], []

    count = 0
    for row in data_df.to_dict(orient='records'):
        source, derivative, is_dim = row['Sursa'], row['Cuvant'], row['Diminutiv']
        vecs = [word_vectors[word] if word in word_vectors else None for word in (source, derivative)]
        if [v for v in vecs if v is None]:
            continue
        src_vec, der_vec = vecs
        delta = der_vec - src_vec
        for data_list, row in zip((src_vecs, der_vecs, delta_vecs, y), (src_vec, der_vec, delta, is_dim)):
            data_list.append(row)
        count += 1
