from flask import Flask, render_template
from models import User, Deck, Card, db
from authentication import auth, login_manager, admin
from deck_management import decks

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'GWENT'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


if __name__ == "__main__":
    app.register_blueprint(auth)
    app.register_blueprint(decks)
    db.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)

    app.run(debug=True)
