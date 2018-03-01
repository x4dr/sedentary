# -*- coding: utf-8 -*-
"""
    Sedentary
    ~~~~~~~~

    A possible Broswergame in early development

    :license: GNU GPL3, see LICENSE for more details.
"""
import random
import time
from sqlite3 import dbapi2 as sqlite3
from sedentary.serverside.TimeOut import TimeOut
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
    render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash

# configuration
DATABASE = './sedentary/sedentary.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'

# create our little application :)
app = Flask('sedentary')
app.config.from_object(__name__)
app.config.from_envvar('SEDENTARY_SETTINGS', silent=True)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


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


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_password_hash(str(session) + str(time.clock()))
    return session['_csrf_token']


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


@app.route('/')
def homepage():
    """Shows a users homepage or if the user is not logged in it will
    redirect to the public welcome page. This homepage serves as the
    central navigational hub for logged in users.
    """
    if not g.user:
        return redirect(url_for('welcome'))
    inventory = query_db('SELECT * FROM inventory WHERE user_id = ?',
                         [session['user_id']], one=True)
    timeout = query_db('SELECT * FROM timeouts WHERE user_id = ? AND finished_date != 0',
                       [session['user_id']])
    
    return render_template('homepage.html', stats=inventory, work=timeout)


@app.route('/welcome')
def welcome():
    """Displays a welcome page for not logged in vistors."""
    return render_template('welcome.html')


@app.route('/<username>')
def user_stats(username):
    """Display's a users stats."""
    profile_user = query_db('SELECT * FROM user WHERE username = ?',
                            [username], one=True)

    return render_template('homepage.html')


def loot(rewards):
    db = get_db()
    inventory = query_db("SELECT * FROM inventory WHERE user_id = ?",
                         [session['user_id']], one=True)
    inventory = dict(inventory) if inventory else {}
    
    inventory = {"money": inventory.get('money', 0),
                 "experience": inventory.get('experience', 0),
                 "blob": inventory.get('blob', "")}
    inventory['money'] = str(int(inventory['money']) + int(rewards.get("money", 0)))
    inventory['experience'] = str(int(inventory['experience']) + int(rewards.get("experience", 0)))
    
    blob = {l.split(":")[0]: l.split(":")[1] for l in inventory['blob'].split("\n")}
    for k in rewards.keys():
        blob[k] = str(int(rewards[k]) + int(blob.get(k, "0")))
    inventory['blob'] = "\n".join([b + ":" + blob[b] for b in blob.keys()])
    db.execute("INSERT OR REPLACE INTO inventory (user_id, money, experience, blob) "
               "VALUES (?,?,?,?);",
               [session['user_id'],
                inventory['money'],
                inventory['experience'],
                inventory['blob']])


@app.route('/work')
def work():
    """gets a users work results. or sets them to work"""
    timeouts = query_db('SELECT * FROM timeouts WHERE user_id = ? AND finished_date != 0',
                        [session['user_id']])
    db = get_db()
    for timeout in timeouts:
        
        timeout = TimeOut(timeout)
        
        if int(time.time()) > timeout.FinishedDate > 0:  # 0 means finished
            if "work" in timeout.Type:
                flash("you earned:\n" + str(timeout))
                loot(timeout.Rewards)
                db.execute("UPDATE timeouts SET finished_date = 0 WHERE timeout_id = ?;",
                           [timeout.Timeout_id])
                db.commit()
                return redirect(url_for('homepage'))
    if len(timeouts) > 1:
        flash("working more than two jobs? really?")
        return redirect(url_for('homepage'))
    write = TimeOut("work_example", int(time.time()) + random.randint(90, 300), {"money": 10, "experience": 1},
                    "{money} Gold and {experience} XP", session["user_id"]).to_db()
    db.execute("INSERT INTO timeouts (user_id, type, blob, finished_date) VALUES (?,?,?,?);",
               [write[0]] + write[2:])
    db.commit()
    flash("started working")
    return redirect(url_for("homepage"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('homepage'))
    error = None
    
    if request.method == 'POST':
        user = query_db('''SELECT * FROM user WHERE
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],
                                     user['email']+request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('homepage'))
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('homepage'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            db = get_db()
            db.execute('''INSERT INTO user (
              username, email, pw_hash) VALUES (?, ?, ?)''',
                       [request.form['username'], request.form['email'],
                        generate_password_hash(request.form['email']+request.form['password'])])
            db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('welcome'))


# add some values to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.globals['csrf_token'] = generate_csrf_token
