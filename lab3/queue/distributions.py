import numpy as np


class AbstractDistribution:
    def generate_time(self):
        raise NotImplementedError


class ExponentialDistribution(AbstractDistribution):
    def __init__(self, lambda_: float):
        self._lambda = lambda_

    def generate_time(self):
        return np.random.exponential(1 / self._lambda)


class NormalDistribution(AbstractDistribution):
    def __init__(self, m: float, sigma: float):
        self._m = m
        self._sigma = sigma
        self._negative_counter = 0

    def generate_time(self):
        time = np.random.normal(self._m, self._sigma)

        if time < 0:
            self._negative_counter += 1
            print('Сгенерировано отрицательных времен обслуживания заявок:', self._negative_counter)
            return 0
        else:
            return time
