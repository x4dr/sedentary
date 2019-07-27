import math
import random
import time
from typing import List

import matplotlib.pyplot as plt

MARKETSIZE = 1000


def avg(x):
    if len(x):
        return sum(x) / len(x)
    else:
        return 0


class Transaction(object):
    def __init__(self, name, price, owner, callback):
        self.Name = name
        self.Price = price
        self.Owner = owner
        self.Callback = callback

    @classmethod
    def empty(cls):
        return Transaction("", 0, None, None)

    def __str__(self):
        return f"{self.Owner}//{self.Name}:{self.Price}"

    def __repr__(self):
        return str(self)


class Market(object):
    def __init__(self, sell_offers: List[Transaction], buy_offers: List[Transaction]):
        self.Sell_Offers = sell_offers
        self.Buy_Offers = buy_offers
        self.Storage = {}
        self.Funds = 0

    def __repr__(self):
        return "Market"

    def price(self, good: str):
        store = self.Storage.get(good, None)
        if store is not None:
            if store[0] == 0:
                return store[1] * 150
            else:
                return int(100 * store[1] / store[0])
        else:
            relevant = max([x for x in self.Sell_Offers + self.Buy_Offers if x.Name == good], key=lambda x: x.Price)
            return relevant.Price

    def handle_transaction(self, transaction=None, price=None, buying=None):
        if transaction:
            if buying:
                print(f"market is buying {transaction.Name} for {price}")
                self.Funds -= price
                newstore = self.Storage.get(transaction.Name, [0, 0])
                newstore[0] += 1
                self.Storage[transaction.Name] = newstore
                # print(f"bringing storage to {self.Storage[transaction.Name][0]}/{self.Storage[transaction.Name][1]} "
                #      f"and funds to {self.Funds}.")
            else:
                print(f"market is selling {transaction.Name} for {price}")
                self.Funds += price
                newstore = self.Storage.get(transaction.Name, [0, 0])
                newstore[0] -= 1
                if newstore[0] < 0:
                    raise Exception("sold nonexistant goods")
                self.Storage[transaction.Name] = newstore
                # print(f"bringing storage to {self.Storage[transaction.Name][0]}/{self.Storage[transaction.Name][1]} "
                #      f"and funds to {self.Funds}.")

    def cull(self, l):
        kill = []
        c = 0
        for t in l:
            c += 1
            # self owned deals, too many deals or bad deals
            if t.Owner == self or \
                    c > 10 or \
                    abs(t.Price - self.price(t.Name)) > 10:
                kill.append(t)
        for k in kill:
            l.remove(k)

    def provision(self, transaction=None, price=None, buying=None):

        self.cull(self.Sell_Offers)
        self.cull(self.Buy_Offers)

        for k in self.Storage.keys():
            p = self.price(k)
            # print(f"{k}: {self.Storage[k][0]}/{self.Storage[k][1]} = {p}")
            if self.Storage[k][0] + 5 < self.Storage[k][1]:
                print(f"market trying to buy {k} at {p}")
                self.buy(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, True)))
            elif self.Storage[k][0] - 5 > self.Storage[k][1]:
                print(f"market trying to sell {k} at {p}")
                self.sell(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, False)))

            mintrans = min([x for x in self.Sell_Offers if x.Owner != self],
                           key=lambda x: x.Price, default=Transaction.empty())
            maxtrans = max([x for x in self.Buy_Offers if x.Owner != self],
                           key=lambda x: x.Price, default=Transaction.empty())
            if maxtrans.Price > p:
                print(f"trying to profiteer by selling at {p} "
                      f"since market price is {maxtrans.Price} at size {len(self.Buy_Offers)}|{len(self.Sell_Offers)}")
                self.sell(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, False)))
            elif mintrans.Name and (mintrans.Price < p):
                print(f"trying to profiteer by buying at {p} "
                      f"since market price is {mintrans.Price} at size {len(self.Buy_Offers)}|{len(self.Sell_Offers)}")
                self.buy(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, True)))
        # print()

    def marketstate(self):
        print(f"funds: {self.Funds}")
        for k in set([x.Name for x in self.Buy_Offers + self.Sell_Offers] + list(self.Storage.keys())):
            print(f"{k} : \n"
                  f"{len(self.Buy_Offers)}"
                  f"{sorted([x for x in self.Buy_Offers if x and x.Name == k], key=lambda x: x.Price)}\n"
                  f"{len(self.Sell_Offers)}"
                  f"{sorted([x for x in self.Sell_Offers if x and x.Name == k], key=lambda x: x.Price)}")
        print()

    def buy(self, offer: Transaction):
        fill_order = min([x for x in self.Sell_Offers if x.Name == offer.Name and x.Price <= offer.Price],
                         key=lambda x: x.Price, default=Transaction.empty())
        if fill_order and (fill_order.Owner is not None):
            self.Sell_Offers.remove(fill_order)
            fill_order.Callback(offer, fill_order.Price)
            offer.Callback(fill_order, fill_order.Price)
            self.provision()
            print()
        else:
            self.Buy_Offers.append(offer)

    def sell(self, offer: Transaction):
        fill_order = max([x for x in self.Buy_Offers if x.Name == offer.Name and x.Price >= offer.Price],
                         key=lambda x: x.Price, default=Transaction.empty())
        if fill_order and (fill_order.Owner is not None):
            self.Buy_Offers.remove(fill_order)
            fill_order.Callback(offer, fill_order.Price)
            offer.Callback(fill_order, fill_order.Price)
            self.provision()
            print()
        else:
            self.Sell_Offers.append(offer)


