from .Storage import Storage


class Module:
    def __init__(
        self, name: str, level: int, size: int, input_goods: dict, output_goods: dict
    ):
        self.Name = name
        self.Level: int = level
        self.Maximum_Level: int = level
        self.Size: int = size
        self.Input: dict[str, int] = input_goods
        self.Output: dict[str, int] = output_goods
        self.Status = ""
        self.Error = ""
        self.Money = 0
        self.Minimum_Profit = 0

    def maximum_intake(self, storages: dict[str, Storage]) -> int:
        multiplier = self.Level
        for good, amt in self.Input.items():
            available = storages[good].amount
            if available < amt * multiplier:  # 20 < 10*3
                multiplier *= available / (amt * multiplier)
        return multiplier

    def production(self, storages: dict[str, Storage]) -> (int, int):

        cost = 0
        # get production costs
        for k, v in self.Input.items():
            storage = storages.get(k, None)
            if not storage or storage.amount == 0:
                self.Error = True
                self.Status = f"unable to input {k}"
            if v > storage.amount:
                return 0, 0
            cost += storage.buy(v, True)

        value = 0
        # get production value
        for k, v in self.Output.items():
            storage = storages.get(k, None)
            if not storage:
                storages[k] = Storage(0, 0)
                storage = storages[k]
            room = storage.maximum - storage.amount
            if room == 0:
                self.Error = True
                self.Status = f"unable to output {k}"
            if room < v:
                return 0, 0
            value += storage.sell(v, True)

        return value, cost

    def tick(self, storages: dict[str, Storage]):
        self.Error = False
        self.Status = "running"
        value, cost = self.production(storages)
        if cost > self.Money:
            self.Error = True
            self.Status = f"Needs additional {cost - self.Money} to buy Inputs"
            return
        if value - cost < self.Minimum_Profit:
            self.Error = True
            self.Status = f"Would lose {cost - value} Money when running"
            return
        self.Status = f"running"

        multiplier = self.maximum_intake(storages)
        for good, amt in self.Input.items():
            self.Money -= storages[good].buy(amt * multiplier)
        for good, amt in self.Output.items():
            self.Money += storages[good].sell(amt * multiplier)
