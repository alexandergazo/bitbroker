from math import sqrt

import numpy as np


def wma_last_value(data, n):

    mask = np.arange(n) + 1

    conv = np.convolve(data[-n:], mask[::-1], mode='valid') / sum(mask)
    return conv[0]


def wma(data, n):

    mask = np.arange(n) + 1

    conv = np.convolve(data, mask[::-1], mode='valid') / sum(mask)
    return conv


def hma_last_value(data, n):

    sub_data = data[- (n + int(sqrt(n))):]
    full = wma(sub_data, n)
    half = wma(sub_data, n // 2)
    aux = 2 * half[-len(full):] - full

    hull = wma_last_value(aux, int(sqrt(n)))

    return hull


def hma(data, n):

    full = wma(data, n)
    half = wma(data, n // 2)
    aux = 2 * half[-len(full):] - full

    hull = wma(aux, int(sqrt(n)))

    return hull
