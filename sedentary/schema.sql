CREATE TABLE IF NOT EXISTS user (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL COLLATE NOCASE,
  email TEXT NOT NULL,
  pw_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
  user_id INTEGER,
  money INTEGER DEFAULT 0,
  experience INTEGER DEFAULT 0,
  blob TEXT DEFAULT '',
  FOREIGN KEY(user_id) REFERENCES user(user_id),
  UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS Tasks (
  Time_Offset INTEGER,
  Time_Rand INTEGER,
  Rewards TEXT,
  Reward_Text TEXT,
  Conditions TEXT,
  Costs TEXT,
  Menu_Entry TEXT,
  Flash_Text TEXT,
  Tags TEXT,
  UNIQUE(Menu_Entry)
);


CREATE TABLE IF NOT EXISTS timeouts (
  user_id INTEGER,
  timeout_id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,
  blob TEXT NOT NULL,
  finished_date INTEGER NOT NULL,
  FOREIGN KEY(user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS skills (
  user_id INTEGER,
  blob TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES user(user_id)
);

