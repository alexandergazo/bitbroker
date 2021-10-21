import argparse
from collections import namedtuple
from enum import Enum
from tabulate import tabulate

import pandas as pd
from tqdm import trange

from brokers import TestCrossoverHullBroker
from brokers import TestJozefHullBroker
from brokers import TestNoLossCrossoverHullBroker

Balance = namedtuple('Balance', 'USD BTC')
Desire = Enum('Desire', 'buy sell none')


def load_data_pd(path):
    data = pd.read_pickle(path)
    print(len(data))
    data = data[(100000 > data['Close']) & (data['Close'] > 100)]
    print(len(data))
    # data = data.loc["20210726":]
    # data = data.loc["20210520":"20210720"]
    data = data.loc["20210420":"20210520"]
    print(len(data))
    return data


def simulate(raw_data, args):
    d = raw_data['Close']

    def data_feeder():
        for i in trange(args.period * 2 + 1, len(d)):
            yield d[i]

    hull_broker = TestCrossoverHullBroker(
        d.tolist()[:args.period * 2],
        args.period,
        data_feeder().__next__,
        args.fee
    )

    try:
        hull_broker.run()
    except StopIteration:
        pass

    hull_broker._sell()
    import numpy as np
    print(len(np.unique(hull_broker.history)) / (len(d) - 2 * args.period - 1))
    print(hull_broker.action_count / (len(d) - 2 * args.period - 1))

    return hull_broker.balance.USD


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulate trading strategies on the provided data.')
    parser.add_argument('--data', type=str, required=True,
                        help='Path to the data file. Either .json or pandas dataframe.')
    parser.add_argument('--period', type=int, required=True,
                        help='Period used for WMA or HULL.')
    parser.add_argument('--fee', default=0, type=float, help='Trading fee for bot.')
    args = parser.parse_args()

    raw_data = load_data_pd(args.data)

    table = []
    for p in trange(2, 90, 3):
        args.period = p
        USD_balance = simulate(raw_data, args)
        table.append([p, USD_balance])
    BASELINE = raw_data['Close'][-1] / raw_data['Close'][4] * 1000
    table.append(['BASELINE', BASELINE])
    print(tabulate(table, headers=['Period', 'Last Balance'], floatfmt=',.2f'))
