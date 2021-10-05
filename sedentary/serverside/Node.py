from typing import Union

from sedentary.serverside import Module, Storage


class Node:
    def __init__(
        self,
        modules: list[Module] = None,
        goods: Union[dict[str, Storage], list[str]] = None,
    ):
        self.Modules = modules
        if not goods:
            self.Storage = {}
        elif isinstance(goods, list):
            self.Storage = {}
            for name in goods:
                self.Storage[name] = Storage(0, 1000)
        else:
            self.Storage = goods

    def price(self, ware: str) -> float:
        return self.Storage[ware].price()

    def buy(self, ware: str, amount: int, commit=False):
        return self.Storage[ware].buy(amount, commit)

    def sell(self, ware: str, amount: int, commit=False):
        return self.Storage[ware].sell(amount, commit)

    def tick(self, equalize_money=True):
        if equalize_money:
            avgmoney = sum(x.Money for x in self.Modules) / len(self.Modules)
            print("avgmoney", avgmoney)
            for m in self.Modules:
                m.Money = avgmoney
                print("processing module {}".format(m.Name))
                m.tick(self.Storage)
                if m.Error:
                    print(m.Status)


if __name__ == "__main__":

    fields = Module(
        "Fields", level=1, size=100, input_goods={"Food": 10}, output_goods={"Food": 100}
    )
    foraging = Module(
        "Woods", level=1, size=100, input_goods={"Food": 0}, output_goods={"Food": 10}
    )

    test = Node([fields, foraging], {"Food": Storage(4, 1000)})

    for i in range(10):
        print("Step", i, test.Storage)
        test.tick()
    print(test.Storage)
