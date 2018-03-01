class TimeOut:
    def __init__(self, row, finished_date=None, rewards=None, text=None, user_id=None, timeout_id=None):
        if finished_date is None:
            rewards = row['blob'].split("%%%%%")
            text = rewards[1]
            rewards = rewards[0]

            rewards = {x.split(":")[0]: x.split(":")[1] for x in rewards.split("\n")}
            self.__init__(row['type'], row['finished_date'], rewards, text,
                          row['user_id'], row['timeout_id'])
        else:
            self.Type = row
            self.FinishedDate = finished_date
            self.Rewards = rewards
            self.Text = text
            self.User_id = user_id
            self.Timeout_id = timeout_id

    def to_db(self):
        blob = "\n".join([r + ":" + str(self.Rewards[r]) for r in self.Rewards]) + "%%%%%" + self.Text
        return [self.User_id, self.Timeout_id, self.Type, blob, self.FinishedDate]

    def __str__(self):
        return self.Text.format(**self.Rewards)
