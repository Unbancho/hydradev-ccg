from flask import Blueprint, jsonify, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import User, Deck, Card, db
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from response import Response

auth = Blueprint(name="auth", import_name=__name__, url_prefix="/auth", template_folder='templates')

login_manager = LoginManager()

bcrypt = Bcrypt()


class ProtectedView(ModelView):
    def is_accessible(self):
        return current_user.admin and current_user.is_authenticated


class UserAdminView(ProtectedView):
    form_edit_rules = ('username', 'decks', 'cards', 'admin')
    column_list = {'username', 'real_name', 'decks', 'cards', 'admin'}


admin = Admin()
admin.add_view(UserAdminView(User, db.session))
admin.add_view(ProtectedView(Deck, db.session))
admin.add_view(ProtectedView(Card, db.session))


def needs_auth_data(func):
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
    authenticated = user and bcrypt.check_password_hash(user.hash, password)
    if not authenticated:
        return Response(message="Authentication failed."), 401
    if login_user(load_user(user.id)):
        return Response(message=f"Logged in. Welcome, {user.real_name}"), 200
    return Response(message="Login failed!"), 401


@auth.post('/register', endpoint="register")
@needs_auth_data
def register(username: str, password: str) -> jsonify:
    register_data = request.form
    if not (real_name := register_data.get("real_name")):
        return Response(message="No real name provided."), 400
    if User.query.filter_by(username=username).first():
        return Response(message=f"{username} is taken."), 400
    p_hash = bcrypt.generate_password_hash(password)
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
    return User.query.get(id)


def has_access_to_data(data, admin_override=False) -> bool:
    return data.user == current_user or admin_override and current_user == admin_override
