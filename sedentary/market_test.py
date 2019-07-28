from __future__ import annotations

from typing import List, Union, Tuple

import matplotlib.pyplot as plt


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
    def __init__(self, name: str, sell_offers: List[Transaction], buy_offers: List[Transaction], storage: dict = None):
        self.Name = name
        self.Sell_Offers = sell_offers
        self.Buy_Offers = buy_offers
        self.Storage = storage if storage else {}
        self.Funds = 0

    def __repr__(self):
        return self.Name

    def price(self, good: str, buyprice=False):
        store = self.Storage.get(good, None)[:]
        store[0] -= 1 if buyprice else 0
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
                # print(f"{self.Name} is buying {transaction.Name} "
                #      f"from {transaction.Owner} "
                #      f"for {price}")
                self.Funds -= price
                newstore = self.Storage.get(transaction.Name, [0, 0])[:]
                newstore[0] += 1
                self.Storage[transaction.Name] = newstore
                # print(f"bringing storage to {self.Storage[transaction.Name][0]}/{self.Storage[transaction.Name][1]} "
                #      f"and funds to {self.Funds}.")
            else:
                # print(f"{self.Name} is selling {transaction.Name} "
                #      f"to {transaction.Owner} "
                #      f"for {price}")
                newstore = self.Storage.get(transaction.Name, [0, 0])[:]
                newstore[0] -= 1
                if newstore[0] < 0:
                    return False
                self.Funds += price
                self.Storage[transaction.Name] = newstore
                # print(f"bringing storage to {self.Storage[transaction.Name][0]}/{self.Storage[transaction.Name][1]} "
                #      f"and funds to {self.Funds}.")
            return True
        return False

    @staticmethod
    def cull(l):
        del [l[:-10]]

    def provision(self):

        self.cull(self.Sell_Offers)
        self.cull(self.Buy_Offers)

        for k in self.Storage.keys():
            # print(f"{k}: {self.Storage[k][0]}/{self.Storage[k][1]} = {p}")
            if self.Storage[k][0] + 0 < self.Storage[k][1]:
                #   print(f"{self.Name} trying to buy {k} at {p}")
                if self.buy(Transaction(k, self.price(g,True), self, lambda x, y: self.handle_transaction(x, y, True))):
                    print("success")
            elif self.Storage[k][0] - 0 > self.Storage[k][1]:
                #   print(f"{self.Name} trying to sell {k} at {p}")
                if self.sell(Transaction(k, self.price(g,False), self, lambda x, y: self.handle_transaction(x, y, False))):
                    print("success")
        self.profiteer()

    def profiteer(self):
        self.cull(self.Sell_Offers)
        self.cull(self.Buy_Offers)

        for k in self.Storage.keys():
            p = self.price(k)
            mintrans = min([x for x in self.Sell_Offers
                            if x.Owner != self
                            and x.Name == k],
                           key=lambda x: x.Price, default=Transaction.empty())
            maxtrans = max([x for x in self.Buy_Offers if x.Owner != self and x.Name == k],
                           key=lambda x: x.Price, default=Transaction.empty())
            if maxtrans.Price > p:
                print(f"{self.Name} trying to profiteer by selling at {p} "
                      f"since market price is {maxtrans.Price} at size {self.Buy_Offers}|{self.Sell_Offers}")
                self.sell(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, False)))
            elif mintrans.Name and (mintrans.Price < p):
                print(f"{self.Name} trying to profiteer by buying at {p} "
                      f"since market price is {mintrans.Price} at size {self.Buy_Offers}|{self.Sell_Offers}")
                self.buy(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, True)))
        # print()

    def marketstate(self):
        print(f"{self.Name} funds: {self.Funds}")
        print(self.Storage)
        for k in set([x.Name for x in self.Buy_Offers + self.Sell_Offers] + list(self.Storage.keys())):
            print(f"{k} : \n"
                  f"Buying {len([x for x in self.Buy_Offers if x and x.Name == k])}:"
                  f"{sorted([x for x in self.Buy_Offers if x and x.Name == k], key=lambda x: x.Price)}\n"
                  f"Selling {len([x for x in self.Sell_Offers if x and x.Name == k])}:"
                  f"{sorted([x for x in self.Sell_Offers if x and x.Name == k], key=lambda x: x.Price)}")

    def buy(self, offer: Union[Transaction, Tuple[str, Market]], instant=False):
        if not isinstance(offer, Transaction):
            return self.buy(
                Transaction(offer[0], self.price(offer[0],True), offer[1],
                            lambda x, y: offer[1].handle_transaction(x, y, True)), True)
        fill_order = min([x for x in self.Sell_Offers
                          if x.Name == offer.Name
                          and x.Price <= offer.Price
                          and x.Owner != offer.Owner],
                         key=lambda x: x.Price, default=Transaction.empty())
        if fill_order.Owner and (fill_order.Owner is not None):
            self.Sell_Offers.remove(fill_order)
            if fill_order.Callback(offer, fill_order.Price):
                offer.Callback(fill_order, fill_order.Price)
            self.provision()
            return offer.Price
        else:
            if not instant:
                self.Buy_Offers.append(offer)
            elif self.price(offer.Name,True) == offer.Price:
                return offer.Price if \
                    self.handle_transaction(offer, offer.Price, False) and \
                    offer.Callback(Transaction(offer.Name, offer.Price, self, None), offer.Price) else 0

            return 0

    def sell(self, offer: Union[Transaction, Tuple[str, Market]], instant=False):
        if not isinstance(offer, Transaction):
            return self.sell(
                Transaction(offer[0], self.price(offer[0]), offer[1],
                            lambda x, y: offer[1].handle_transaction(x, y, False)), True)
        fill_order = max([x for x in self.Buy_Offers
                          if x.Name == offer.Name
                          and x.Price >= offer.Price
                          and x.Owner != offer.Owner],
                         key=lambda x: x.Price, default=Transaction.empty())
        if fill_order.Owner and (fill_order.Owner is not None):
            self.Buy_Offers.remove(fill_order)
            if fill_order.Callback(offer, fill_order.Price):
                offer.Callback(fill_order, fill_order.Price)
                self.provision()
                return offer.Price
        else:
            if not instant:
                self.Sell_Offers.append(offer)
            elif self.price(offer.Name) == offer.Price:
                return offer.Price if \
                    self.handle_transaction(offer, offer.Price, True) and \
                    offer.Callback(Transaction(offer.Name, offer.Price, self, None), offer.Price) else 0

            return 0