def tradetest():
    supply = [100000]  # [MAXPRICE] * MARKETSIZE  # seed the market
    demand = [0]  # [MINPRICE] * MARKETSIZE
    i = 0
    t = time.time()
    while (not supply) or (not demand) or abs(min(demand) - max(supply)) > 2:
        i += 1
        print(f"D:{demand}\nS:{supply}\n")
        if len(supply) < MARKETSIZE:
            s = round(avg([max(demand), max(supply * 2)]), 0)
            print("trying to raise supply", s)
        else:
            s = round(avg([max(demand), avg(supply)]), 0)

        if len(demand) < MARKETSIZE:
            d = round(avg([0, min(supply)]), 0)
            print("trying to lower demand", d)
        else:
            d = round(avg([avg(demand), min(supply)]), 0)

        buy = sell = False
        '''
        if any(x - s >= 0 for x in demand):
            buy = True
            # highest bidder gets transaction because the new supply price is lower
        if any(y - d <= 0 for y in supply):
            sell = True
            # cheapest offer gets transaction because the new demand price is higher
            '''
        if buy:
            demand.remove(max(demand))
        else:
            supply.append(s)
        if sell:
            supply.remove(min(supply))
        else:
            demand.append(d)

        if len(demand) > MARKETSIZE:  # the oldest offer gets dropped
            demand.pop(0)
        if len(supply) > MARKETSIZE:
            supply.pop(0)
        if i % 100 == 0 and t + 3 < time.time():
            t = time.time()
            print(f"Round {i}\naverage supply cost:   {avg(supply):.2f}")
            print(f"average demand budget: {avg(demand):.2f}\n")
            print(f"current diff is : {round(abs(min(demand) - max(supply)), 2)}")

    supply = sorted(supply)
    supply = {x: supply.count(x) for x in supply}
    demand = sorted(demand, reverse=True)
    demand = {x: demand.count(x) for x in demand}

    print(i, "\navailable prices on market:", supply)
    print("fullfillable orders on market:", demand)


selloffers = [Transaction("Food", 75 + x, "INIT", lambda x, y: print("Test callback:", x, y)) for x in
              range(30, -1, -1)]

sut = Market([], [])
sut.Funds = 10000
sut.Storage["Food"] = [1001, 1000]
overtime_food = [sut.Storage["Food"][0]]
overtime_funds = [sut.Funds]
overtime_price = [sut.price("Food")]
i = 0
cheapfood = True
while i < 150000:  # or sum(overtime_funds[-100:]) < 100 * 1000:
    i += 1

    if cheapfood == (random.randint(0, 120) < 50):
        if sut.price("Food") < 1500:
            sale = Transaction("Food", sut.price("Food") + random.randint(0, 2), "TestBuy",
                               lambda x, y: print(f"Test Buying from {x} for {y}"))
            # print(f">external buyer trying to buy at at {sale.Price}")
            sut.buy(sale)
    else:
        sale = Transaction("Food", sut.price("Food") + random.randint(-2, 0), "TestSell",
                           lambda x, y: print(f"Test Selling to {x} for {y}"))
        print(f">external seller selling at {sale.Price}")
        sut.sell(sale)
    if sut.price("Food") < 95:
        if random.randint(0, sut.price("Food") * 50) == 0:
            cheapfood = False
    elif sut.price("Food") > 105:
        if random.randint(0, (200 - sut.price("Food")) * 30) == 0:
            cheapfood = True
    sut.provision()
    overtime_food.append(sut.Storage["Food"][0])
    overtime_funds.append(sut.Funds)
    overtime_price.append(sut.price("Food"))
    print(">>>>>", sut.Funds)
sut.marketstate()


def smooth(lis, smo):
    return [
        sum(lis[max(x - smo, 0):x + smo]) /
        len(lis[max(x - smo, 0):x + smo])
        for x in range(len(lis))]


print(i, end=" sm")
overtime_funds = smooth(overtime_funds[0:], 5)
print(end="o")
overtime_food = smooth(overtime_food[0:], 5)
print(end="o")
overtime_price = smooth(overtime_price[0:], 1)
print("th")

plt.plot(overtime_food)
plt.ylabel("Food")
plt.show()
plt.plot(overtime_funds)
plt.ylabel("Funds")
plt.show()
plt.plot(overtime_price)
plt.ylabel("FoodPrice")
plt.show()
