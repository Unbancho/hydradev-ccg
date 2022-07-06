from flask import Blueprint, request
from flask_login import login_required, current_user
from models import Deck, Card, db


decks = Blueprint(name="decks", import_name=__name__, url_prefix="/decks", template_folder='templates')

@decks.route("/decks", methods=['POST'])
@login_required
def add_deck():
    deck_data = request.json
    name = deck_data['name']
    cards = deck_data['cards']
    deck = Deck(name=name, cards=cards)
    current_user.decks.append(deck)
    db.session.commit()
    return {"deck_created": deck.name}

@decks.route("/decks", methods=['GET'])
@login_required
def get_decks():
    decks = current_user.decks
    dictionary = {}
    for d in decks:
        dictionary[d.name] = [(c.name, c.power, c.description) for c in d.cards]
    return dictionary

@decks.route("/deck/<id>", methods=['GET'])
@login_required
def get_deck(id):
    deck = get_by_user_id(id, Deck)
    return {"name": deck.name, "cards": [c.name for c in deck.cards]}

@decks.route("/deck/<id>", methods=['DELETE'])
@login_required
def delete_deck(id):
    deck = get_by_user_id(id, Deck)
    db.session.delete(deck)
    db.session.commit()
    return {"deck_deleted": deck.name}

@decks.route("/cards", methods=['GET'])
@login_required
def get_cards():
    cards = current_user.cards
    return {c.user_id : c.name for c in cards}

@decks.route("/cards", methods=['POST'])
@login_required
def add_card_to_user():
    card_data = request.json
    power = card_data['power']
    name = card_data['name']
    desc = card_data['description']
    card = Card(power=power, name=name, description=desc)
    current_user.cards.append(card)
    db.session.commit()
    return {"card_added": card.name}

@decks.route("/card/<id>", methods=['POST'])
@login_required
def add_card_to_deck(id):
    deck = get_by_user_id(id, Deck)
    card_data = request.json
    power = card_data['power']
    name = card_data['name']
    desc = card_data['description']
    card = Card(power=power, name=name, description=desc)
    deck.cards.append(card)
    db.session.commit()
    return {"card_added": card.name, "deck": deck.name}

@decks.route("/card/<id>", methods=['DELETE'])
@login_required
def remove_card_from_user(id):
    card = get_by_user_id(id, Card)
    db.session.delete(card)
    db.session.commit()
    return {"card_deleted": card.name}

@decks.route("/card/<deck_id>/<card_id>", methods=['DELETE'])
@login_required
def remove_card_from_deck(deck_id, card_id):
    deck = get_by_user_id(deck_id, Deck)
    card = (Card.query.filter(Card.deck == deck)).filter_by(deck_id=card_id).first()    
    db.session.delete(card)
    db.session.commit()
    return {"card_deleted": card.name}

def get_by_user_id(id, model):
    return (model.query.filter(model.user == current_user)).filter_by(user_id=id).first()
