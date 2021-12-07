from abc import ABC
from abc import abstractmethod
from collections import namedtuple
from enum import Enum

import ephem
import tensorflow as tf

from .indicators import hma
from .indicators import hma_last_value

Balance = namedtuple('Balance', 'USD BTC')
Desire = Enum('Desire', 'buy sell none')


class Broker(ABC):
    def __init__(self, available_data, candle_getter, fee=0):
        self.available_data = available_data
        self.balance = Balance(1000, 0)
        self.get_fresh_candle = candle_getter
        self.history = [self.balance]
        self.fee = fee

    def isholding(self):
        return self.balance.USD == 0 and self.balance.BTC > 0

    @abstractmethod
    def _get_desire(self):
        raise NotImplementedError

    def run(self):
        while True:
            new_candle = self.get_fresh_candle()
            self.available_data.append(new_candle['Close'])

            desire = self._get_desire()

            self._act(desire)
            self.history.append(self.balance)

    def _act(self, desire):
        if self.isholding() and desire == Desire.sell:
            self._sell()
        elif not self.isholding() and desire == Desire.buy:
            self._buy()

    def _estimate_buy_balance(self):
        BTC_price = self.available_data[-1]
        BTC_bought = self.balance.USD / BTC_price * (1 - self.fee)
        BTC_total = BTC_bought + self.balance.BTC
        return Balance(0, BTC_total)

    def _estimate_sell_balance(self):
        BTC_price = self.available_data[-1]
        USD_bought = self.balance.BTC * BTC_price * (1 - self.fee)
        USD_total = USD_bought + self.balance.USD
        return Balance(USD_total, 0)

    @abstractmethod
    def _buy(self):
        raise NotImplementedError

    @abstractmethod
    def _sell(self):
        raise NotImplementedError


class NoLossBroker(Broker):
    def _get_last_USD(self):
        for balance in reversed(self.history):
            if balance.USD > 0:
                return balance.USD

    def _act(self, desire):
        if self.isholding() and desire == Desire.sell:
            last_USD = self._get_last_USD()
            now_USD = self._estimate_sell_balance().USD
            if now_USD > last_USD:
                self._sell()
        elif not self.isholding() and desire == Desire.buy:
            self._buy()


class AIBroker(Broker):
    def __init__(self, model_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = tf.keras.models.load_model(model_path)
        self.offset = 0.00

    def _get_desire(self, candle):
        prediction = candle['prediction']
        if prediction > 0.5 + self.offset:
            return Desire.buy
        elif prediction < 0.5 - self.offset:
            return Desire.sell
        else:
            return Desire.none

    def run(self):
        while True:
            new_candle = self.get_fresh_candle()
            self.available_data.append(10 ** new_candle['log10close'])

            desire = self._get_desire(new_candle)

            self._act(desire)
            self.history.append(self.balance)


class AIRegressionBroker(Broker):
    def __init__(self, model_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = tf.keras.models.load_model(model_path)

    def _get_desire(self, candle):
        prediction = 10 ** candle['prediction']
        return Desire.buy if prediction > self.available_data[-1] else Desire.sell

    def run(self):
        while True:
            new_candle = self.get_fresh_candle()
            self.available_data.append(10 ** new_candle['log10close'])

            desire = self._get_desire(new_candle)

            self._act(desire)
            self.history.append(self.balance)


class TestBroker(Broker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_data

    def _buy(self):
        self.balance = self._estimate_buy_balance()

    def _sell(self):
        self.balance = self._estimate_sell_balance()


class AbstractHullBroker(Broker):
    def __init__(self, hull_period, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hull_period = hull_period


class CrossoverHullBroker(AbstractHullBroker):
    def _get_desire(self):
        hma_fast = hma_last_value(self.available_data, self.hull_period)
        hma_slow = hma_last_value(self.available_data, self.hull_period * 2)

        desire = Desire.buy if hma_fast > hma_slow else Desire.sell

        return desire


class CrossoverInverseHullBroker(AbstractHullBroker):
    def _get_desire(self):
        hma_fast = hma_last_value(self.available_data, self.hull_period)
        hma_slow = hma_last_value(self.available_data, self.hull_period * 2)

        desire = Desire.buy if hma_fast < hma_slow else Desire.sell

        return desire


class CrossoverJozefComboHullBroker(AbstractHullBroker):
    def _get_desire(self):
        hma_fast = hma_last_value(self.available_data, self.hull_period)
        hma_slow = hma_last_value(self.available_data, self.hull_period * 2)

        desire = Desire.buy if hma_fast > hma_slow else Desire.sell

        if desire == Desire.buy:
            return Desire.none if self.available_data[-1] < hma_fast else Desire.buy
        else:
            return Desire.sell if self.available_data[-1] < hma_fast else Desire.none


class SimpleHullBroker(AbstractHullBroker):
    def _get_desire(self):
        hma = hma_last_value(self.available_data, self.hull_period)

        return Desire.sell if self.available_data[-1] < hma else Desire.buy


class MoonBroker(AbstractHullBroker):
    def _get_desire(self, candle):
        if ephem.previous_full_moon(candle['Date']) < ephem.previous_new_moon(candle['Date']):
            return Desire.buy
        else:
            return Desire.sell

    def run(self):
        while True:
            new_candle = self.get_fresh_candle()
            self.available_data.append(new_candle['Close'])

            desire = self._get_desire(new_candle)

            self._act(desire)
            self.history.append(self.balance)


class ReversedMoonBroker(MoonBroker):
    def _get_desire(self, candle):
        moon_desire = super()._get_desire(candle)
        if moon_desire == Desire.sell:
            return Desire.buy
        elif moon_desire == Desire.buy:
            return Desire.sell
        else:
            return Desire.none


class JozefHullBroker(AbstractHullBroker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trendUP = True
        self.past_hma = hma(self.available_data, self.hull_period).tolist()

    def _get_desire(self):

        last_trend = self.trendUP

        hma_value = hma_last_value(self.available_data, self.hull_period)
        self.past_hma.append(hma_value)

        self.trendUP = self.past_hma[-1] > self.past_hma[-3]

        if last_trend != self.trendUP:
            return Desire.sell if self.available_data[-1] < self.past_hma[-1] else Desire.buy

        return Desire.none


# TODO fix later to inherit only from broker
class HoldlBroker(AbstractHullBroker):
    def _get_desire(self):
        return Desire.buy


class TestCrossoverHullBroker(TestBroker, CrossoverHullBroker):
    pass


class TestNoLossCrossoverHullBroker(TestBroker, CrossoverHullBroker, NoLossBroker):
    pass


class TestJozefHullBroker(TestBroker, JozefHullBroker):
    pass


class TestHoldlBroker(TestBroker, HoldlBroker):
    pass


class TestSimpleHullBroker(TestBroker, SimpleHullBroker):
    pass


class TestMoonBroker(TestBroker, MoonBroker):
    pass


class TestReversedMoonBroker(TestBroker, ReversedMoonBroker):
    pass


class TestAIBroker(TestBroker, AIBroker):
    pass


class TestAIRegressionBroker(TestBroker, AIRegressionBroker):
    pass
