from crud import CRUD, try_int
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify, request, abort
from authentication import has_access_to_data, bcrypt

NoAlterations = "No alterations"


class Decks(CRUD):

    def __init__(self):
        super().__init__("/decks", ["GET", "PUT", "POST", "DELETE"], db, Deck)

    @CRUD.needs_data('name')
    def create(self, **kwargs) -> jsonify:
        if id := kwargs.get('id'):
            return self.add_card(**kwargs)
        data = kwargs['data']
        name = data['name']
        cards = data.get('cards', [])
        deck = Deck(name=name, cards=cards)
        user = User.query.get(try_int(id)) if (id := kwargs.get('user')) and current_user.admin else current_user
        user.decks.append(deck)
        db.session.commit()
        return Response(data=deck.jsonify()), 201

    @CRUD.needs_data('name', 'power')
    @CRUD.gets_by_id(needs_permission=True)
    def add_card(self, **kwargs):
        deck = kwargs.pop('model')
        card = Cards.create_card(kwargs['data'], deck.user)
        deck.cards.append(card)
        db.session.commit()
        return Response(data=card.jsonify()), 201

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return self.read_one(id=try_int(id)) if id else self._get_decks(kwargs.get('args'))

    @staticmethod
    def _get_decks(args) -> (bool, dict):
        if not args:
            return Response([d.jsonify() for d in current_user.decks]), 200
        decks = filter_model(Deck, args, True)
        return Response([d.jsonify() for d in decks]), 200

    @CRUD.gets_by_id(needs_permission=True)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        deck = kwargs['model']
        old = deck.jsonify()
        deck = CRUD._update_model(deck, data)
        db.session.commit()
        return Response(data=deck.jsonify(), message=None if deck.jsonify() != old else NoAlterations), 200

    @CRUD.gets_by_id(needs_permission=True)
    def delete(self, **kwargs) -> jsonify:
        deck = kwargs['model']
        db.session.delete(deck)
        db.session.commit()
        return Response(message=f"Deleted {deck.name}"), 200


class Cards(CRUD):

    def __init__(self):
        super().__init__("/cards", ["GET", "PUT", "POST", "DELETE"], db, Card)

    @CRUD.needs_data('name', 'power')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        user = User.query.get(try_int(id)) if (id := kwargs.get('user')) and current_user.admin else current_user
        card = Cards.create_card(data, user)
        db.session.commit()
        return Response(card.jsonify()), 201

    @staticmethod
    def create_card(data: dict, user: User) -> Card:
        desc = data.get('description', '')  # Some cards might just be Beatsticks.
        card = Card(power=try_int(data['power']), name=data['name'], description=desc)
        user.cards.append(card)
        return card

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return self.read_one(id=try_int(id)) if id else self._get_cards(kwargs.get('args'))  # id overrides query

    @staticmethod
    def _get_cards(args) -> (bool, dict):
        if not args:
            return Response([c.jsonify() for c in current_user.cards]), 200
        cards = filter_model(Card, args, True)
        return Response([c.jsonify() for c in cards]), 200

    # TODO: Fix adding to deck that doesn't exist.
    @CRUD.gets_by_id(needs_permission=True)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        card = kwargs['model']
        # TODO: Fix.
        if deck_id := data.get('deck_id'):
            if not (deck := Deck.query.get(try_int(deck_id))) or not has_access_to_data(deck, True):
                return Response(message=NoWithID), 404
        old = card.jsonify()
        card = CRUD._update_model(card, data)
        db.session.commit()
        return Response(data=card.jsonify(), message=None if old != card.jsonify() else NoAlterations), 200

    @CRUD.gets_by_id(needs_permission=True)
    def delete(self, **kwargs) -> jsonify:
        card = kwargs['model']
        db.session.delete(card)
        db.session.commit()
        return Response(message=f"Deleted {card.name}"), 200


def filter_model(model, filters, admin_override=False):
    filters = dict(filters)
    if admin_override and current_user.admin and (user := filters.pop('user', None)):
        user = User.query.get(try_int(user))
        result = model.query.filter(model.user == user)
    else:
        result = model.query.filter(model.user == current_user)
    for f in filters:
        if hasattr(model, f):
            result = result.filter(getattr(model, f).contains(filters[f]))
    return result.all()


class Users(CRUD):

    def __init__(self):
        super().__init__("/users", ["GET", "PUT", "POST", "DELETE"], db, User)

    @staticmethod
    def needs_admin(func):
        def _inner(self, id: int = None, **kwargs):
            if not current_user.admin:
                return Response(message="Permission Denied."), 403
            return func(self, **({'id': id} | kwargs))
        return _inner

    @needs_admin
    @CRUD.needs_data('username', 'password', 'real_name')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        username = data['username']
        password = data['password']
        real_name = data['real_name']
        if User.query.filter_by(username=username).first():
            return Response(message=f"{username} is taken."), 400
        p_hash = bcrypt.generate_password_hash(password)
        user = User(username=username, hash=p_hash, real_name=real_name, admin=data.get('admin', False))
        db.session.add(user)
        db.session.commit()
        return Response(user.jsonify()), 201

    @needs_admin
    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return self.read_one(id=try_int(id)) if id else self._get_users(kwargs.get('args'))  # id overrides query

    @CRUD.gets_by_id(needs_permission=False)
    def read_one(self, **kwargs):
        user = kwargs['model']
        return Response(user.jsonify()), 200

    @staticmethod
    def _get_users(args):
        if not args:
            return Response([u.jsonify() for u in User.query.all()]), 200
        result = User.query
        for f in (filters := dict(args)):
            if hasattr(User, f):
                result = result.filter(getattr(User, f).contains(filters[f]))
        if result == User.query:
            result = {}
        return Response([u.jsonify() for u in result.all()]), 200

    @needs_admin
    @CRUD.gets_by_id(needs_permission=False)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        user = kwargs['model']
        old = user.jsonify()
        if password := data.get("password"):
            user.hash = bcrypt.generate_password_hash(password)
        user = CRUD._update_model(user, data)
        db.session.commit()
        return Response(data=user.jsonify(), message=None if old != user.jsonify() else NoAlterations), 200

    @needs_admin
    @CRUD.gets_by_id(needs_permission=False)
    def delete(self, **kwargs) -> jsonify:
        user = kwargs['model']
        if user == current_user:
            return Response(message="Can't auto-delete."), 403
        db.session.delete(user)
        db.session.commit()
        return Response(message=f"Deleted {user.username}"), 200


