from flask import Flask, render_template
from models import db
from authentication import auth, login_manager, admin
from crud import CRUD
from deck_crud import Decks, Cards

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'GWENT'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')


def build_crud_routes(crud: CRUD, _app: Flask):
    app.add_url_rule(crud.prefix, endpoint=crud.prefix, view_func=crud.manager, methods=crud.methods)
    app.add_url_rule(crud.prefix+'/<id>', endpoint=crud.prefix+'/<id>', view_func=crud.manager, methods=crud.methods)


if __name__ == "__main__":
    app.register_blueprint(auth)
    db.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)

    build_crud_routes(Decks(), app)
    build_crud_routes(Cards(), app)

    app.run(debug=True)  # TODO: , ssl_context="adhoc")
