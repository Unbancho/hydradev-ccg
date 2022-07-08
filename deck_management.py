from crypt import methods
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Deck, Card, db
from response import Response

ccg = Blueprint(name="decks", import_name=__name__, url_prefix="/ccg", template_folder='templates')


@ccg.route("/decks/", methods=['GET', 'POST'])
@login_required
def decks() -> Response:
    method = request.method
    if method == 'GET':
        return get_decks()
    if method == 'POST':
        return create_deck()


@ccg.route("/decks/<deck_id>/add", methods=['POST'])
@ccg.route("/decks/<deck_id>/add/<card_id>", methods=['POST'])
@login_required
def add_card_to_deck(deck_id : int, card_id : int =None) -> Response:
    deck = Deck.query.get(int(deck_id))
    if not deck or (deck.user != current_user and not current_user.admin):
        return {"card_added": False}
    if card_id:
        card = Card.query.get(int(card_id))
        deck.cards.append(card)
        db.session.commit()
        return {"card_added": True, "card": card.jsonify(), "deck": deck.jsonify()}
    if not request.json:
        return {"card_added": False}
    card_data = request.json
    power = card_data['power']
    name = card_data['name']
    desc = card_data['description']
    card = Card(power=power, name=name, description=desc)
    deck.cards.append(card)
    db.session.commit()
    return {"card_added": True, "card": card.jsonify(), "deck": deck.jsonify()}

@ccg.route("/cards/<id>", methods=['DELETE'])
@login_required
def remove_card_from_user(id : int) -> Response:


# TODO: Return False when card was already isolated.
@ccg.route("/cards/<id>/isolate", methods=['PUT'])
@login_required
def remove_card_from_deck(id : int) -> Response:
    card = Card.query.get(int(id))
    if not card or (card.user != current_user and not current_user.admin):
        return {"card_removed": False}
    card.deck_id = None
    db.session.commit()
    return {"card_removed": True, "card": card.jsonify()}

@ccg.route("/cards/<id>/update", methods=['PUT'])
@login_required
def update_card(id: int) -> Response:
    card = Card.query.get(int(id))
    if not card or (card.user != current_user and not current_user.admin):
        return {'card_updated': False}
    updates = request.json
    for column in updates:
        if updates[column] and hasattr(card, column):
            setattr(card, column, updates[column])
    db.session.commit()
    return {'card_updated': True, 'card': card.jsonify()}

@ccg.route("/decks/<id>/update", methods=['PUT'])
@login_required
def update_deck(id: int) -> Response:
    deck = Deck.query.get(int(id))
    if not deck or (deck.user != current_user and not current_user.admin):
        return {'deck_updated': False}
    updates = request.json
    for column in updates:
        if updates[column] and hasattr(deck, column):
            setattr(deck, column, updates[column])
    db.session.commit()
    return {'deck_updated': True, 'deck': deck.jsonify()}