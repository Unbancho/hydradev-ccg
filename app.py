from flask import Flask, render_template
from models import User, db
from forms import SignUpForm
from authentication import auth, login_manager
from deck_management import decks

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# TODO: Make it actually secretive.
app.config['SECRET_KEY'] = 'GWENT'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    db.create_all()
    return render_template('index.html')


if __name__ == "__main__":
    app.register_blueprint(auth)
    app.register_blueprint(decks)
    db.init_app(app)
    login_manager.init_app(app)
    app.run(debug=True)
