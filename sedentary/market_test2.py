from collections import defaultdict
from typing import List, Dict, Any, DefaultDict, Union, Tuple


class Process(object):
    Outputs: Dict[str, int]
    Inputs: Dict[str, int]

    def __init__(self, inputs: Dict[str, int], outputs: Dict[str, int]):
        self.Inputs = inputs
        self.Outputs = outputs

    def profit(self, m: 'Market') -> int:
        """given a market m, how much could theoretically be earned by this process"""
        return self.gains(m) - self.costs(m)

    def costs(self, m: 'Market') -> int:
        """given a market m, how much needs to be spend on all of the process"""
        return sum(x[0] for x in self.costs_by_input(m).values())

    def costs_by_input(self, m: 'Market') -> Dict[str, Tuple[int, int]]:
        """given a market m, how much needs to be spend on each input of the process"""
        return {item: m.price(item, buying=amount) for item, amount in self.Inputs.items()}

    def gains(self, m: 'Market') -> int:
        """given a market m, how much will be earned from all of the ouputs of the process"""
        return sum(x[0] for x in self.gains_by_output(m).values())

    def gains_by_output(self, m: 'Market') -> Dict[str, Tuple[int, int]]:
        """given a market m, how much will be earned from each of the ouputs of the process"""
        return {item: m.price(item, selling=amount) for item, amount in self.Outputs.items()}

    def __repr__(self):
        return "Inputs: " + str(self.Inputs) + " Outputs: " + str(self.Outputs)


class Agent(object):
    Processes: List[Process]
    Name: str
    Funds: int
    Status: DefaultDict[Any, int]

    def __init__(self, name, funds):
        self.Name = name
        self.Status = defaultdict(int)
        self.Funds = funds
        self.Minimum_Profit = {}
        self.Maximum_Expense = {}
        self.Processes = []

    def __str__(self):
        return f"{self.Name}${self.Funds}"

    def __repr__(self):
        return str(self)

    def best_process(self, good: Union[str, None], m: 'Market'):
        p = max((x for x in self.Processes if ((good in x.Outputs.keys()) if good is not None else 1)),
                key=lambda x: x.profit(m))
        print("considering processes:", p)
        profit = p.profit(m)
        if profit > 0:
            return p
        else:
            print("not profitable: ", profit)
            return None

    def interact(self, m: 'Market'):
        p = self.best_process(None, m)
        print(self, "best process", p)
        funds_before = self.Funds
        if p:
            for good in p.costs_by_input(m).items():
                m.buy(self, good, None)
            for good, price in p.gains_by_output(m).items():
                m.sell(self, good, price)
        return

    def buy(self, good, price):
        if self.Funds >= price:
            print(self, "buying", good, "for", price)
            self.Funds -= price
            self.Status[good] += 1
            return True
        return False

    def sell(self, good, price):
        if self.Status[good] > 0:
            print(self, "selling", good, "for", price)
            self.Status[good] -= 1
            self.Funds += price
            return True
        return False

    def annull(self, m: 'Market'):
        m.annull(self)


class Order(object):
    Good: str
    Owner: Agent
    Period: int
    Size: int  # how many to buy, negative to sell

    def __init__(self, owner, good, period, size):
        self.Owner = owner
        self.Good = good
        self.Period = period
        self.Size = size


class Transaction(object):
    Buying: bool
    Price: int
    Good: str
    Owner: Agent

    def __init__(self, name, price, owner, buying):
        self.Good = name
        self.Price = price
        self.Owner = owner
        self.Buying = buying

    @classmethod
    def empty(cls):
        return Transaction("", 0, None, None)

    def __str__(self):
        return f"{self.Owner}//{self.Good}:{self.Price}"

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return self.Price < other.Price

    def __le__(self, other):
        return self.Price <= other.Price

    def __add__(self, other):
        if other is Transaction:
            return self.Price + other.Price
        else:
            return self.Price + other

    def __radd__(self, other):
        return self.__add__(other)

    def transact(self, other: Agent):
        if not self.Buying:
            if self.Owner.sell(self.Good, self.Price):
                if other.buy(self.Good, self.Price):
                    return True
                else:
                    if self.Owner.buy(self.Good, self.Price):  # rollback
                        return False
                    else:
                        raise Exception("rollback failed!")
            else:
                return False
        else:
            if self.Owner.buy(self.Good, self.Price):
                if other.sell(self.Good, self.Price):
                    return True
                else:
                    if self.Owner.sell(self.Good, self.Price):  # rollback
                        return False
                    else:
                        raise Exception("rollback failed!")
            else:
                return False


