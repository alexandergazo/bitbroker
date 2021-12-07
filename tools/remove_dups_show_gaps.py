import datetime
import json
import sys


with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)

last = data[0]
new_data = [last]
for dictum in data[1:]:
    if last[0] - dictum[0] != 0:
        new_data.append(dictum)
    last = dictum
data = new_data

with open("lolol.json", 'w') as f:
    json.dump(data, f)

last, counter = data[0], 0
for i, dictum in enumerate(data[1:]):
    if last[0] - dictum[0] != int(sys.argv[2]):
        counter += 1
        print(f'Index: {i}', end='\t')
        print(f'Dates: {datetime.datetime.fromtimestamp(dictum[0])}', end=' ')
        print(f'{datetime.datetime.fromtimestamp(last[0])}', end='\t')
        print('Difference: {last[0] - dictum[0]} s')
    last = dictum
