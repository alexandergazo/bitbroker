from abc import ABC
from abc import abstractmethod
from collections import namedtuple
from enum import Enum

from indicators import hma
from indicators import hma_last_value

Balance = namedtuple('Balance', 'USD BTC')
Desire = Enum('Desire', 'buy sell none')


class Broker(ABC):
    def __init__(self, available_data, hull_period, price_getter, fee=0):
        self.available_data = available_data
        self.hull_period = hull_period
        self.balance = Balance(1000, 0)
        self.get_fresh_price = price_getter
        self.history = [self.balance]
        self.fee = fee

    def isholding(self):
        return self.balance.USD == 0 and self.balance.BTC > 0

    @abstractmethod
    def _get_desire(self):
        raise NotImplementedError

    def run(self):
        while True:
            new_price = self.get_fresh_price()
            self.available_data.append(new_price)

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


class TestBroker(Broker):
    def _buy(self):
        self.balance = self._estimate_buy_balance()

    def _sell(self):
        self.balance = self._estimate_sell_balance()


class CrossoverHullBroker(Broker):
    def _get_desire(self):
        hma_fast = hma_last_value(self.available_data, self.hull_period)
        hma_slow = hma_last_value(self.available_data, self.hull_period * 2)

        desire = Desire.buy if hma_fast < hma_slow else Desire.sell

        return desire


class JozefHullBroker(Broker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trendUP = True

    def _get_desire(self):

        last_trend = self.trendUP

        hull = hma(self.available_data, self.hull_period)

        if (hull[-1] > hull[-3]) and not self.trendUP:
            self.trendUP = True
        elif hull[-1] < hull[-3] and self.trendUP:
            self.trendUP = False

        if last_trend != self.trendUP:
            return Desire.sell if self.available_data[-1] < hull[-1] else Desire.buy

        return Desire.none


class TestCrossoverHullBroker(TestBroker, CrossoverHullBroker):
    pass


class TestNoLossCrossoverHullBroker(TestBroker, CrossoverHullBroker, NoLossBroker):
    pass


class TestJozefHullBroker(TestBroker, JozefHullBroker):
    pass
