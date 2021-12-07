import argparse

import numpy as np
import pandas as pd
from tabulate import tabulate
from tqdm import trange

from . import brokers


def load_data(path):
    data = pd.read_pickle(path)
    data = data.loc["20190101":]
    data = data[(100000 > data['Close']) & (data['Close'] > 100)]
    return data


def simulate(raw_data, broker_cls, period, fee, return_index=False):
    d = raw_data['Close']

    start_idx = period * 2 + 1

    def data_feeder():
        for i in trange(start_idx, len(d)):
            yield raw_data.iloc[i]  # d[i]

    broker = broker_cls(period, d.tolist()[: period * 2], data_feeder().__next__, fee)

    try:
        broker.run()
    except StopIteration:
        pass

    broker._sell()

    return (broker, raw_data.Date[start_idx:]) if return_index else broker


def get_order_frequency(broker):
    return len(np.unique(broker.history)) / len(broker.history) * 100


def parallel_helper_simulation(args):
    raw_data, broker_cls, period, fee = args
    return simulate(raw_data, broker_cls, period, fee)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Simulate trading strategies on the provided data.'
    )
    parser.add_argument('--data', type=str, required=True, help='Path to the data file.')
    parser.add_argument('--fee', default=0, type=float, help='Trading fee for bot.')
    args = parser.parse_args()

    raw_data = load_data(args.data)

    table = []
    for period in range(2, 150, 3):
        broker = simulate(raw_data, brokers.TestSimpleHullBroker, period, args.fee)
        USD_balance = broker.balance.USD
        table.append([period, USD_balance, get_order_frequency(broker)])
        print(table[-1])
    BASELINE = raw_data['Close'][-1] / raw_data['Close'][4] * 1000
    table.append(['BASELINE', BASELINE])
    print(
        tabulate(
            table,
            headers=['Period', 'Last Balance', 'Order Frequency [%]'],
            floatfmt=',.2f',
        )
    )
