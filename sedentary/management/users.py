import flask
from flask import Blueprint, request, session
from flask_login import login_required, current_user, logout_user, login_user

from sedentary.management.Forms import LoginForm

from is_safe_url import is_safe_url

from sedentary.management.User import User
from sedentary.management.Logging import Debug

users = Blueprint("users", __name__, template_folder="templates")


@users.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u = form.username
        p = form.password
        Debug.log(10, "login attempt", u)
        user = User(u.data).login(p.data)
        if user.is_authenticated:
            flask.flash(f"Logged in {user.name} successfully.")
            login_user(user)
        else:
            flask.flash(f"Failure to log in")

        next_page = session.get("next")
        if next_page and not is_safe_url(next_page, request.host_url):
            return flask.abort(400)

        return flask.redirect(next_page or flask.url_for("views.welcome"))
    return flask.render_template("login.html", form=form)


@login_required
@users.route("/test")
def test():
    print(current_user.id + " visited test!")
    return "Ok"


@users.route("/register")
def register():
    u = User("xx")
    u.register("asd")
    return "ok"


@login_required
@users.route("/logout")
def logout():
    logout_user()


@users.record_once
def on_load(state):
    """
    http://stackoverflow.com/a/20172064/742173

    :param state: state
    """
    state.app.login_manager.blueprint_login_views[users.name] = 'users.login'
