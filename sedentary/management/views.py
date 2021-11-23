# -*- coding: utf-8 -*-
"""
    Sedentary
    ~~~~~~~~

    A possible Broswergame in early development

    :license: GNU GPL3, see LICENSE for more details.
"""
import random
import time
from datetime import datetime

from flask import (
    request,
    session,
    url_for,
    redirect,
    render_template,
    g,
    flash,
    Blueprint,
)
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash


from sedentary.serverside import TimeOut


views = Blueprint("views", __name__, template_folder="templates")


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d @ %H:%M")


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = generate_password_hash(
            str(session) + str(time.clock()) + str(random.random())
        )
    return session["_csrf_token"]


@views.route("/status")
@login_required
def status():
    current_user.data["test"] = "gnarg"
    return render_template("statuspage.html")


@views.route("/")
def homepage():
    return render_template("homepage.html", stats="", work="")


@views.route("/welcome")
def welcome():
    print(current_user)
    return render_template("welcome.html")


@views.route("/<username>")
def user_stats(username):
    """Display's a users stats."""
    profile_user = {"no": "val"}

    return render_template("homepage.html", stats=profile_user)


def loot(timeout: TimeOut):
    rewards = timeout.Rewards
    inventory = get_inventory()

    for k in rewards.keys():
        inventory[k] = str(int(rewards[k]) + int(inventory.get(k, "0")))
    set_inventory(inventory)
    set_timeout_looted(timeout)


def taskrun(starttask_result):
    resultcode = starttask_result[0]
    timeout = starttask_result[1]
    context_a = starttask_result[2]
    context_b = starttask_result[3]
    if resultcode == 0:
        flash(context_a)
        set_inventory(context_b)
        add_timeout(timeout)
    elif resultcode == 1:
        flash(
            "Unable to Pay: \n"
            + "\n".join([x + ":" + str(context_a[x]) for x in context_a.keys()])
        )
    elif resultcode == 2:
        flash(
            "Conditions not Met: \n"
            + "\n".join([x + ":" + str(context_b[x]) for x in context_b.keys()])
        )


@views.route("/work")
def work():
    """gets a users work results. or sets them to work"""
    if session.get("user_id", None) is None:
        return redirect(url_for("views.login"))
    collected = 0
    timeouts = get_timeouts()
    for timeout in timeouts:
        print(timeout.to_db())
        if int(time.time()) > timeout.FinishedDate:
            flash("you earned:\n" + str(timeout))
            loot(timeout)
            collected += 1
    if collected:
        return redirect(url_for("homepage"))

    flash("nothing to collect!")
    return redirect(url_for("homepage"))


@views.route("/startwork/<x>")
def startwork(x: str):
    inventory = get_inventory()
    tasklist = get_tasklist()
    if x in tasklist.keys():
        taskrun(tasklist[x].starttask(inventory, session["user_id"]))
    if x == "labour":
        add_timeout(
            TimeOut(
                "labour",
                int(time.time()) + random.randint(90, 300),
                {"money": 10, "experience": 1},
                "{money} Gold and {experience} XP",
                session["user_id"],
            )
        )
        flash("Started labour!")
    if x == "woodcutting":
        if inventory.get("woodaxe", 0) > 0:
            add_timeout(
                TimeOut(
                    x,
                    int(time.time()) + random.randint(90, 300),
                    {"wood": 10, "experience": 1},
                    "{wood} wood and {experience} XP using 1 woodaxe",
                    session["user_id"],
                )
            )
            inventory["woodaxe"] -= 1
            flash("Started chopping wood!")
        else:
            add_timeout(
                TimeOut(
                    x,
                    int(time.time()) + random.randint(150, 360),
                    {"wood": 1, "experience": 1},
                    "{wood} wood and {experience} XP using your bare hands",
                    session["user_id"],
                )
            )
            flash("Started gathering wood by hand!")
    if x == "mining":
        if inventory.get("pickxe", 0) > 0:
            add_timeout(
                TimeOut(
                    x,
                    int(time.time()) + random.randint(90, 300),
                    {"iron": 10, "experience": 1},
                    "{iron} iron and {experience} XP using 1 pickaxe",
                    session["user_id"],
                )
            )
            inventory["pickaxe"] -= 1
            flash("Started mining!")
        else:
            add_timeout(
                TimeOut(
                    x,
                    int(time.time()) + random.randint(150, 360),
                    {"iron": 10, "experience": 1},
                    "{iron} iron and {experience} XP using 1 pickaxe",
                    session["user_id"],
                )
            )
            flash("Started collecting red stones from the ground!")
    if x == "buy_woodaxe_1":
        if inventory["money"] >= 100:
            inventory["money"] -= 100
            add_timeout(
                TimeOut(
                    x,
                    time.time() + 5,
                    {"woodaxe": 1},
                    "{woodaxe} woodaxe for 100 gold",
                    session["user_id"],
                )
            )
    set_inventory(inventory)
    return redirect(url_for("homepage"))


@views.route("/register", methods=["GET", "POST"])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for("homepage"))
    error = None
    if request.method == "POST":
        if not request.form["username"]:
            error = "You have to enter a username"
        elif not request.form["email"] or "@" not in request.form["email"]:
            error = "You have to enter a valid email address"
        elif not request.form["password"]:
            error = "You have to enter a password"
        elif request.form["password"] != request.form["password2"]:
            error = "The two passwords do not match"
        elif get_user_id(request.form["username"]) is not None:
            error = "The username is already taken"
        else:
            add_user(
                request.form["username"],
                request.form["email"],
                request.form["password"],
            )
            flash("You were successfully registered and can login now")
            return redirect(url_for("login"))
    return render_template("register.html", error=error)


@views.route("/logout")
def logout():
    """Logs the user out."""
    flash("You were logged out")
    session.pop("user_id", None)
    return redirect(url_for("welcome"))


# add some values to jinja
