from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Deck, Card, db


ccg = Blueprint(name="decks", import_name=__name__, url_prefix="/ccg", template_folder='templates')

@ccg.route("/decks/add", methods=['POST'])
@login_required
def add_deck() -> jsonify:
    deck_data = request.json
    name = deck_data['name']
    cards = deck_data['cards']
    deck = Deck(name=name, cards=cards)
    current_user.decks.append(deck)
    db.session.commit()
    return {"deck_created": True, "deck": deck.jsonify()}

@ccg.route("/decks", methods=['GET'])
@login_required
def get_decks() -> jsonify:
    decks = current_user.decks
    return dict(enumerate([d.jsonify() for d in decks]))

@ccg.route("/decks/<id>", methods=['GET'])
@login_required
def get_deck(id: int) -> jsonify:
    deck = Deck.query.get(int(id))
    if deck and (deck.user == current_user or current_user.admin):
        return deck.jsonify()
    return {}

@ccg.route("/decks/<id>/delete", methods=['DELETE'])
@login_required
def delete_deck(id: int) -> jsonify:
    deck = Deck.query.get(int(id))
    if not deck or (deck.user != current_user and not current_user.admin):
        return {"deck_deleted": False}
    db.session.delete(deck)
    db.session.commit()
    return {"deck_deleted": True, "deck": deck.jsonify()}

@ccg.route("/cards")
@ccg.route("/cards/<name>", methods=['GET'])
@login_required
def get_cards(name : str = None) -> jsonify:
    if name:
        cards = ((Card.query.filter(Card.user == current_user)).filter(Card.name.contains(name))).all()
    else:
        cards = current_user.cards
    return dict(enumerate([c.jsonify() for c in cards]))

@ccg.route("/cards/add", methods=['POST'])
@login_required
def add_card_to_user() -> jsonify:
    card_data = request.json
    power = card_data['power']
    name = card_data['name']
    desc = card_data['description']
    card = Card(power=power, name=name, description=desc)
    current_user.cards.append(card)
    db.session.commit()
    return {"card_added": True, "card": card.jsonify()}

@ccg.route("/decks/<deck_id>/add", methods=['POST'])
@ccg.route("/decks/<deck_id>/add/<card_id>", methods=['POST'])
@login_required
def add_card_to_deck(deck_id : int, card_id : int =None) -> jsonify:
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
def remove_card_from_user(id : int) -> jsonify:
    card = Card.query.get(int(id))
    if not card or (card.user != current_user and not current_user.admin):
        return {"card_deleted": False}
    db.session.delete(card)
    db.session.commit()
    return {"card_deleted": True, "card": card.jsonify()}

# TODO: Return False when card was already isolated.
@ccg.route("/cards/<id>/isolate", methods=['PUT'])
@login_required
def remove_card_from_deck(id : int) -> jsonify:
    card = Card.query.get(int(id))
    if not card or (card.user != current_user and not current_user.admin):
        return {"card_removed": False}
    card.deck_id = None
    db.session.commit()
    return {"card_removed": True, "card": card.jsonify()}

@ccg.route("/cards/<id>/update", methods=['PUT'])
@login_required
def update_card(id: int) -> jsonify:
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
def update_deck(id: int) -> jsonify:
    deck = Deck.query.get(int(id))
    if not deck or (deck.user != current_user and not current_user.admin):
        return {'deck_updated': False}
    updates = request.json
    for column in updates:
        if updates[column] and hasattr(deck, column):
            setattr(deck, column, updates[column])
    db.session.commit()
    return {'deck_updated': True, 'deck': deck.jsonify()}