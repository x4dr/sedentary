from typing import Union


class StorageOverflow(Exception):
    pass


class StorageUnderflow(Exception):
    pass


class Storage:
    def __init__(self, current, maximum):
        self.maximum = maximum
        self._amount = 0
        self.amount = min(current, maximum)
        self.balancepoint = maximum / 2
        self.base_price = 100

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.amount}/{self.maximum}@{self.price()}"

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, x: int):
        if not x <= self.maximum:
            raise StorageOverflow(f"{x} > {self.maximum}]")
        elif not x >= 0:
            raise StorageUnderflow(f"{x} < 0")
        self._amount = x

    def price_of_delta(self, delta: int) -> float:
        return round(self.price_of_range(self.amount, self.amount + delta), 10)

    def price(self) -> float:
        return round(self.base_price * self.price_fun(self.amount / self.maximum), 10)

    @staticmethod
    def price_fun(x: float):
        """function of price at x, where x is fill ratio"""
        return 1 - 3 * x + 6 * x ** 2 - 4 * x ** 3

    @staticmethod
    def price_integral(x: float):
        """integral of price_fun"""
        return x - (3 / 2) * x ** 2 + 2 * x ** 3 - x ** 4

    def price_of_range(self, a, b):
        if a == b:
            return 0
        total = b - a
        a /= self.maximum
        b /= self.maximum
        return (
            self.base_price
            * total
            * (self.price_integral(b) - self.price_integral(a))
            / (b - a)
        )

    def price_mod_of(self, x) -> float:
        """approach where we look at remaining capacities and  adjust
        a lot of empty storage space => price modifier negative
        a lot of filled storage space = price modifier positive
        scaled to [-1,+1] 0 at balancepoint
        """
        current = self.balancepoint - x
        if x > self.balancepoint:
            target = self.maximum - self.balancepoint
        elif x < self.balancepoint:
            target = self.balancepoint
        else:
            return 0
        return current / target

    def buy(self, amount: int, offer=False):
        return self.trade(-amount, commit=not offer)

    def sell(self, amount: int, offer=False):
        return self.trade(amount, commit=not offer)

    def trade(self, storage_delta: int, commit=False) -> Union[None, float]:
        try:
            if not 0 <= self.amount + storage_delta <= self.maximum:
                # TODO: hook logging for over/under requests and ask for adjusting of target and max
                return None
            price = self.price_of_delta(storage_delta)
            if commit:
                self.amount += storage_delta
        except StorageOverflow or StorageUnderflow:
            return None
        return price
