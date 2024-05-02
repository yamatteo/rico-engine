import math
from typing import Sequence


class Estimator:
    def __init__(self, value=0.0, max_counter=None):
        self.estimate = float(value)
        self.counter = 0
        self.max_counter = max_counter

    def __float__(self):
        return self.estimate

    def put(self, value):
        if self.max_counter is not None and self.counter >= self.max_counter:
            alpha = 1.0 / self.max_counter
        else:
            self.counter += 1
            alpha = 1.0 / self.counter

        self.estimate = self.estimate + alpha * (value - self.estimate)

def upper_confidence_bound(seq: Sequence[Estimator], c: float = 1.4142) -> list[float]:
    total_counter = math.log(max(1, sum(est.counter for est in seq)))
    return [ float(est) + c*(total_counter/max(1, est.counter))**0.5 for est in seq ]