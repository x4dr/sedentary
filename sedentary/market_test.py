from __future__ import annotations

from typing import List, Union, Tuple, Any

import matplotlib.pyplot as plt


class Transaction(object):
    def __init__(self, name, price, owner, callback):
        self.Name = name
        self.Price = price
        self.Owner = owner
        self.Callback = callback
        self.Deprecated = False

    @classmethod
    def empty(cls):
        return Transaction("", 0, None, None)

    def __str__(self):
        return f"{self.Owner}//{self.Name}:{self.Price}"

    def __repr__(self):
        return str(self)


class Market(object):
    Outstanding_Offers: List[Transaction]
    Sell_Offers: List[Transaction]
    Buy_Offers: List[Transaction]

    def __init__(self, name: str, sell_offers: List[Transaction], buy_offers: List[Transaction], storage: dict = None):
        self.Outstanding_Offers = []
        self.Name = name
        self.Sell_Offers = sell_offers
        self.Buy_Offers = buy_offers
        self.Storage = storage if storage else {}
        self.Funds = 0

    def __repr__(self):
        return self.Name

    def price(self, good: str, buyprice=False, adjustment=0):
        store = self.Storage.get(good, None)[:]
        if buyprice:
            return self.price(good, adjustment=1)
        if store is not None:
            if store[0] - adjustment == 0:
                return store[1] * 150
            else:
                return int(100 * store[1] / (store[0] - adjustment))
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

    def provision(self):
        self.Buy_Offers = [x for x in self.Buy_Offers if not x.Deprecated]
        self.Sell_Offers = [x for x in self.Sell_Offers if not x.Deprecated]
        for k in self.Storage.keys():
            p = self.price(k)
            # print(f"{k}: {self.Storage[k][0]}/{self.Storage[k][1]} = {p}")
            if self.Storage[k][0] + 0 < self.Storage[k][1]:
                # p=self.price(k,True)
                # print(f"{self.Name} trying to buy {k} at {p}")
                if self.buy(
                        Transaction(k, self.price(k, True), self, lambda x, y: self.handle_transaction(x, y, True))):
                    print(f"success, {self.Name} bought {k} at {p}")
            elif self.Storage[k][0] - 0 > self.Storage[k][1]:
                # p = self.price(k, False)
                # print(f"{self.Name} trying to sell {k} at {p}")
                if self.sell(
                        Transaction(k, self.price(k, False), self, lambda x, y: self.handle_transaction(x, y, False))):
                    pass  # print(f"success, {self.Name} sold {k} at {p}")
        self.profiteer()

    def profiteer(self):
        for k in self.Storage.keys():
            p = self.price(k)
            mintrans = min([x for x in self.Sell_Offers
                            if x.Owner != self
                            and x.Name == k],
                           key=lambda x: x.Price, default=Transaction.empty())
            maxtrans = max([x for x in self.Buy_Offers if x.Owner != self and x.Name == k],
                           key=lambda x: x.Price, default=Transaction.empty())
            if maxtrans.Price > p:
                pass  # print(f"{self.Name} trying to profiteer by selling at {p} "
                # f"since market price is {maxtrans.Price} at size {self.Buy_Offers}|{self.Sell_Offers}")
                self.sell(Transaction(k, p, self, lambda x, y: self.handle_transaction(x, y, False)))
            elif mintrans.Name and (mintrans.Price < p):
                pass  # print(f"{self.Name} trying to profiteer by buying at {p} "
                #       f"since market price is {mintrans.Price} at size {self.Buy_Offers}|{self.Sell_Offers}")
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

    def selectsell(self, offer):
        self.Sell_Offers = [x for x in self.Sell_Offers if not x.Deprecated]
        return [x for x in self.Sell_Offers
                if x.Name == offer.Name
                and x.Price <= offer.Price
                and x.Owner != offer.Owner]

    def buy(self, offer: Union[Transaction, Tuple[str, Market]], instant=False, nooffer=False):
        if not isinstance(offer, Transaction):
            return self.buy(
                Transaction(offer[0], self.price(offer[0], True), offer[1],
                            lambda x, y: offer[1].handle_transaction(x, y, True)), True)
        fill_order = min(self.selectsell(offer),
                         key=lambda x: x.Price, default=Transaction.empty())
        if fill_order.Owner and (fill_order.Owner is not None):
            self.Sell_Offers.remove(fill_order)
            if fill_order.Callback(offer, fill_order.Price):
                offer.Callback(fill_order, fill_order.Price)
            # self.provision()
            return offer.Price
        else:
            if not instant and not nooffer:
                self.Buy_Offers.append(offer)
            elif self.price(offer.Name, True) == offer.Price:
                return offer.Price if \
                    self.handle_transaction(offer, offer.Price, False) and \
                    offer.Callback(Transaction(offer.Name, offer.Price, self, None), offer.Price) else 0

            return 0

    def selectbuy(self, offer):
        self.Buy_Offers = [x for x in self.Buy_Offers if not x.Deprecated]
        return [x for x in self.Buy_Offers
                if x.Name == offer.Name
                and x.Price >= offer.Price
                and x.Owner != offer.Owner]

    def sell(self, offer: Union[Transaction, Tuple[str, Market]], instant=False, nooffer=False):
        if not isinstance(offer, Transaction):
            return self.sell(
                Transaction(offer[0], self.price(offer[0]), offer[1],
                            lambda x, y: offer[1].handle_transaction(x, y, False)), True)
        fill_order = max(self.selectbuy(offer),
                         key=lambda x: x.Price, default=Transaction.empty())
        if fill_order.Owner and (fill_order.Owner is not None):
            self.Buy_Offers.remove(fill_order)
            if fill_order.Callback(offer, fill_order.Price):
                offer.Callback(fill_order, fill_order.Price)
                # self.provision()
                return offer.Price
        else:
            if not instant and not nooffer:
                self.Sell_Offers.append(offer)
            elif self.price(offer.Name) == offer.Price:
                return offer.Price if \
                    self.handle_transaction(offer, offer.Price, True) and \
                    offer.Callback(Transaction(offer.Name, offer.Price, self, None), offer.Price) else 0

            return 0

    def build_offers(self, good: str, amount: int = None, buy=True):
        if amount is None:
            amount = self.Storage[good][0]            # use all
        return [self.build_offer(good, buy, a if buy else -a) for a in range(amount)]

    def build_offer(self, good: str, buy=True, adjustment=0):
        self.Outstanding_Offers.append(Transaction(good, self.price(good, adjustment=adjustment), self,
                                                   lambda x, y: self.handle_transaction(x, y, buy)))
        return self.Outstanding_Offers[-1]

    def deprecate_outstanding(self):
        for o in self.Outstanding_Offers:
            o.Deprecated = True

        self.Buy_Offers = [x for x in self.Buy_Offers if not x.Deprecated]
        self.Sell_Offers = [x for x in self.Sell_Offers if not x.Deprecated]


