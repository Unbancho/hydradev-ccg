from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager
from models import User

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # TODO: Create SPA endpoint.
    return app.send_static_file()

@app.route('/login', methods=['GET', 'POST'])
def login() -> jsonify:
    login_data = request.json
    username = login_data.get("username")
    # TODO: Hash and salt.
    password = login_data.get("password")
    # TODO: Authenticate.
    return jsonify({"login": AUTH_SUCCESS})

# TODO: Instantiate user.
@login_manager.user_loader
def load_user(user) -> User:
    return User()
    

if __name__ == "__main__":
    app.run(debug=True)