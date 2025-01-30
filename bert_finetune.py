import dataclasses

# from transformers import pipeline
# import pandas as pd
import re

@dataclasses.dataclass
class TextChunk:
    text : str
    url : str = ''
    words : list[tuple[str, tuple[int, int]]] = dataclasses.field(default_factory=list)
    diminutive_labels : dict[int, str] = dataclasses.field(default_factory=dict)
    def __post_init__(self):
        if not self.words:
            for match in re.finditer(r'\w+', self.text):
                self.words.append((match.group(), match.span()))




if __name__ == "__main__":
    tc = TextChunk('Bun, bun, e și ieftina')

    # dim_classifier = pipeline('text-classification', model="./my_isdim_model/save2")
    # df = pd.read_csv('./data/diminutive_suffixes.csv', sep='\t', encoding='utf-8')
    # for chunk in reddit_str_list:
    #     for word in re.split(r'[\s%s]+' % string.punctuation, chunk):
    #         if re.fullmatch(suffixes_nodia_regex, to_no_diacritics(word)):
    #             print(word, '\t', classifier(word))