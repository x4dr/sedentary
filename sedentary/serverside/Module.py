from sedentary.serverside import take


class Module:
    def __init__(self, name: str, level: int, size: int, _input: dict, _output: dict):
        self.Name = name
        self.Level = level
        self.Size = size
        self.Input = _input
        self.Output = _output

    def tick(self, pops: dict, goods: dict):
        personnel = take(pops, self.Level, self.Size)
        material = {k: take(goods, k, v) for k, v in self.Input.items()}
        personnelratio = personnel / self.Size
        goodsratios = {k: (v / self.Input[k] if self.Input[k] else 1) for k, v in material.items()}
        minratio = min(goodsratios.values())
        print(f"Personnel needs at {personnelratio * 100}%; Goods needs at {minratio * 100}%")
        if minratio < personnelratio:
            delta = round(personnelratio - minratio,6)
            if delta:
                print(personnelratio, minratio, "ratio diff", delta, "giving back", self.Size * delta, "People")
                pops[self.Level] += int(self.Size * delta)
        else:
            minratio = personnelratio
        if minratio < 1:
            for g in material.keys():
                delta = ((material[g] / self.Input[g]) if self.Input[g] else 1) - minratio
                if delta:
                    print("ware ratio diff", delta, "giving back", self.Input[g] * delta, g)
                    goods[g] += int(self.Input[g] * delta)

        result = {k: int(v * minratio) for k, v in self.Output.items()}
        print("{} returning {}".format(self.Name, ",".join(["{} {}".format(int(v), k) for k, v in result.items()])), )
        return result
