import argparse

import numpy as np
import pandas as pd
from finta import TA
from pandas import DataFrame
from pandas import Series


def HullRSI(
    ohlc: DataFrame,
    period: int = 14,
    column: str = "close",
) -> Series:

    delta = ohlc[column].diff()

    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    aux_up = DataFrame(data=ohlc, copy=True)
    aux_up['close'] = up
    aux_down = DataFrame(data=ohlc, copy=True)
    aux_down['close'] = down.abs()
    _gain = TA.HMA(aux_up, period=period)
    _loss = TA.HMA(aux_down, period=period)

    RS = _gain / _loss
    return pd.Series(100 - (100 / (1 + RS)), name=f"{period} period RSI")


def main(datapath):
    raw_data = pd.read_pickle(datapath)
    raw_data.columns = list(map(str.lower, raw_data.columns))

    ath = raw_data.close.copy()

    max_value = 0
    for idx, value in enumerate(ath):
        max_value = max(value, max_value)
        ath[idx] = max_value

    # for i in trange(2, 202, 20):
    #     raw_data[f'Hull_{i}'] = TA.HMA(raw_data, period=i)

    result = DataFrame(index=raw_data.index)
    # cols = list(filter(lambda x: x not in ['date', 'low', 'high', 'open', 'volume'], raw_data.columns))
    # for i, col in enumerate(tqdm(cols)):
    #     for col2 in cols[i + 1:]:
    #         result[f'{col}<{col2}'] = (raw_data[col] < raw_data[col2]) * 2 - 1

    result['%_ath'] = raw_data['close'] / ath
    result['log10close'] = np.log10(raw_data['close'])

    result['RSI'] = TA.RSI(raw_data)
    result['HullRSI'] = HullRSI(raw_data)

    result['dayofweek'] = raw_data.index.dayofweek
    result['quarter'] = raw_data.index.quarter

    result = pd.get_dummies(result, columns=['dayofweek', 'quarter'], drop_first=True)

    result['y'] = raw_data['close'].shift(-1)
    result['%y'] = result['%gain'].shift(-1)
    result['log10y'] = np.log10(result['y'])
    result['booly'] = result['y'] > raw_data['close']

    result['%gain'] = (raw_data['close'].shift(1) / raw_data['close']) - 1

    result.dropna(inplace=True)

    return
    result.to_pickle(datapath.replace('pkl.xz', 'preprocessed.pkl.xz'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create trading data.')
    parser.add_argument('--data', type=str, required=True, help='Path to the data file.')
    args = parser.parse_args()

    main(args.data)
