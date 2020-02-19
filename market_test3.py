import pathlib
from random import random as nextfloat
from collections import defaultdict
from typing import Dict, Union, List, Optional


class ItemCollection(defaultdict):
    storagemax: dict

    def __init__(self, d: Union[None, Dict[str, int]] = None,
                 storagemax: Union[None, Dict[str, int]] = None):
        if d is not None:
            if "storagemax" in d.keys():
                raise Exception("storagemax in key!")
            super().update(d)
        if storagemax is None:
            self.storagemax = {}
        else:
            self.storagemax = storagemax
        super().__init__(int)

    def __getitem__(self, item: str) -> int:
        return super().__getitem__(item)

    def __setitem__(self, key: str, value: int):
        return super().__setitem__(key, value)

    def empty(self):
        return not any(x > 0 for x in super().values())

    def __repr__(self):
        return str({k: str(self[k]) + "/" + str(self.storagemax.get(k, None))
                    for k in set(set(self.storagemax.keys()).union(set(self.keys())))})

    def __str__(self):
        return super().__str__()

    def __add__(self, other):
        if isinstance(other, ItemCollection):
            res = ItemCollection(dict(self.items()), self.storagemax)
            for key, value in other.items():
                res[key] += value
            for key, value in other.storagemax.items():
                res.storagemax[key] += value
        else:
            raise NotImplementedError()
        return res

    def __isub__(self, other):
        if isinstance(other, dict):
            for key, value in other.items():
                if not isinstance(key, str):
                    raise NotImplementedError("keytype " + type(key))
                if not isinstance(value, int):
                    raise NotImplementedError("valuetype " + type(value))
                self[key] -= value
                if self[key] < 0:
                    raise Exception("subtraction led to subzero value in Itemcollection!")
            if isinstance(other, ItemCollection):
                try:
                    if other.storagemax:
                        self.storagemax = {key: self.storagemax.get(key, 0) - other.storagemax.get(key, 0)
                                           for key in set(self.storagemax.keys()).union(other.storagemax)}
                except AttributeError:
                    pass  # no storagemax is also empty
        else:
            raise NotImplementedError(type(other))
        return self

    def __iadd__(self, other):
        if isinstance(other, dict):
            for key, value in other.items():
                if not isinstance(key, str):
                    raise NotImplementedError("keytype " + type(key))
                if not isinstance(value, int):
                    raise NotImplementedError("valuetype " + type(value))
                self[key] += value
            if isinstance(other, ItemCollection):
                try:
                    if other.storagemax:
                        self.storagemax = {key: self.storagemax.get(key, 0) + other.storagemax.get(key, 0)
                                           for key in set(self.storagemax.keys()).union(other.storagemax)}
                except AttributeError:
                    pass  # no storagemax is also empty
        else:
            raise NotImplementedError(type(other))
        return self

    def required(self, req: 'ItemCollection') -> 'ItemCollection':
        """
        checks what else is required to fullfill the conditions set in req

        :param req: ItemCollection of items and counts
        :return: empty ItemCollection if everything is met, otherwise the needed difference
        """
        return ItemCollection({name: amount - self[name] for name, amount in req.items()
                               if self[name] < amount}, req.storagemax)

    def deduct(self, ded: 'ItemCollection', block: bool) -> 'ItemCollection':
        """
        deducts the requested amount of items (or as much as possible if block is false)

        :param block: wether or not to block the whole deduction if a part is unmet.
        :param ded: ItemCollection of items and counts to deduct
        :return: empty Itemcollection if successfull, otherwise a ItemCollection of unmet requirements
        """
        req = self.required(ded)
        if block and req.empty():
            for name, amount in ded.items():
                self[name] -= amount
        return req

    def spacerequired(self, req: 'ItemCollection') -> 'ItemCollection':
        """
        checks how much more storage is required to add the items from req
        :param req: ItemCollection to be added
        :return: empty ItemCollection if there is space, otherwise the needed difference
        """
        return ItemCollection(
            {name: amount + self[name] - self.storagemax.get(name, 0) for name, amount in req.items()
             if amount + self[name] - self.storagemax.get(name, 0) > 0})

    def spaceavailable(self) -> 'ItemCollection':
        return ItemCollection(
            {name: self.storagemax[name] - self[name] for name in self.storagemax.keys()})

    def add(self, ad: 'ItemCollection') -> 'ItemCollection':
        """
        :param ad: ItemCollection of items and counts to add
        :return: empty Itemcollection if successfull, otherwise a ItemCollection of unmet space requirements
        """
        req = self.spacerequired(ad)
        if req.empty():
            for name, amount in ad.items():
                self[name] += amount
            return ItemCollection()  # no issues
        else:
            return req  # diff needed

    def transfer(self, target: 'ItemCollection', amount: 'ItemCollection', block: bool) -> bool:
        if amount.empty():
            return False  # no transfer happened
        unavailable_items = self.required(amount)
        unavailable_space = target.spacerequired(amount)
        if unavailable_items.empty() and unavailable_space.empty():
            # transfer available in full
            if self.deduct(amount, True).empty() and target.add(amount).empty():
                # at least 1 item was transfered
                return True
            else:  # #shouldneverhappen
                raise Exception("inconsistent state:", self.deduct(amount, True), target.add(amount))
        else:
            impossible = {k: max(unavailable_space[k], unavailable_items[k]) for k in amount.keys()}
            if block:
                return False
            amount -= impossible
            return self.transfer(target, amount, block)  # recursion


