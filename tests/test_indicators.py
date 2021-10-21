import pandas as pd
import pytest

from bitbroker.indicators import hma
from bitbroker.indicators import hma_last_value
from bitbroker.indicators import wma
from bitbroker.indicators import wma_last_value


ohlc = pd.read_csv('tests/data/bittrex_btc-usdt.csv', index_col="date", parse_dates=True)


@pytest.mark.parametrize("test_input, expected",
                         [(([0, 0, 1], 3), [0.5]),
                          (([0, 0, 1], 2), [0, 2/3]),
                          (([0, 0, 1], 1), [0, 0, 1])])
def test_wma(test_input, expected):
    assert all(wma(*test_input) == expected)


@pytest.mark.parametrize("test_input, expected",
                         [(([1, 10, 100], 2), [13, 130]),
                          (([1, 10, 100, 1000], 2), [13, 130, 1300])])
def test_hma(test_input, expected):
    result = hma(*test_input)
    assert all(result == expected)


def test_hma_long():
    """
    Test data from https://github.com/peerchemist/finta
    """
    result = hma(ohlc['close'].tolist(), 16)[-1]
    result = round(result, 8)
    expected = 6186.93727146
    assert result == expected


def test_hma_last_value_long():
    """
    Test data from https://github.com/peerchemist/finta
    """
    result = hma_last_value(ohlc['close'].tolist(), 16)
    result = round(result, 8)
    expected = 6186.93727146
    assert result == expected


@pytest.mark.parametrize("test_input, expected",
                         [(([1, 0, 0], 2), 0),
                          (([6, 0, 0], 3), 1),
                          (([0, 0, 2], 3), 1),
                          (([100, 10, 2], 3), 21)])
def test_wma_last_value(test_input, expected):
    result = wma_last_value(*test_input)
    assert result == expected


@pytest.mark.parametrize("test_input, expected",
                         [(([1, 10, 100], 2), 130),
                          (([1, 10, 100, 1000], 2), 1300)])
def test_hma_last_value(test_input, expected):
    result = hma_last_value(*test_input)
    assert result == expected
