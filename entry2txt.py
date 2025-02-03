import json
from collections import defaultdict

import lxml
import pandas as pd
from lxml import etree
import re

import utils

BOLD = {'style': 'font-weight: bold'}, '#'
UNDERLINE = {'style': 'text-decoration:underline'}, '_'
ITALIC = {'style': 'font-style: italic;'}, '*'
DOUBLE = {'style': 'text-decoration:double'}, '!'

MARKUPS = [BOLD, UNDERLINE, ITALIC]

def match_markup(node: lxml.etree._Element, markup : tuple[dict, str]) -> str:
    for k,v in markup[0].items():
        if k in node.attrib and v in node.attrib[k]:
            return markup[1]
    return ''

def match_all_markups(node: lxml.etree._Element, markup_list : list[tuple[dict, str]], closing : bool) -> str:
    if closing:
        markup_list = markup_list[::-1] # reverse order
    markup_str = ''.join([match_markup(node, m) for m in markup_list])
    return markup_str

def entry_to_text(node: lxml.etree._Element, is_first = True) -> str:
    s = match_all_markups(node, MARKUPS, False)
    s += (node.text if node.text is not None else '')
    for child in node.getchildren():
        s += entry_to_text(child, False)
    s += match_all_markups(node, MARKUPS, True)
    s += (node.tail if node.tail is not None else '')
    if is_first:
        s = s.strip()
    return s

def split_entry_string(entry_str : str) -> list[str]:
    # this sucks
    # replace [;,] in parentheses with #[;,]
    entry_str_hash = re.sub(r'([\[\(][^\[\(\]\]]*)([,;])([^\(\[\]\)]*[\)\]])', r'\1&&\3', entry_str)
    # split by commas and semicolons that are not in parentheses
    entry_str_split = re.split(r'[,;]', entry_str_hash)
    # reintroduce commas
    entry_str_split = [s.replace('&&', ',').strip() for s in entry_str_split]
    return entry_str_split

def make_two(n : dict) -> (dict, dict):
    keys = n['sequence'][0].split('/')[:2]
    keys = [re.findall(r'#([^#]+)#', k)[0] for k in keys]
    forms = [re.sub(r'[0-9]+', '', k) for k in keys]
    stresses = [f.index('_') if '_' in f else -1 for f in forms]
    forms = [f.replace('_', '') for f in forms]
    plur = n['PlForms2']
    if len(plur) < 2:
        plur = plur * 2
    copies = [dict(n), dict(n)]
    copies = [d|{'key':k, 'SgForm':f, 'SgStress':s, 'PlForms2':[p]} for d,k,f,s,p in
              zip(copies, keys, forms, stresses, plur)]
    return copies


def check_desp(r: dict) -> bool:
    if r['Desp'] == '': return True
    desp = r['Desp'].replace('"', '')
    word = r['out_form'].replace('"', '')
    i = word.find(desp)
    if i == -1:
        return False
    i2 = word[i+len(desp):].find(desp)
    if i2 != -1:
        return False
    return True


def vowel_check(word : str) -> bool:
    sylls = word.split('-')
    for i, syl in enumerate(sylls):
        vowels = re.findall('[aeiouăîâ]+', syl)
        if len(vowels) == 1:
            continue
        if len(vowels) == 2 and vowels[1] == 'i' and i == len(sylls)-1 and syl[-1] == 'i':
            continue
        return False
    return True

def check_syllables(word : str, stressed_letter_index : int) -> (str, int):
    sylls = word.split('-')
    stressed = [i for i, syl in enumerate(sylls) if '"' in syl]
    if len(stressed) > 1 or len(stressed) == 0 and len(sylls) > 1:
        return ('', -1)
    sylls = [syl.replace('"', '') for syl in sylls]
    if len(sylls) == 1: # mono syllabic
        return sylls[0], -1
    stressed_syllable = stressed[0]
    word_nosep = word.replace('"', '').replace("-", "")
    if stressed_letter_index >= len(word_nosep) or word_nosep[stressed_letter_index] not in 'aeiouăîâ':
        return ('', -1)
    char_count = 0
    for i, syl in enumerate(sylls):
        if stressed_letter_index >= char_count and stressed_letter_index < char_count + len(syl):
            if i != stressed_syllable:
                return ('', -1)
            return ('-'.join([('"' if j == stressed_syllable else '') + _syl for j, _syl in enumerate(sylls)]),
                    stressed_letter_index - char_count)
        char_count += len(syl)
    return ('', -1)


