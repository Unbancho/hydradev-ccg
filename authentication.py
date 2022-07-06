from flask import Blueprint, jsonify, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import User, Deck, Card, db
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

auth = Blueprint(name="auth", import_name=__name__, url_prefix="/auth", template_folder='templates')

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

bcrypt = Bcrypt()

# TODO: Finish.
admin = Admin()
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Deck, db.session))
admin.add_view(ModelView(Card, db.session))

@auth.route('/login', methods=['POST'])
def login() -> jsonify:
    login_data = request.form
    username = login_data.get("username")
    password = login_data.get("password")
    user = User.query.filter_by(username=username).first()
    authenticated = user and bcrypt.check_password_hash(user.hash, password)
    if(authenticated):
        login_user(load_user(user.id))
    return {"login": authenticated}

@auth.route('/register', methods=['POST'])
def register() -> jsonify:
    register_data = request.form
    hash = bcrypt.generate_password_hash(register_data.get("password"))
    username = register_data.get("username")
    # TODO: Fix me.
    if User.query.filter_by(username=username).first():
        return {"register": False}
    user = User(username=username, hash=hash, real_name=register_data.get("real_name"))
    db.session.add(user)
    db.session.commit()
    return {"register": True}

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return {"logout": True}

@auth.route("/current")
@login_required
def get_current_user():
    return {"Username": current_user.username, "Real Name": current_user.real_name}


@login_manager.user_loader
def load_user(id) -> User:
    try:
        return User.query.get(id)
    except:
        return None