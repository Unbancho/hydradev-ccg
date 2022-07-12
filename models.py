from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RestrictedAccess:
    def can_be_accessed_by(self, user) -> bool:
        raise NotImplementedError


class JSONifiable:
    def jsonify(self) -> dict:
        raise NotImplementedError


# TODO: many-to-many table to have one card in multiple decks?


class Card(db.Model, RestrictedAccess, JSONifiable):
    id = db.Column(db.Integer, primary_key=True)
    power = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def can_be_accessed_by(self, user) -> bool:
        return self.user == user or user.admin

    def jsonify(self) -> dict:
        return {
                    'id': self.id,
                    'power': self.power,
                    'name': self.name,
                    'description': self.description,
                    'deck_id': self.deck_id,
                    'user_id': self.user_id
                }


class Deck(db.Model, RestrictedAccess, JSONifiable):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    cards = db.relationship("Card", backref='deck')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def can_be_accessed_by(self, user) -> bool:
        return self.user == user or user.admin

    def jsonify(self) -> dict:
        return {
                    'id': self.id,
                    'name': self.name,
                    'cards': [c.jsonify() for c in self.cards],
                    'user_id': self.user_id
                }


class User(db.Model, UserMixin, RestrictedAccess, JSONifiable):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), nullable=False, unique=True)
    hash = db.Column(db.String(), nullable=False)
    real_name = db.Column(db.String(), nullable=False)
    decks = db.relationship("Deck", backref='user', cascade="all, delete-orphan")
    cards = db.relationship("Card", backref='user', cascade="all, delete-orphan")
    admin = db.Column(db.Boolean, default=False)

    def can_be_accessed_by(self, user) -> bool:
        return self == user or user.admin

    def jsonify(self) -> dict:
        return {
                    'id': self.id,
                    'username': self.username,
                    'real_name': self.real_name,
                    'decks': [d.jsonify() for d in self.decks],
                    'cards': [c.jsonify() for c in self.cards],
                    'admin': self.admin
                }
