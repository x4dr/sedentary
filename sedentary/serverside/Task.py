import random
import time

from sedentary.serverside import TimeOut


class Task:
    def __init__(self,
                 time_offset: int,
                 time_rand: int,
                 rewards: dict,
                 reward_text: str,
                 conditions: dict,
                 costs: dict,
                 menu_entry: str,
                 flash_text: str,
                 tags: dict,
                 ):
        print(time_offset)
        self.Time_Offset = time_offset
        self.Time_Rand = time_rand
        self.Rewards = rewards
        self.Reward_Text = reward_text
        self.Conditions = conditions
        self.Costs = costs
        self.Menu_Entry = menu_entry
        self.Flash_Text = flash_text,
        self.Tags = tags

    @staticmethod
    def check_cond(conditions: dict, tocheck: dict):
        for c in conditions.keys():
            if tocheck.get(c, -1) < conditions[c]:
                return False
        return True

    @staticmethod
    def pay(costs: dict, tocheck: dict):
        if Task.check_cond(costs, tocheck):
            for c in costs.keys():
                tocheck[c] -= costs[c]
            return True
        return False

    def starttask(self, inventory: dict, uid):
        if self.pay(self.Conditions, inventory):
            if self.pay(self.Costs, inventory):
                return 0, \
                       TimeOut(self.Menu_Entry,
                               int(time.time()) + random.randint(0,self.Time_Rand) + self.Time_Offset,
                               self.Rewards, self.Reward_Text, uid), \
                       self.Flash_Text, \
                       inventory
            else:
                return 1, None, self.Costs, None
        else:
            return 2, None, self.Costs, self.Conditions
