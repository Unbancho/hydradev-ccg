from flask import Flask
from models import db
from authentication import auth, login_manager, admin
from crud import CRUD
from crud_handling import Decks, Cards, Users
from werkzeug.exceptions import NotFound, BadRequest, Forbidden, Unauthorized
from response import Response

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'GWENT'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return Response(message="do cool spa frontend things")


def build_crud_routes(crud: CRUD, _app: Flask):
    """
    Maps all the CRUD routes to the CRUD routers.
    """
    app.add_url_rule(crud.prefix, endpoint=crud.prefix, view_func=crud.router, methods=crud.methods)
    app.add_url_rule(crud.prefix + '/<id>', endpoint=crud.prefix+'/<id>', view_func=crud.router, methods=crud.methods)


@app.errorhandler(NotFound)
def handle_notfound(e):
    return Response(message="Not found."), 404


@app.errorhandler(BadRequest)
def handle_badrequest(e):
    return Response(message="Bad request."), 400


@app.errorhandler(Forbidden)
def handle_forbidden(e):
    return Response(message="Access forbidden."), 403


@app.errorhandler(Unauthorized)
def handle_unauthorized(e):
    return Response(message="Unauthorized."), 401


if __name__ == "__main__":
    app.register_blueprint(auth)
    db.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)
    build_crud_routes(Decks(), app)
    build_crud_routes(Cards(), app)
    build_crud_routes(Users(), app)
    app.run(debug=True, ssl_context="adhoc")
