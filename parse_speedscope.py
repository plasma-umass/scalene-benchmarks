from io import StringIO
import json
from collections import defaultdict

def parse_speedscope(f: StringIO):
    speedscope_json = json.load(f)
    res_dict = defaultdict(lambda : defaultdict(lambda : 0))
    profiles = speedscope_json['profiles'][0]
    frames = speedscope_json['shared']['frames']
    for sample in profiles['samples']:
        for frameno in sample:
            frame = frames[frameno]
            res_dict[frame["file"]][frame["name"]] += 1
    return res_dict

if __name__ == '__main__':
    with open('speedscope.json', 'r') as f:
        print(parse_speedscope(f))
