from crud import CRUD
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify
from authentication import has_access_to_data


class Decks(CRUD):

    def create(self, data=None, **kwargs) -> jsonify:
        # TODO: Deck name validation.
        if not (n := data.get('name')):
            return Response(message="Invalid deck name.")
        name = n
        cards = data.get('cards', [])
        # TODO: Validate cards.
        deck = Deck(name=name, cards=cards)
        current_user.decks.append(deck)
        db.session.commit()
        return Response(status=True)

    # TODO: Filtering by name.
    def read(self, id: int = None, **kwargs) -> jsonify:
        if not id:
            decks = current_user.decks
            return Response(True, dict(enumerate([d.jsonify() for d in decks])))
        if not (deck := Deck.query.get(int(id))):
            return Response(message=f"No deck with ID {id}")
        if not has_access_to_data(deck, True):
            return Response(True, deck.jsonify())
        return Response(message="Unauthorized.")

    def update(self, id: int, **kwargs) -> jsonify:
        pass

    def delete(self, id: int, **kwargs) -> jsonify:
        if not id:
            return Response(message="No ID provided.")
        if not (deck := Deck.query.get(int(id))):
            return Response(message=f"No deck with ID {id}")
        if not has_access_to_data(deck, True):
            return Response(message="Unauthorized")
        db.session.delete(deck)
        db.session.commit()
        return Response(True)


class Cards(CRUD):

    def create(self, data=None, **kwargs) -> jsonify:
        if not (name := data.get('name')):
            return Response(message="No name provided")
        if not (power := data.get('power')):
            return Response(message="No power provided")
        desc = data.get('description', '')  # Some cards might just be Beatsticks.
        card = Card(power=power, name=name, description=desc)
        current_user.cards.append(card)
        db.session.commit()
        return Response(True)

    def read(self, id: int = None, **kwargs) -> jsonify:
        if id:
            if not (card := Card.query.get(id)):
                return Response(message=f"No card with ID {id}")
            if not has_access_to_data(card, True):
                return Response(message="Unauthorized.")
            return Response(True, card.jsonify())
        if substring := kwargs.get('substring'):
            # TODO: Figure out how to filter directly from user.
            cards = ((Card.query.filter(Card.user == current_user)).filter(Card.name.contains(substring))).all()
        else:
            cards = current_user.cards
        return Response(True, dict(enumerate([c.jsonify() for c in cards])))

    def update(self, id: int, data=None, **kwargs) -> jsonify:
        pass

    def delete(self, id: int, **kwargs) -> jsonify:
        if not (card := Card.query.get(int(id))):
            return Response(message=f"No card with ID {id}")
        if not has_access_to_data(card, True):
            return Response(message="Unauthorized.")
        db.session.delete(card)
        db.session.commit()
        return {"card_deleted": True, "card": card.jsonify()}

class Users(CRUD):
    pass
