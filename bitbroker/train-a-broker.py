import argparse

import pandas as pd
import tensorflow as tf
from tqdm import tqdm

from . import brokers
from .run_parallel_simulation import get_usd_series
from .run_simulation import get_order_frequency


def main(args):
    training_point = "20190101"
    # training_point = "20201201"
    data = pd.read_pickle(args.data)
    Xs = tf.convert_to_tensor(data.drop(['y', 'log10y', 'booly'], axis=1)[:training_point])
    val = tf.convert_to_tensor(data.drop(['y', 'log10y', 'booly'], axis=1)[training_point:])
    y = data['booly']
    # y = data['log10y'] - data['log10close']
    val_y = tf.convert_to_tensor(y[training_point:])
    y = tf.convert_to_tensor(y[:training_point])
    print(
        f"{(data['booly'] == 1).sum() / len(data) * 100 :.2f} % {(data['booly'] == 0).sum() / len(data) * 100 :.2f} %"
    )

    if args.train:

        inputs = tf.keras.Input(shape=(Xs.shape[1]))

        model = tf.keras.layers.Dense(200, activation='gelu')(inputs)
        model = tf.keras.layers.Dense(200, activation='gelu')(model)
        model = tf.keras.layers.Dropout(rate=args.dropout)(model)
        model = tf.keras.layers.Dense(1, activation='sigmoid')(model)

        model = tf.keras.Model(inputs=inputs, outputs=model)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(clipnorm=0.1),
            loss=tf.keras.losses.BinaryCrossentropy(),
            metrics=['accuracy'],
        )

        model.fit(
            x=Xs, y=y, batch_size=args.batch_size, epochs=args.epochs, validation_data=(val, val_y)
        )

        model.save(args.model_path)

    else:
        model = tf.keras.models.load_model(args.model_path)
        dat = data.drop(['y', 'log10y', 'booly'], axis=1)[training_point:]
        # data = pd.read_pickle('data/data.bitcoinchartsBTC-USD.2011.GRAN300.pkl.xz')[training_point:]
        data = pd.read_pickle('data/data.bitcoinchartsBTC-USD.2011.resampled.GRAN900.pkl.xz')[
            training_point:
        ]
        data = data[(100000 > data['Close']) & (data['Close'] > 100)]
        data = data.drop(data.index[-1])
        dat['prediction'] = model.predict(val)

        def gen():
            for _, row in tqdm(dat[training_point:].iterrows(), total=len(dat[training_point:])):
                yield row

        broker = brokers.TestAIBroker(args.model_path, [], gen().__next__, fee=0.000)

        try:
            broker.run()
        except StopIteration:
            pass

        broker._sell()

        print(broker.balance.USD, get_order_frequency(broker))

        import mplfinance as mpf

        s = get_usd_series(broker, dat[training_point:].index, data)
        ai = mpf.make_addplot(s)
        mpf.plot(data, type='candle', addplot=[ai])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create trading data.')
    parser.add_argument('--data', type=str, required=True, help='Path to the data file.')
    parser.add_argument("--learning_rate", default=0.0001, type=float, help="Learning rate.")
    parser.add_argument("--batch_size", default=8192, type=int, help="Batch size.")
    parser.add_argument("--epochs", default=10, type=int, help="Training epochs.")
    parser.add_argument("--dropout", default=0.5, type=float, help="Dropout rate.")
    parser.add_argument("--model_path", default="model.model", type=str, help="Model save path.")
    parser.add_argument("--train", default=False, action="store_true", help="Training the model.")
    args = parser.parse_args()

    main(args)
