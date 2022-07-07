from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    power = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def jsonify(self) -> dict:
        return {'id': self.id, 'power': self.power, 'name': self.name, 'description': self.description, 'deck_id': self.deck_id, 'user_id': self.user_id}


class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    cards = db.relationship("Card", backref='deck')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def jsonify(self) -> dict:
        return {'id': self.id, 'name': self.name, 'cards': [c.jsonify() for c in self.cards], 'user_id': self.user_id}

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), nullable=False, unique=True)
    hash = db.Column(db.String(), nullable=False)
    real_name = db.Column(db.String(), nullable=False)
    decks = db.relationship("Deck", backref='user')
    cards = db.relationship("Card", backref='user')
    admin = db.Column(db.Boolean, default=False)

    def jsonify(self) -> dict:
        return {'id': self.id, 'username': self.username, 'real_name': self.real_name, 'decks': [d.jsonify() for d in self.decks], 'cards': [c.jsonify() for c in self.cards]}

    def is_admin(self) -> bool:
        return self.admin