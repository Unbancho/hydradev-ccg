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


class UserAdminView(ModelView):
    form_edit_rules = ('username', 'decks', 'cards', 'admin')


# TODO: Finish.
admin = Admin()
admin.add_view(UserAdminView(User, db.session))
admin.add_view(ModelView(Deck, db.session))
admin.add_view(ModelView(Card, db.session))


@auth.route('/login', methods=['POST'])
def login() -> jsonify:
    login_data = request.form
    username = login_data.get("username")
    if not username:
        return Response(message="No username provided.")
    password = login_data.get("password")
    if not password:
        return Response(message="No password provided")
    user = User.query.filter_by(username=username).first()
    authenticated = user and bcrypt.check_password_hash(user.hash, password)
    if not authenticated:
        return Response(message="Authentication failed.")
    return Response(login_user(load_user(user.id)))


@auth.route('/register', methods=['POST'])
def register() -> jsonify:
    register_data = request.form
    if not (username := register_data.get("username")):
        return Response(message="No username provided.")
    if not (password := register_data.get("password")):
        return Response(message="No password provided.")
    if not (real_name := register_data.get("real_name")):
        return Response(message="No real name provided.")
    if User.query.filter_by(username=username).first():
        return Response(message="That username is taken.")
    p_hash = bcrypt.generate_password_hash(password)
    user = User(username=username, hash=p_hash, real_name=real_name)
    db.session.add(user)
    db.session.commit()
    return Response(True)


@auth.route("/logout")
@login_required
def logout() -> jsonify:
    return Response(logout_user())


@auth.route("/current")
@login_required
def get_current_user() -> jsonify:
    return Response(True, current_user.jsonify())


@login_manager.user_loader
def load_user(id) -> User:
    return User.query.get(id)


def has_access_to_data(data, admin_override=False) -> bool:
    return data.user == current_user or admin_override and current_user == admin_override
