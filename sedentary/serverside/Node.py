from typing import List

from sedentary.serverside import Module, Population


class Node:
    def __init__(self, modules: List[Module] = None, pops: List[Population] = None, goods: dict = None):
        self.Modules = modules
        self.Populations = pops
        self.Goods = goods

    def tick(self):

        for m in self.Modules:
            print("processing module {}".format(m.Name), self.Populations[0].Size, self.Populations[0].Counter)
            workforce = {}
            for p in self.Populations:
                if p.Level == m.Level:
                    draft = min(m.Size - workforce.get(p.Level, 0), p.Size - p.Counter)
                    workforce[p.Level] = workforce.get(p.Level, 0) + draft
                    p.Counter += draft
            if sum(workforce.values()) == 0:
                print("Aborting because no workforce found")
            for k, v in m.tick(workforce, self.Goods).items():
                if k in self.Goods.keys():
                    self.Goods[k] += v
                else:
                    self.Goods[k] = v
                print(f"Output {k}:{v}")
            if sum(workforce.values()):
                for p in reversed(self.Populations):
                    if p.Level in [x for x in workforce.keys() if workforce[x]]:
                        ret = min(p.Counter, workforce[p.Level])
                        p.Counter -= ret
                        workforce[p.Level] -= ret
                        print(f"returned {ret} {p.Name}")
        print(self.Goods)
        for p in self.Populations:
            p.Counter = 0
            if p.Size != 0:
                print("processing Population {}".format(p.Name))
                p.tick(self.Goods)
        if sum(p.Size for p in self.Populations) == 0:
            print("DEATH")
            return False
        return True


fields = Module("Fields", 1, 100, {"Food": 10}, {"Food": 100})
foraging = Module("Woods", 1, 1, {"Food": 0}, {"Food": 10})
farmers = Population("Farmers", 50, 1, {"Food": 1})
test = Node([fields, foraging], [farmers], {"Food": 4})

for i in range(10):
    print("Step", i, "Population:", test.Populations[0].Size, test.Goods)
    if not test.tick():
        break
print("Population:", test.Populations[0]._Size, test.Goods)
