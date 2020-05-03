import os
import json

dct = {}
for r, d, f in os.walk('caps'):
    for file in f:
        dct[file] = []
        with open('caps/{}'.format(file), 'r') as fp:
            for l in fp.readlines():
                l = l.strip('\n')
                if 'ADMIN' not in l:
                    dct[file] += [l]
with open('app/caps_mapping.json', 'w') as fp:
    json.dump(dct, fp, indent=2)