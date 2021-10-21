import json
import pandas as pd
import sys


with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)

filename = '.'.join(sys.argv[1].split('.')[:-1]) + '.pkl.xz'

df = pd.DataFrame(data, columns=['Date', 'Low', 'High', 'Open', 'Close', 'Volume'])
df['Date'] = pd.to_datetime(df['Date'], unit='s')
df.index = pd.DatetimeIndex(df['Date'])
df.to_pickle(filename)
