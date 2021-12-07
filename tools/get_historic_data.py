#!/usr/bin/env python3
import argparse
import datetime
import json
import time

import pandas as pd
import requests
from tqdm import tqdm


API_RESPONSE_LIMIT = 300


def generate_filename(args):
    if args.format == 'json':
        format_ext = 'json'
    elif args.format == 'pd':
        format_ext = 'pkl'
    return f'data.{args.product}.{args.startdate}.GRAN{args.granularity}.{format_ext}'


def main(args):

    data = []
    date_range = pd.date_range(
        args.startdate,
        pd.Timestamp.now(),
        freq=f'{args.granularity * API_RESPONSE_LIMIT}S',
    )
    date_range = date_range.to_pydatetime().tolist() + [datetime.datetime.now()]

    reversed_date_range = reversed(date_range)
    end = next(reversed_date_range)
    for start in tqdm(reversed_date_range, total=len(date_range)):

        params = {
            'start': start.isoformat(),
            'end': end.isoformat(),
            'granularity': args.granularity,
        }

        while True:
            response = requests.get(args.endpoint, params=params)
            if response.ok:
                break
            print('Response not ok:', response.text)
            time.sleep(10)

        data.extend(response.json())

        end = start

    last = data[0]
    new_data = [last]
    for dictum in data[1:]:
        if last[0] - dictum[0] != 0:
            new_data.append(dictum)
        last = dictum
    data = new_data

    filename = generate_filename(args)
    if args.format == 'pd':

        df = pd.DataFrame(data, columns=['Date', 'Low', 'High', 'Open', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'], unit='s')
        df.index = pd.DatetimeIndex(df['Date'])
        df.to_pickle(filename + '.xz')

    elif args.format == 'json':

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    print('Gathered data saved to ', filename)
    print()


def test(args):

    print('Coinbase does not guarantee completness of the data so we run a continuity test...')
    print()

    filename = generate_filename(args)

    if args.format == 'json':
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)

    elif args.format == 'pd':

        # TODO
        raise NotImplementedError

    last, counter = data[0], 0
    for i, dictum in enumerate(data[1:]):
        if last[0] - dictum[0] != args.granularity:
            counter += 1
            print(f'Index: {i}', end='\t')
            print(f'Dates: {datetime.datetime.fromtimestamp(dictum[0])}', end=' ')
            print(f'{datetime.datetime.fromtimestamp(last[0])}', end='\t')
            print('Difference: {last[0] - dictum[0]} s')
        last = dictum

    print()
    print(f'Summary:\nTotal gathered entries: {len(data)}\nGaps count: {counter}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download historic candlestick data from coinbase.'
    )
    parser.add_argument(
        '--product',
        type=str,
        default='BTC-USD',
        help='Product ID in {Currency}-{Currency} format.',
    )
    parser.add_argument(
        '--startdate',
        type=str,
        default='2016-01-01',
        help='The date from which onward the candles are gathered.',
    )
    parser.add_argument(
        '--granularity',
        type=int,
        default=3600 * 24,
        choices=[60, 300, 900, 3600, 21600, 86400],
        help='Time window in seconds.',
    )
    parser.add_argument(
        '--format',
        type=str,
        default='json',
        choices=['json', 'pd'],
        help='Requested format of the saved data.',
    )

    args = parser.parse_args()

    args.endpoint = f'https://api.pro.coinbase.com/products/{args.product}/candles'

    print(args)

    # main(args)
    test(args)
