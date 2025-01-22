
import utils

from string_distance import simple_string_distance as w_dist

substitution_costs = {
    ('t', 'ț') : 0.1,
    ('a', 'ă') : 0.1,
    ('â', 'i') : 0.2,
    ('ă', 'e') : 0.2,
}

def remove_final_vowels(s : str, count : int = -1) -> str:
    while s and s[-1] in 'aeiouăîâ' and count != 0:
        s = s[:-1]
        count -= 1
    return s

def guess_source(deriative : str, suffix : str, candidiates : list[str],
                 chop : bool = False) -> list[tuple[str, str, float]]:
    if not deriative.endswith(suffix):
        raise Exception('Derivative does not end in suffix')
    der_root = deriative[:-(len(suffix))]
    candidiates = [(c, remove_final_vowels(c, 1), w_dist(der_root, remove_final_vowels(c, 1), substitution_costs))
                   for c in candidiates]
    candidiates.sort(key=lambda t : t[-1])
    if chop and candidiates:
        candidiates = [t for t in candidiates if t[-1] == candidiates[0][-1]]
    return candidiates



if __name__ == "__main__":
    nouns : list[str] = utils.p_load('./nouns_doom1.p')
    suffix = 'ișor'
    possible_derivs = [n for n in nouns if n.endswith(suffix) and len(n) > len(suffix) + 1]
    for possible in possible_derivs:
        candidates = guess_source(possible, suffix, nouns, True)
        candidates.sort(key=lambda t : len(t[0]))
        print(possible, '\t', candidates[0][0], '\t', candidates)