class Market(object):
    Historical: Dict[str, float]
    Orders: List[Order]
    Sell_Offers: List[Transaction]

    Buy_Offers: List[Transaction]

    def __init__(self, name: str):
        self.Orders = []
        self.Name = name
        self.Sell_Offers = []
        self.Buy_Offers = []
        self.Historical = defaultdict(lambda: 100.)

    def __repr__(self):
        return self.Name

    def price(self, good: str, buying=0, selling=0) -> (int, int):
        demand = sorted(x for x in self.Buy_Offers if x.Good == good)
        supply = sorted(x for x in self.Sell_Offers if x.Good == good)
        delta = buying - selling
        price = 0
        extreme = 0
        if delta < 0:
            print("supply:", supply, delta)
            extreme = supply[-1].Price if supply else self.Historical[good]
            if len(supply) < -delta:
                price += extreme * (-delta - len(supply))  # assume highest price for the rest of them
                delta = -len(supply)
                print("adjusting sell")
            price += sum(supply[delta:])
        else:
            extreme = demand[0].Price if demand else self.Historical[good]
            if len(supply) < delta:
                price += self.Historical[good] * delta - len(supply)  # assume lowest price
                delta = len(supply)
                print("adjusting buy")
            price += sum(demand[:delta])
        print("price of", good, "=", price)
        return price, extreme

    def market(self, good):
        buying = sum(o.Size / o.Period for o in self.Orders if o.Good == good and o.Size > 0)
        selling = sum(-o.Size / o.Period for o in self.Orders if o.Good == good and o.Size < 0)
        return [buying, selling]

    def order(self, order: Order):
        self.Orders.append(order)

    def buy(self, buyer, good, maxprice):
        o = min([x for x in self.Sell_Offers if x.Good == good] or [None])

        if maxprice is None:  # buy under all circumstances
            if o:
                print(maxprice, o.Price,"<<<<<<<<<<<<<<<<<<<")
                maxprice = o.Price + 1
            else:
                maxbuy = max([x for x in self.Buy_Offers if x.Good == good] or [None])
                if maxbuy:
                    maxprice = maxbuy.Price + 1
                else:
                    maxprice = self.Historical[good]

        if o and o.Price <= maxprice and o.transact(buyer):
            self.Historical[good] = o.Price
            return True
        else:
            self.Buy_Offers.append(Transaction(good, maxprice, buyer, True))
            return False

    def sell(self, seller, good, minprice):
        o = max([x for x in self.Buy_Offers if x.Good == good] or [None])
        if o and o.Price >= minprice and o.transact(seller):
            self.Historical[good] = o.Price
            return True
        else:
            self.Sell_Offers.append(Transaction(good, minprice, seller, False))
            return False

    def annull(self, a: Agent, amt=None, bs="bs"):
        buy_candidates = sorted([x for x in self.Buy_Offers if x.Owner == a])
        sell_candidates = sorted([x for x in self.Sell_Offers if x.Owner == a], reverse=True)
        if "b" in bs:
            if amt is not None:
                self.Buy_Offers = [x for x in self.Buy_Offers if x not in buy_candidates[:amt]]
            else:
                self.Buy_Offers = [x for x in self.Buy_Offers if x not in buy_candidates]
        if "s" in bs:
            if amt is not None:
                self.Sell_Offers = [x for x in self.Sell_Offers if x not in sell_candidates[:amt]]
            else:
                self.Sell_Offers = [x for x in self.Sell_Offers if x not in sell_candidates]


GeneralMarket = Market("Market")

Farm = Agent("Farm", 1000)
Farm.Status.update({"Food": 110})
Farm.Processes.append(Process({"Work": 1}, {"Food": 1}))
Farm.Processes.append(Process({"Work": 20}, {"Food": 21}))
Person = Agent("Person", 1000)

Person.Processes.append(Process({"Food": 1}, {"Work": 1}))
print("Foodstate:", Farm.Status["Food"], Person.Status["Food"], GeneralMarket.price("Food"))
print("Muny", Farm.Funds, Person.Funds)

for round_ in range(1):
    # print("BO",sut.Buy_Offers)
    # print("SO",sut.Sell_Offers)
    Farm.interact(GeneralMarket)
    Person.interact(GeneralMarket)
    GeneralMarket.buy(Person, "Food", None)
    print("Foodstate:", Farm.Status["Food"], Person.Status["Food"], GeneralMarket.price("Food"))
    print("Muny", Farm.Funds, Person.Funds)
