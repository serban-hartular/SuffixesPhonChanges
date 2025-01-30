import itertools
import json
import subprocess

import requests
import pycurl



url = 'http://relate.racai.ro:5000/process'

def get_phon_syll(text : str) -> list[dict]:
    r = subprocess.run(f'curl http://relate.racai.ro:5000/process -d "text={text}&exec=word-phonetic-transcription"',
        capture_output=True)
    json_res = json.loads(r.stdout.decode())
    json_res = json_res['teprolin-result']['tokenized']
    return list(itertools.chain.from_iterable(json_res))




