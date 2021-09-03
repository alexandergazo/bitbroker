#!/usr/bin/env python3

from tqdm import tqdm
import requests
import pandas as pd
from math import floor
import datetime
import json
import time


PRODUCT = 'BTC-USD'
ENDPOINT = f'https://api.pro.coinbase.com/products/{PRODUCT}/candles'
STARTDATE = '2016-01-01'


def main(params):

    freq = floor(300 / (24 * 3600 / params['granularity']))

    data = []
    date_range = pd.date_range(STARTDATE, pd.Timestamp.now(), freq=f'{freq}D')
    start = date_range[0]
    for date in tqdm(date_range[1:]):

        params['start'] = start.strftime("%Y-%m-%d")
        params['end'] = date.strftime("%Y-%m-%d")

        while True:
            response = requests.get(ENDPOINT, params=params)
            if response.ok: break
            print(response.text)
            time.sleep(1)

        data.extend(response.json()[::-1])

        start = date

    last = data[0]
    new_data = [last]
    for i, dictum in enumerate(data[1:]):
        if dictum[0] - last[0] != 0:
            new_data.append(dictum)
        last = dictum
    data = new_data

    with open(f'data.{PRODUCT}.{STARTDATE}.GRAN{params["granularity"]}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def test():

    with open(f'data.{PRODUCT}.{STARTDATE}.GRAN{params["granularity"]}.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    last = data[0]
    for i, dictum in enumerate(data[1:]):
        if dictum[0] - last[0] != 900:
            print(f'{i} {dictum[0]=} {last[0]=} {dictum==last} {dictum[0]-last[0]}')
        last = dictum


if __name__ == "__main__":
    params = {'granularity': 900}

    main(params)
    # test(params)
