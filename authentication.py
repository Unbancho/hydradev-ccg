from flask import Blueprint, jsonify, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import User, db
from flask_bcrypt import Bcrypt
from response import Response

auth = Blueprint(name="auth", import_name=__name__, url_prefix="/auth")
login_manager = LoginManager()
bcrypt = Bcrypt()


def needs_auth_data(func):
    """
    Decorator function. Use this to decorate methods that require Username and Password form data.
    Returns 400 if requirements are not satisfied.
    """
    def _inner():
        if not (username := request.form.get("username")):
            return Response(message="No username provided."), 400
        if not (password := request.form.get("password")):
            return Response(message="No password provided."), 400
        return func(username, password)
    return _inner


@auth.post('/login', endpoint="login")
@needs_auth_data
def login(username: str, password: str) -> jsonify:
    user = User.query.filter_by(username=username).first()
    authenticated = user and bcrypt.check_password_hash(user.hash, password)    # NOTE: Hash check.
    if not authenticated:
        return Response(message="Authentication failed."), 401
    if login_user(load_user(user.id)):
        return Response(message=f"Logged in. Welcome, {user.real_name}"), 200
    return Response(message="Login failed!"), 401


@auth.post('/register', endpoint="register")
@needs_auth_data
def register(username: str, password: str) -> jsonify:
    if not (real_name := request.form.get("real_name")):
        return Response(message="No real name provided."), 400
    if User.query.filter_by(username=username).first():
        return Response(message=f"{username} is taken."), 400
    p_hash = bcrypt.generate_password_hash(password)    # NOTE: Hash the password.
    user = User(username=username, hash=p_hash, real_name=real_name)
    db.session.add(user)
    db.session.commit()
    return Response(message=f"Successfully registered."), 201


@auth.get("/logout")
@login_required
def logout() -> jsonify:
    return Response(logout_user()), 200


@auth.get("/current")
@login_required
def get_current_user() -> jsonify:
    return Response(current_user.jsonify()), 200


@login_manager.user_loader
def load_user(id) -> User:
    """
    utility function for Flask
    """
    return User.query.get(id)
