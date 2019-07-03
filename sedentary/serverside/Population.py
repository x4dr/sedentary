from math import ceil


def take(take_from, take_what, take_amount):
    if not (take_from.get(take_what, 0)):
        print(f"No {take_what} in {take_from}!")
        return 0
    actual = min(take_amount, take_from[take_what])
    take_from[take_what] -= actual
    return actual


class Population(object):
    def __init__(self, name: str, size: int, level: int, demands: dict):
        self.Name = name
        self._Size = size
        self.Counter = 0
        self.Storage = {}
        self.Bids = {}
        self.Level = level
        self.Demands = demands
        self.Funds = 0

    @property
    def Size(self):
        return int(self._Size)

    @Size.setter
    def Size(self, x):
        self._Size = x + self._Size - self.Size

    def tick(self, goods):
        self.Bids = {}
        fullfillment = {k: take(goods, k, ceil(self.Size * v * 1.09)) for k, v in self.Demands.items()}
        print("taking", fullfillment)
        fullfillment = sum(fullfillment.values()) / (sum(self.Demands.values())*self.Size)
        print("Fullfillment of {} needs is {}%".format(self.Name, int(fullfillment * 100)))
        if fullfillment:
            if fullfillment < 0.99:
                print("Population decay:", fullfillment, fullfillment ** 0.5)
            self._Size = self._Size * (fullfillment ** 0.5)
        else:
            self._Size = self._Size / 10
