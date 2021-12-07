import mplfinance as mpf
import pandas as pd


def main():
    # data = pd.read_pickle('data/data.BTC-USD.2016-01-01.GRAN900.brokers_inv_jozef_combo.pkl.xz')
    # data = pd.read_pickle('data/data.bitcoinchartsBTC-USD.2011.GRAN60.simple.pkl.xz')
    data = pd.read_pickle('data/data.BTC-USD.2016-01-01.GRAN86400.moon.pkl.xz')
    # data = data[:"20190501"]
    holdl = mpf.make_addplot(data['TestHoldlBroker_0.0000_0'])
    cross = mpf.make_addplot(data['TestMoonBroker_0.0010_0'])
    cross2 = mpf.make_addplot(data['TestReversedMoonBroker_0.0010_0'])
    # cross = mpf.make_addplot(data['TestCrossoverHullBroker_0.0007_101'])
    # cross = mpf.make_addplot(data['TestJozefHullBroker_0.0000_146'])
    # mpf.plot(data, type='candle', addplot=[cross])
    mpf.plot(data, type='candle', addplot=[cross, holdl, cross2])


if __name__ == "__main__":
    main()