class Module:
    """
    the smallest subdivision, a place where items can be stored or processes run
    """
    process: Optional['Process']
    inventory: ItemCollection

    def __init__(self, name, space: Union[ItemCollection, Dict[str, int]] = None, process: 'Process' = None):
        self.name = name
        theorymax = process.inputs + process.outputs
        self.inventory = ItemCollection(None, space)
        self.inventory += ItemCollection(None, self.inventory.spacerequired(theorymax))
        self.process = process

    @property
    def running(self) -> bool:
        return self.process.running if self.process else False

    def start(self):
        if not self.process:
            return False
        return self.process.start(self.inventory)

    def tick(self):
        if not self.process:
            return False
        return self.process.tick(self.inventory)

    @property
    def demand(self):
        return self.inventory.required(self.process.inputs)

    def __repr__(self):
        return "[Module:" + self.name + "]"

    def __str__(self):
        return self.__repr__()


class Node:
    modules: List[Module]

    def __init__(self, modules=None):
        self.modules = modules or []

    @property
    def inventory(self) -> ItemCollection:
        inv = ItemCollection()
        for m in self.modules:
            inv += m.inventory
        return inv

    def tick(self):
        print("tick...")
        mods = self.modules
        demand = ItemCollection()  # virtual
        for m in mods:
            demand += m.demand
        demand = ItemCollection(dict(demand.items()),
                                dict(demand.items()))  # the rest of the needed items / the total needed items

        for m in sorted(mods, key=lambda p: p.process.outputpriority):
            demand = m.inventory.deduct(demand, False)
        supply = demand.spaceavailable()  # flip to how much we have fullfilled
        for m in sorted(mods, key=lambda p: p.process.inputpriority, reverse=True):  # fullfillment pass
            dem = m.demand
            if supply.transfer(m.inventory, dem, True):  # try to deliver the requested amount
                m.process.inputpriority -= 1  # got what was needed so will need to wait more
            else:
                m.process.inputpriority += 1  # more important in the future
        for m in sorted(mods, key=lambda p: p.process.inputpriority, reverse=True):  # acceptance pass
            if supply.transfer(m.inventory, m.demand, False):  # try to transfer as much as possible
                print(f"dump {m.demand} of {supply} into {m}")
                m.process.inputpriority -= 1  # got what was needed so will need to wait more
            else:
                m.process.inputpriority += 1  # more important in the future
        if not supply.empty():
            raise Exception(f"noone accepted the partial request of {supply}")
        names = [m.process.name for m in mods]
        started = [m.start() for m in mods]
        for i, x in enumerate(started):
            if x:
                print(f"started: {names[i]}")
        finished = [m.tick() for m in mods]
        for i, x in enumerate(finished):
            if x:
                print(f"finished process: {names[i]}")
        if max(abs(x.process.inputpriority) for x in mods) > 1000:
            self.rebalance()

    def rebalance(self):
        print("REBALANCE! in:" + ", ".join([str(m) + str(m.process.inputpriority) for m in self.modules]))
        for i, m in enumerate(sorted(self.modules, key=lambda x: x.process.inputpriority + nextfloat())):
            # some shuffling within equal prio
            m.process.inputpriority = i
        print("REBALANCE! out:" + ", ".join([str(m) + str(m.process.inputpriority) for m in self.modules]))


class Process:
    name: str
    inputpriority: int
    outputpriority: int
    inputs: ItemCollection
    outputs: ItemCollection
    time: int
    curtime: Union[None, int]

    def __init__(self, name: str, inputs: Dict[str, int], outputs: Dict[str, int], time: int):
        self.name = name
        self.inputs = ItemCollection(inputs)
        self.outputs = ItemCollection(outputs)
        self.time = time
        self.curtime = None
        self.inputpriority = 0
        self.outputpriority = 0

    def start(self, inv: ItemCollection) -> bool:
        """
        starts process
        :param inv: inventory to make deductions from
        :return: True on Success, False otherwise
        """
        if not (self.running or inv.deduct(self.inputs, True)):
            self.curtime = self.time
            return True
        else:
            return False

    @property
    def running(self) -> bool:
        return self.curtime is not None

    def tick(self, inv: ItemCollection) -> bool:
        """
        progresses process
        :param inv: inventory to apply outputs to
        :return: True while finished
        """
        if self.curtime is None:
            return False
        if self.curtime < 1:
            if inv.add(self.outputs).empty():  # if adding successfull
                self.curtime = None  # reset
                return True
            else:
                print("could not", self.name, "because", inv.add(self.outputs), "cannot fit into", inv)
                return True  # else stay ready but dont add
        else:
            self.curtime -= 1  # countdown
            return False


city = Node()

with pathlib.Path("~/sedentary.conf").expanduser().open() as f:
    for line in f.readlines():
        print(line)
        if not line.strip() or line.strip().startswith("#"):
            continue
        seg = line.split("|")
        name, store, proc, inp, outp, duration = seg
        name = name.strip()
        store = {k.strip(): int(v) for k, v in [d.split(":") for d in store.split(",") if d.strip()]}
        proc = proc.strip()
        inp = {k.strip(): int(v) for k, v in [d.split(":") for d in inp.split(",")if d.strip()]}
        outp = {k.strip(): int(v) for k, v in [d.split(":") for d in outp.split(",")if d.strip()]}
        duration = int(duration)
        city.modules.append(Module(name, store, Process(proc, inp, outp, duration)))

for _ in range(100):
    city.tick()
    print(city.inventory)