sut = Market("Market", [], [], {"Food": [10, 10],
                                "Work": [10, 10],
                                #  "Iron": [1000, 1000]
                                })
pop = Market("Population", [], [], {"Food": [10, 10],
                                    "Work": [10, 10],
                                    #   "Iron": [1000, 1000]
                                    })
emp = Market("Employers", [], [], {"Food": [10, 10],
                                   "Work": [10, 10],
                                   #   "Iron": [1000, 1000]
                                   })

funds = {x: [0] for x in [sut, pop, emp]}
amt = {}
price_dev = {}
pop_dev = {"Population": [], "Farmsize": []}
for x in funds.keys():
    amt[x] = {}
    price_dev[x] = {}
    for g in x.Storage.keys():
        amt[x][g] = [x.Storage[g][0]]
        price_dev[x][g] = [x.price(g)]

i = 0
popsize = 5
farmsize = 5

while i < 200:
    i += 1
    print("day", i)
    bought = 0
    sold = 0
    net = 0
    fed = 0
    laboured = 0

    for x in range(int(popsize)):
        pop.Storage["Food"][0] -= 1
        if pop.Storage["Food"][0] < 0:
            pop.Storage["Food"][0] = 0
            popsize -= 1
            continue
        pop.Storage["Work"][0] += 1
    pop.Storage["Food"][1] = int(popsize * 2)
    pop.Storage["Work"][1] = int(popsize * 2)
    for buying_food in pop.build_offers("Food", int(pop.Storage["Food"][1])):
        b = sut.buy(buying_food)
        if b:
            bought += b
            fed += 1
    swo=pop.build_offers("Work", buy=False)
    print(swo)
    for selling_work in swo:
        b = sut.sell(selling_work)

        if b:
            laboured += 1
            sold += b

    popsize += (pop.Storage["Food"][0] / (pop.Storage["Food"][1] + 1) - 1)

    net = sold - bought
    print(f"bought {fed} Food for {bought} and sold {laboured} Work for {sold} net {net}")

    for x in range(int(farmsize)):
        emp.Storage["Work"][0] -= 1
        if emp.Storage["Work"][0] < 0:
            emp.Storage["Work"][0] = 0
            farmsize -= 1
            break
        emp.Storage["Food"][0] += 1

    worked = 0
    marketed = 0
    sold = 0
    bought = 0
    for buying_work in emp.build_offers("Work", int(emp.Storage["Work"][1])):
        b = sut.buy(buying_work)
        if b:
            bought += b
            worked += 1
    for selling_food in emp.build_offers("Food", buy=False):
        b = sut.sell(selling_food)

        if b:
            marketed += 1
            sold += b

    emp.Storage["Food"][1] = farmsize * 2
    emp.Storage["Work"][1] = farmsize * 2

    farmsize += (emp.Storage["Work"][0] / (emp.Storage["Work"][1] + 1) - 1)

    net += sold - bought
    print(f"bought {worked} Work for {bought} and sold {marketed} Food for {sold} net {sold - bought}")

    print("Farmsize is", farmsize, "popsize is", popsize, "money change is", net)

    for x in funds.keys():
        funds[x].append(x.Funds)
        for g in sut.Storage.keys():
            amt[x][g].append(x.Storage[g][0])
            price_dev[x][g].append(x.price(g))
    pop_dev["Population"].append(popsize)
    pop_dev["Farmsize"].append(farmsize)

    sut.Storage["Food"][1] = (farmsize + popsize) * 2
    sut.Storage["Work"][1] = (farmsize + popsize) * 2

    print(">>>>>", sut.Funds, emp.Funds, pop.Funds)