def str_to_symbol_list(s : str) -> list[str]:
    mult_char_symbols = ['e̯', 'i̯', 'o̯', 'u̯']
    l = []
    while s:
        c_in_multi = False
        for multi in mult_char_symbols:
            if s.startswith(multi):
                l.append(multi)
                s = s[len(multi):]
                c_in_multi = True
                break
        if not c_in_multi:
            l.append(s[0])
            s = s[1:]
    return l



def syll_to_phon(word : str, vowel_dict: dict[str, list[str]], stress_vowel_index : int = -1) -> str:
    dzh = 'ğ'
    tsch = 'č'
    if not word or '-' in word and '"' not in word:
        print('Error ' + word)
        return None
    word = word.replace('â', 'î')
    sylls = word.split('-')
    phon_sylls = []
    for si, syl in enumerate(sylls):
        vowels = re.findall('[aeiouăî]+', syl)
        if len(vowels)==2 and vowels[1]=='i' and si==len(sylls)-1 and syl[-1]=='i':
            # short final i
            syl = syl[:-1] + 'i̯'
            vowels = vowels[:1]
        if len(vowels)!=1:
            print('Error vowels ' + word)
            return None
        vowels = vowels[0]
        phon_vowels = vowel_dict[vowels]
        if not phon_vowels:
            print(f'Error center {vowels} not allowed')
            return None
        if len(phon_vowels)==1:
            syl = syl.replace(vowels, phon_vowels[0])
        elif si==len(sylls)-1 and '"' in syl and syl[-2:]=='iu': # it's 'iu'
            syl = syl.replace('iu', 'iu̯') # fistichiu
        else:
            syl = syl.replace('iu',   'i̯u')
        if '"' in syl and stress_vowel_index:
            symbol_list = str_to_symbol_list(syl.replace('"', ''))
            if symbol_list[stress_vowel_index] not in ('a', 'e', 'i', 'o', 'u', 'ă', 'î'):
                print('Stress index warning ' + word)
        phon_sylls.append(syl)
    word = "-".join(phon_sylls)
    word = re.sub(r'(c)([ei)])', fr'{tsch}\2', word)
    word = re.sub(r'(g)([ei)])', fr'{dzh}\2', word)
    word = re.sub(r'ch?', 'k', word)
    word = re.sub(r'gh', 'g', word)

    return word

def move_stress(word : str, new_stress_index: int) -> str:
    sylls = word.split('-')
    if len(sylls) == 1:
        return word
    if new_stress_index < 0 or new_stress_index >= len(sylls):
        return None
    sylls = [('"' if i == new_stress_index else '')  + syl.replace('"', '')
             for i, syl in enumerate(sylls)]
    return '-'.join(sylls)

def find_stress(word : str, zero_if_single_syllable : bool = True) -> int:
    sylls = word.split('-')
    if len(sylls) == 1:
        return 0 if zero_if_single_syllable else -1
    stresses = [i for i, syl in enumerate(sylls) if '"' in syl]
    return stresses[0] if len(stresses) == 1 else -1

def change_pl_stress(r : dict, sing_key_dict : dict[str, int]) -> tuple[str, bool]:
    if r['Num'] == 'Sing' or r['key'] not in sing_key_dict:
        return r['Silabic'], False
    stress0 = find_stress(r['Silabic'])
    stress1 = sing_key_dict[r['key']]
    if stress0 == stress1:
        return r['Silabic'], False
    return move_stress(r['Silabic'], stress1), True




if __name__ == "__main__":
    df = pd.read_excel('./data/Nons_Phon_Syll5.xlsx')
    df = df.fillna('')


    # doom_json = open('./dictionaries/doom.jsonl', 'r', encoding='utf-8').readlines()
    # doom_items = [json.loads(s) for s in doom_json]
    # doom_entries = [{'url':d['url'], 'entries':[lxml.etree.fromstring(e) for e in d['entries']]} for d in doom_items]
    #
    # entries_chunks = []
    # for item in doom_entries:
    #     for entry in item['entries']:
    #         entries_chunks.append(split_entry_string(entry_to_text(entry)))
    # entry_dicts = []
    # for entry_chunk in entries_chunks:
    #     match = re.match(r'#(.+)#', entry_chunk[0])
    #     if not match or not match.groups():
    #         print('No match for ', entry_chunk)
    #     else:
    #         entry_dicts.append({'key':[match.groups()[0]], 'sequence':entry_chunk})
    #
    # nouns = []
    #
    # for n in nouns:
    #     plurs = []
    #     for s in n['sequence']:
    #         if 'pl.' in s:
    #             plurs = re.findall(r'\*[^\*]+\*', s)
    #             plurs = [p[1:-1] for p in plurs]
    #             break
    #     n['PlStress'] = [p.find('_') for p in plurs]
    #     n['PlForms'] = [p.replace('_', '') for p in plurs]
