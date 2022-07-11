from crud import CRUD
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify, request
from authentication import has_access_to_data, bcrypt

Unauthorized = "Unauthorized."
NoWithID = "Doesn't exist."
NoAlterations = "No alterations"
NotProvided = "Not provided: "


class Decks(CRUD):

    def __init__(self):
        super().__init__("/decks", ["GET", "PUT", "POST", "DELETE"], db)

    def create(self, **kwargs) -> jsonify:
        data = request.json
        # TODO: Deck name validation.
        if not (n := data.get('name')):
            return Response(message=NotProvided+'name'), 400
        name = n
        cards = data.get('cards', [])
        # TODO: Validate cards.
        deck = Deck(name=name, cards=cards)
        if (id := kwargs.get('args').get('user')) and current_user.admin:
            user = User.query.get(int(id))
        else:
            user = current_user
        user.decks.append(deck)
        db.session.commit()
        return Response(data=deck.jsonify()), 201

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return self._get_one_deck(int(id)) if id else self._get_decks(kwargs.get('args'))

    @staticmethod
    def _get_decks(args) -> (bool, dict):
        if not args:
            return Response([d.jsonify() for d in current_user.decks]), 200
        decks = filter_model(Deck, args, True)
        return Response([d.jsonify() for d in decks]), 200

    @staticmethod
    def _get_one_deck(id: int) -> (bool, jsonify, str):
        if not (deck := Deck.query.get(id)):
            return Response(message=NoWithID)
        if not has_access_to_data(deck, True):
            return Response(message=Unauthorized)
        return Response(deck.jsonify()), 200

    def update(self, **kwargs) -> jsonify:
        data = request.json
        id = kwargs.get('id')
        if not id:
            return Response(message=NotProvided+'id'), 400
        if not (deck := Deck.query.get(int(id))):
            return Response(message=NoWithID), 404
        if not has_access_to_data(deck, True):
            return Response(message=Unauthorized), 401
        old = deck.jsonify()
        deck = CRUD._update_model(deck, data)
        db.session.commit()
        return Response(data=deck.jsonify(), message=None if deck.jsonify() != old else NoAlterations), 200

    def delete(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        if not id:
            return Response(message=NotProvided+'id'), 400
        if not (deck := Deck.query.get(int(id))):
            return Response(message=NoWithID), 404
        if not has_access_to_data(deck, True):
            return Response(message=Unauthorized), 401
        db.session.delete(deck)
        db.session.commit()
        return Response(message=f"Deleted {deck.name}"), 200


class Cards(CRUD):

    def __init__(self):
        super().__init__("/cards", ["GET", "PUT", "POST", "DELETE"], db)

    def create(self, **kwargs) -> jsonify:
        data = request.json
        if not (name := data.get('name')):
            return Response(message=NotProvided+'name'), 400
        if not (power := data.get('power')):
            return Response(message=NotProvided+'power'), 400
        desc = data.get('description', '')  # Some cards might just be Beatsticks.
        card = Card(power=power, name=name, description=desc)
        if (id := kwargs.get('args').get('user')) and current_user.admin:
            user = User.query.get(int(id))
        else:
            user = current_user
        user.cards.append(card)
        db.session.commit()
        return Response(card.jsonify()), 201

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return self._get_one_card(int(id)) if id else self._get_cards(kwargs.get('args'))  # id overrides query

    @staticmethod
    def _get_cards(args) -> (bool, dict):
        if not args:
            return Response([c.jsonify() for c in current_user.cards]), 200
        cards = filter_model(Card, args, True)
        return Response([c.jsonify() for c in cards]), 200

    @staticmethod
    def _get_one_card(id: int) -> (bool, jsonify, str):
        if not (card := Card.query.get(id)):
            return Response(message=NoWithID), 404
        if not has_access_to_data(card, True):
            return Response(message=Unauthorized), 401
        return Response(card.jsonify()), 200

    def update(self, **kwargs) -> jsonify:
        data = request.json
        id = kwargs.get('id')
        if not (card := Card.query.get(int(id))):
            return Response(message=NoWithID), 404
        if not has_access_to_data(card, True):
            return Response(message=Unauthorized), 401
        old = card
        card = CRUD._update_model(card, data)
        db.session.commit()
        return Response(data=card.jsonify(), message=None if old != card else NoAlterations), 200

    def delete(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        if not (card := Card.query.get(int(id))):
            return Response(message=NoWithID), 404
        if not has_access_to_data(card, True):
            return Response(message=Unauthorized), 401
        db.session.delete(card)
        db.session.commit()
        return Response(message=f"Deleted {card.name}"), 200


def filter_model(model, filters, admin_override=False):
    filters = dict(filters)
    if admin_override and current_user.admin and (user := filters.pop('user', None)):
        user = User.query.get(int(user))
        result = model.query.filter(model.user == user)
    else:
        result = model.query.filter(model.user == current_user)
    for f in filters:
        if hasattr(model, f):
            result = result.filter(getattr(model, f).contains(filters[f]))
    return result.all()


# TODO: Admin functionality.
class Users(CRUD):

    def __init__(self):
        super().__init__("/users", ["GET", "PUT", "POST", "DELETE"], db)

    @staticmethod
    def needs_admin(func):
        def _inner(self, id: int = None, **kwargs):
            if not current_user.admin:
                return Response(message="Permission Denied."), 401
            return func(self, **({'id': id} | kwargs))

        return _inner

    @needs_admin
    def create(self, **kwargs) -> jsonify:
        data = request.json
        if not (username := data.get(key := "username")):
            return Response(message=NotProvided+key), 400
        if not (password := data.get(key := "password")):
            return Response(message=NotProvided+key), 400
        if not (real_name := data.get(key := "real_name")):
            return Response(message=NotProvided+key), 400
        if User.query.filter_by(username=username).first():
            return Response(message=f"{username} is taken."), 400
        p_hash = bcrypt.generate_password_hash(password)  # TODO: check.
        user = User(username=username, hash=p_hash, real_name=real_name, admin=data.get('admin', False))
        db.session.add(user)
        db.session.commit()
        return Response(user.jsonify()), 201

    @needs_admin
    def read(self, id: int = None, **kwargs) -> jsonify:
        return self._get_one_user(int(id)) if id else self._get_users(kwargs.get('args'))  # id overrides query

    @staticmethod
    def _get_one_user(id: int):
        if not (user := User.query.get(id)):
            return Response(message=NoWithID), 404
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
    def update(self, id: int, **kwargs) -> jsonify:
        data = request.json
        if not (user := User.query.get(int(id))):
            return Response(message=NoWithID), 404
        old = user.jsonify()
        user = CRUD._update_model(user, data)
        db.session.commit()
        return Response(data=user.jsonify(), message=None if old != user.jsonify() else NoAlterations), 200

    @needs_admin
    def delete(self, id: int, **kwargs) -> jsonify:
        if not (user := User.query.get(int(id))):
            return Response(message=NoWithID), 404
        db.session.delete(user)
        db.session.commit()
        return Response(message=f"Deleted {user.username}"), 200

