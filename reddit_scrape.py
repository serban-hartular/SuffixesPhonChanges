
import requests

import lxml

def traverse_reddit_json(r) -> list[str]:
    l = []
    if isinstance(r, list):
            for c in r:
                l.extend(traverse_reddit_json(c))
    elif isinstance(r, dict):
        for k,v in r.items():
            if k in ("selftext", "title", "body"):
                l.append(str(v))
            else:
                l.extend(traverse_reddit_json(v))
    return l
