from crud import CRUD
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify, request
from authentication import has_access_to_data
from flask_sqlalchemy import SQLAlchemy

Unauthorized = "Unauthorized."
NoWithID = "Doesn't exist."
NoAlterations = "No alterations"


class Decks(CRUD):

    def __init__(self):
        super().__init__("/decks", ["GET", "PUT", "POST", "DELETE"], db)

    def create(self, **kwargs) -> jsonify:
        # TODO: Deck name validation.
        data = request.json
        if not (n := data.get('name')):
            return Response(message="Invalid deck name.")
        name = n
        cards = data.get('cards', [])
        # TODO: Validate cards.
        deck = Deck(name=name, cards=cards)
        current_user.decks.append(deck)
        db.session.commit()
        return Response(status=True)

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        return Response(*self._get_one_deck(int(id))) if id else Response(*self._get_decks(kwargs.get('filter')))

    # TODO: Filtering (by name).
    @staticmethod
    def _get_decks(filter) -> (bool, dict):
        return True, dict(enumerate([d.jsonify() for d in current_user.decks]))

    def _get_one_deck(self, id: int) -> (bool, jsonify, str):
        if not (deck := Deck.query.get(id)):
            return False, None, NoWithID
        if not has_access_to_data(deck, True):
            return False, None, Unauthorized
        return True, deck.jsonify()

    def update(self, **kwargs) -> jsonify:
        data = request.json
        id = kwargs.get('id')
        if not id:
            return Response(message="No ID provided.")
        if not (deck := Deck.query.get(int(id))):
            return Response(message=NoWithID)
        if not has_access_to_data(deck, True):
            return Response(message=Unauthorized)
        deck, diff = CRUD._update_model(deck, data)
        if diff:
            db.session.commit()
        return Response(diff, data=deck, message=None if diff else NoAlterations)

    def delete(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        if not id:
            return Response(message="No ID provided.")
        if not (deck := Deck.query.get(int(id))):
            return Response(message=NoWithID)
        if not has_access_to_data(deck, True):
            return Response(message=Unauthorized)
        db.session.delete(deck)
        db.session.commit()
        return Response(True)


class Cards(CRUD):

    def __init__(self):
        super().__init__("/cards", ["GET", "PUT", "POST", "DELETE"], db)

    def create(self, **kwargs) -> jsonify:
        data = request.json
        if not (name := data.get('name')):
            return Response(message="No name provided")
        if not (power := data.get('power')):
            return Response(message="No power provided")
        desc = data.get('description', '')  # Some cards might just be Beatsticks.
        card = Card(power=power, name=name, description=desc)
        current_user.cards.append(card)
        db.session.commit()
        return Response(True)

    def read(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        if id:
            if not (card := Card.query.get(int(id))):
                return Response(message=NoWithID)
            if not has_access_to_data(card, True):
                return Response(message=Unauthorized)
            return Response(True, card.jsonify())
        if substring := kwargs.get('substring'):
            # TODO: Figure out how to filter directly from user.
            cards = ((Card.query.filter(Card.user == current_user)).filter(Card.name.contains(substring))).all()
        else:
            cards = current_user.cards
        return Response(True, dict(enumerate([c.jsonify() for c in cards])))

    def update(self, **kwargs) -> jsonify:
        data = request.json
        id = kwargs.get('id')
        if not (card := Card.query.get(int(id))):
            return Response(message=NoWithID)
        if not has_access_to_data(card, True):
            return Response(message=Unauthorized)
        card, diff = CRUD._update_model(card, data)
        if diff:
            db.session.commit()
        return Response(diff, data=card.jsonify(), message=None if diff else NoAlterations)

    def delete(self, **kwargs) -> jsonify:
        id = kwargs.get('id')
        if not (card := Card.query.get(int(id))):
            return Response(message=NoWithID)
        if not has_access_to_data(card, True):
            return Response(message=Unauthorized)
        db.session.delete(card)
        db.session.commit()
        return Response(True)


class Users(CRUD):
    pass