sut = Market("Market", [], [], {"Food": [1000, 1000],
                                "Work": [1000, 1000],
                                "Iron": [1000, 1000]
                                })
pop = Market("Population", [], [], {"Food": [1000, 1000],
                                    "Work": [1000, 1000],
                                    "Iron": [1000, 1000]
                                    })

funds = {x: [0] for x in [sut, pop]}
amt = {}
price_dev = {}
for x in funds.keys():
    amt[x] = {}
    price_dev[x] = {}
    for g in x.Storage.keys():
        amt[x][g] = [x.Storage[g][0]]
        price_dev[x][g] = [x.price(g)]

i = 0
popsize = 10
farmsize = 0

while i < 25:
    i += 1
    print("day", i)
    bought = 0
    sold = 0
    fed = 0
    b= []
    for x in range(int(popsize)):
        b.append(sut.buy(("Food", pop)))
        if b[-1]:
            fed += 1
            bought += b[-1]
            sold += sut.sell(("Work", pop))
    net = sold - bought
    print(f"bought {fed} Food {b} for {bought} and sold Work for {sold} net {net}")

    worked = 0
    bought = 0
    sold = 0
    b = []
    for x in range(farmsize):
        if sut.price("Work") < sut.price("Food"):
            b.append(sut.buy(("Work", pop)))
            if b[-1]:
                sold += sut.sell(("Food", pop))
                bought += b[-1]
            worked += 1
    net += sold - bought
    print(f"bought {worked} Work for {bought} and sold the Food for {sold} net {sold-bought}")
    if worked == farmsize:
        farmsize += 1
    elif worked == 0:
        farmsize = max(1, farmsize - 1)
    print("Farmsize is", farmsize, "popsize is", popsize, "money change is", net )

    for x in funds.keys():
        funds[x].append(x.Funds)
        for g in sut.Storage.keys():
            amt[x][g].append(x.Storage[g][0])
            price_dev[x][g].append(x.price(g))

    print(">>>>>", sut.Funds)
sut.marketstate()

for g in sut.Storage.keys():
    for x in funds.keys():
        plt.plot(amt[x][g], label=x.Name + " " + g)
plt.ylabel("Amount")
plt.grid()
plt.legend()
plt.show()
for g in sut.Storage.keys():
    for x in funds.keys():
        plt.plot(price_dev[x][g], label=x.Name + " " + g, linewidth=4 if x == sut else 2)
plt.ylabel("Price")
plt.grid()
plt.legend()
plt.show()
for x in funds.keys():
    plt.plot(funds[x], label=x.Name)
plt.ylabel("Funds")
plt.legend()
plt.grid()
plt.show()
