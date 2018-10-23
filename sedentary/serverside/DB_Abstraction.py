from sqlite3 import dbapi2 as sqlite3
from typing import Union

from flask import _app_ctx_stack, request, abort, session
from flask import g
from werkzeug.security import generate_password_hash

from sedentary import app
from sedentary.serverside import TimeOut
from sedentary.serverside.Task import Task


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def add_timeout(write: TimeOut):
    db = get_db()
    write = write.to_db()
    db.execute("INSERT INTO timeouts (user_id, type, blob, finished_date) VALUES (?,?,?,?);",
               [write[0]] + write[2:])
    db.commit()


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()
    if exception:
        print("encountered exception during teadown: ", exception)


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print("database initialized")


def query_db(query: str, args=(), one: bool = False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('SELECT user_id FROM user WHERE username = ?',
                  [username], one=True)
    return rv[0] if rv else None


def get_inventory():
    raw = query_db('SELECT money,experience,blob FROM inventory WHERE user_id = ?',
                   [session['user_id']], one=True)
    if not raw:
        return {}
    inv = {l.split(":")[0]: int(l.split(":")[1]) for l in raw[2].split("\n") if ":" in l}
    inv["money"] = raw[0]
    inv["experience"] = raw[1]
    return inv


def set_inventory(inventory: dict):
    db = get_db()
    blob = "\n".join(name + ":" + str(item) for name, item in inventory.items()
                     if name not in ("money", "experience"))
    db.execute("INSERT OR REPLACE INTO inventory (user_id, money, experience, blob) "
               "VALUES (?,?,?,?);",
               [session['user_id'],
                inventory['money'],
                inventory['experience'],
                blob])
    db.commit()


def get_timeouts(include_dead=False):
    return [TimeOut(x) for x in query_db('SELECT * FROM timeouts WHERE user_id = ? '
                                         'AND finished_date != 0' if not include_dead else '',
                                         [session['user_id']])]


def set_timeout_looted(timeout: TimeOut):
    db = get_db()
    db.execute("UPDATE timeouts SET finished_date = 0 WHERE timeout_id = ?;",
               [timeout.Timeout_id])
    db.commit()


def get_user(user: Union[str, int]):
    if type(user) == str:
        return query_db('SELECT * FROM user WHERE username = ?',
                        [user], one=True)
    else:
        return query_db('SELECT * FROM user WHERE user_id = ?',
                        [user], one=True)


def add_user(username, email, password):
    db = get_db()
    db.execute('''INSERT INTO user (
      username, email, pw_hash) VALUES (?, ?, ?)''',
               [username, email,
                generate_password_hash(email + password)])
    db.commit()


def get_tasklist():
    tasks = [Task(int(x["Time_Offset"]),
                  int(x["Time_Rand"]),
                  {l.split(":")[0]: int(l.split(":")[1]) for l in x["Rewards"].split("\n") if ":" in l} ,
                  str(x["Reward_Text"]),
                  {l.split(":")[0]: int(l.split(":")[1]) for l in x["Conditions"].split("\n") if ":" in l},
                  {l.split(":")[0]: int(l.split(":")[1]) for l in x["Costs"].split("\n") if ":" in l},
                  str(x["Menu_Entry"]),
                  str(x["Flash_Text"]),
                  {l.split(":")[0]: int(l.split(":")[1]) for l in x["Tags"].split("\n") if ":" in l},
                  )
             for x in query_db('SELECT * FROM Tasks')]
    return {x.Menu_Entry: x for x in tasks}


@app.before_request
def before_request():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)
    g.user = None
    if 'user_id' in session:
        g.user = query_db('SELECT * FROM user WHERE user_id = ?',
                          [session['user_id']], one=True)
