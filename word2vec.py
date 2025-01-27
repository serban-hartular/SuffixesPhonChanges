from datasets import DatasetDict, Dataset

print('Importing libraries')
import pandas as pd
# from gensim.models.keyedvectors import KeyedVectors
from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
import numpy as np
from numpy.linalg import norm

import torch

import utils

def vec_distance(a : np.ndarray, b : np.ndarray) -> float:
    return float(norm(a - b))

def bert_encode_text_old(text : str, model : BertModel, tokenizer : BertTokenizer)\
        -> list[tuple[str, np.ndarray]]:
    # Tokenize and encode text using batch_encode_plus
    # The function returns a dictionary containing the token IDs and attention masks

    encoding = tokenizer.batch_encode_plus( [text],# List of input texts
        padding=True,              # Pad to the maximum sequence length
        truncation=True,           # Truncate to the maximum sequence length if necessary
        return_tensors='pt',      # Return PyTorch tensors
        add_special_tokens=True,    # Add special tokens CLS and SEP
        is_split_into_words = False,
    )
    input_ids = encoding['input_ids']  # Token IDs
    attention_mask = encoding['attention_mask']  # Attention mask
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        word_embeddings = outputs.last_hidden_state  # This contains the embeddings
    word_vec_list = list(zip(encoding, word_embeddings[0][1:-1]))
    return word_vec_list

def bert_encode_text(text : str, model : BertModel, tokenizer : BertTokenizer)\
        -> list[tuple[str, np.ndarray]]:
    input_ids = torch.tensor(tokenizer.encode(text, add_special_tokens=True)).unsqueeze(0)
    tokens = tokenizer.batch_decode(input_ids[0])[1:-1] # skip special tokens
    outputs = model(input_ids)
    last_hidden_states = outputs[0]
    token_vectors = [t.detach().numpy() for t in last_hidden_states[0][1:-1]] # skip special tokens
    return list(zip(tokens, token_vectors))


def df_to_tokenized_dataset(tokenizer, df: pd.DataFrame, column_dict: dict[str, str] = None,
                            split_ratio = 0.25) -> DatasetDict:
    if column_dict:
        df = df.rename(columns=column_dict)
    dataset = Dataset.from_pandas(df)
    tokenized_dataset = dataset.map(lambda d : tokenizer(d["text"], truncation=True), batched=True)
    tokenized_datasetdict = tokenized_dataset.train_test_split(split_ratio)
    return tokenized_datasetdict


if __name__ == '__main__':
    print('Loading vectors')
    # model : BertModel = utils.p_load('./language_models/bert-base-romanian-cased-v1-model.p')
    # tokenizer : BertTokenizer = utils.p_load('./language_models/bert-base-romanian-cased-v1-tokenizer.p')
    tokenizer = AutoTokenizer.from_pretrained("dumitrescustefan/bert-base-romanian-cased-v1")
    model = AutoModel.from_pretrained("dumitrescustefan/bert-base-romanian-cased-v1")

    pahar = bert_encode_text('pahar', model, tokenizer)
    paharel = bert_encode_text('păhărel', model, tokenizer)