sut.marketstate()
pop.marketstate()
emp.marketstate()


def smooth(x, smoothing_width):
    return (sum(x[((y - smoothing_width) if y > (smoothing_width - 1) else 0):y + 1]) /
            len(x[((y - smoothing_width) if y > (smoothing_width - 1) else 0):y + 1])
            for y in range(len(x)))


def scragglyness(x):
    result = 0
    for y in range(len(x) - 1):
        result += abs(1 - abs(x[y] / (x[y + 1] if x[y + 1] else 1)))
    return int(result)


graphstyle = ["r-", "b-", "y-", "ro", "bo", "yo"]
graphind = -1
for g in sut.Storage.keys():
    for x in funds.keys():
        graphind += 1
        s = scragglyness(amt[x][g])
        print("amt", g, x, s)
        plt.plot(list(smooth(amt[x][g], s)), graphstyle[graphind], label=x.Name + " " + g, linewidth=4 if x == sut else 2)

plt.ylabel("Amount")
plt.grid()
plt.legend()
plt.figure()
graphstyle = ["r-", "b-", "y-", "ro", "bo", "yo"]
graphind = -1
for g in sut.Storage.keys():
    for x in funds.keys():
        graphind += 1
        s = scragglyness(price_dev[x][g])
        print("pri", g, x, s)
        plt.plot(list(smooth(price_dev[x][g], s)), graphstyle[graphind], label=x.Name + " " + g, linewidth=4 if x == sut else 2)
plt.ylabel("Price")
plt.grid()
plt.legend()
plt.figure()
# '''
for x in funds.keys():
    s = scragglyness(funds[x])
    print("fun", x, s)
    plt.plot(list(smooth(funds[x], s)), label=x.Name)
plt.ylabel("Funds")
plt.legend()
plt.grid()
plt.figure()
# '''
for x in pop_dev.keys():
    plt.plot(pop_dev[x], "bo--", label=x)
    print("pop", x, scragglyness(pop_dev[x]))
plt.ylabel("Size")
plt.legend()
plt.grid()
plt.show()
# '''
