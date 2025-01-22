import pandas as pd
from gensim.models.keyedvectors import KeyedVectors
from transformers import BertTokenizer, BertModel
import numpy as np
import torch

import utils

def bert_encode_text(text : str | list[str], model : BertModel, tokenizer : BertTokenizer)\
        -> list[tuple[str, np.ndarray]]:
    # Tokenize and encode text using batch_encode_plus
    # The function returns a dictionary containing the token IDs and attention masks
    if isinstance(text, list):
        tokens = text
        is_split_into_words = True
    else:
        tokens = tokenizer.tokenize(text)
        is_split_into_words = False

    encoding = tokenizer.batch_encode_plus( [text],# List of input texts
        padding=True,              # Pad to the maximum sequence length
        truncation=True,           # Truncate to the maximum sequence length if necessary
        return_tensors='pt',      # Return PyTorch tensors
        add_special_tokens=True,    # Add special tokens CLS and SEP
        is_split_into_words = is_split_into_words,
    )
    input_ids = encoding['input_ids']  # Token IDs
    attention_mask = encoding['attention_mask']  # Attention mask
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        word_embeddings = outputs.last_hidden_state  # This contains the embeddings
    word_vec_list = []
    for word, vector in zip(tokens, word_embeddings[0][1:-1]):
        if not word.startswith('##'):
            # vector = np.array(vector)
            word_vec_list.append((word, np.array(vector)))
        else:
            word_vec_list[-1] = word_vec_list[-1][0] + word[2:], word_vec_list[-1][1]
    return word_vec_list


if __name__ == '__main__':
    print('Loading vectors')
    noun_vecs : dict[str, np.ndarray] = utils.p_load('./word_vectors/nouns_w2v.corola-big.p')
    print('Loading nouns')
    nouns : list[str] = utils.p_load('./nouns_doom1.p')
    print('Loading pairs')
    pair_df = pd.read_csv('./data/')