import pandas as pd
from tqdm import tqdm


def main():
    data = pd.read_pickle('data/data.BTC-USD.2016-01-01.GRAN900.jozef.pkl.xz')

    normalization_ratio = data.iloc[0]['Close'] / 1000
    for label in tqdm(data.columns):
        if 'Broker' not in label:
            continue

        data[label] = data[label] / data['Close'] * normalization_ratio

    data.to_pickle('data/data.BTC-USD.2016-01-01.GRAN900.jozef.BTC.pkl.xz')


if __name__ == "__main__":
    main()
