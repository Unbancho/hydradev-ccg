from crud import CRUD
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify, request
from authentication import has_access_to_data

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
        current_user.decks.append(deck)
        db.session.commit()
        return Response(data=deck.jsonify()), 201

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return self._get_one_deck(int(id)), 200 if id else self._get_decks(kwargs.get('args')), 200

    @staticmethod
    def _get_decks(args) -> (bool, dict):
        if not args:
            return Response([d.jsonify() for d in current_user.decks]), 200
        decks = filter_model(Deck, args, True)
        return Response([d.jsonify() for d in decks]), 200

    @staticmethod
    def _get_one_deck(self, id: int) -> (bool, jsonify, str):
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
        old = deck
        deck = CRUD._update_model(deck, data)
        db.session.commit()
        return Response(data=deck, message=None if deck != old else NoAlterations), 200

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
        current_user.cards.append(card)
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
    if admin_override and current_user.admin and (user := filters.pop('user')):
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
    pass
