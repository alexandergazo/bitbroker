import argparse
import multiprocessing as mp

import pandas as pd
from tqdm import tqdm

from . import brokers
from .run_simulation import load_data
from .run_simulation import simulate


def get_usd_series(broker, index, raw_data):
    data = []
    for balance, ts in zip(broker.history[1:], index):

        USD = balance.USD if balance.USD > 0 else balance.BTC * raw_data.loc[ts].Close
        data.append(USD)

    return pd.Series(data=data, index=index)


def parallel_helper_simulation(over):
    data_path, broker_cls, fee, period = over
    raw_data = load_data(data_path)
    finished_broker, index = simulate(raw_data, broker_cls, period, fee, return_index=True)
    return f'{broker_cls.__name__}_{fee:.4f}_{period}', get_usd_series(
        finished_broker, index, raw_data
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Simulate trading strategies on the provided data.'
    )
    parser.add_argument('--data', type=str, required=True, help='Path to the data file.')
    args = parser.parse_args()

    raw_data = load_data(args.data)

    args_override = [
        (args.data, broker, fee, period)
        for broker in [
            brokers.TestMoonBroker,
            brokers.TestReversedMoonBroker,
        ]  # [brokers.TestSimpleHullBroker]
        for fee in [0, 0.001]
        for period in [0]  # range(2, 200, 3)
    ] + [(args.data, brokers.TestHoldlBroker, 0, 0)]

    with mp.Pool() as pool:
        for name, series in tqdm(
            pool.imap(parallel_helper_simulation, args_override), total=len(args_override)
        ):
            raw_data[name] = series
            print(name, series.iloc[-1])

    raw_data.to_pickle(args.data.replace('pkl.xz', 'simple.pkl.xz'))
