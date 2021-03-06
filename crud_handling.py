from crud import CRUD, to_int
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify, request, abort
from authentication import bcrypt


class FilterableCRUD(CRUD):
    """
    CRUD manager with generalized GET by ID response. Filtering rules for URL query parameters must be implemented.
    """
    def read(self, **kwargs) -> jsonify:
        if id := kwargs.get('id'):
            return self.read_one(id=to_int(id))
        result = self._filter(kwargs.get('args'))
        return Response([r.jsonify() for r in result]), 200

    @CRUD.gets_by_id(needs_permission=True)
    def read_one(self, **kwargs) -> jsonify:
        return Response(kwargs['model'].jsonify()), 200

    # TODO: bad request handle JSON
    def _filter(self, args):
        """
        Must be implemented. Is used to handle URL query parameters.
        """
        raise NotImplementedError


class Decks(FilterableCRUD):
    def __init__(self):
        super().__init__("/decks", ["GET", "PUT", "POST", "DELETE"], db, Deck)

    @CRUD.needs_data('name')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        name = data['name']
        cards = data.get('cards', [])
        deck = Deck(name=name, cards=cards)
        user = User.query.get(to_int(id)) if (id := data.get('user')) and current_user.admin else current_user
        if not user:
            return abort(404)
        user.decks.append(deck)
        db.session.commit()
        return Response(data=deck.jsonify()), 201

    def _filter(self, args):
        if not args:
            return current_user.decks
        query = Deck.query
        if name := args.get('name'):
            query = query.filter(Deck.name.contains(name))
        if current_user.admin and (id := args.get('user')):
            query = query.filter(Deck.user_id == id)
        else:
            query = query.filter(Deck.user_id == current_user.id)
        return query.all()

    @CRUD.gets_by_id(needs_permission=True)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        deck = kwargs['model']
        deck = CRUD._update_model(deck, data)
        db.session.commit()
        return Response(data=deck.jsonify()), 200

    @CRUD.gets_by_id(needs_permission=True)
    def delete(self, **kwargs) -> jsonify:
        deck = kwargs['model']
        db.session.delete(deck)
        db.session.commit()
        return Response(message=f"Deleted {deck.name}"), 200


class Cards(FilterableCRUD):

    def __init__(self):
        super().__init__("/cards", ["GET", "PUT", "POST", "DELETE"], db, Card)

    @CRUD.needs_data('name', 'power')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        user = User.query.get(to_int(id)) if (id := data.get('user')) and current_user.admin else current_user
        if not user:
            return abort(404)
        card = Cards.create_card(data, user)
        db.session.commit()
        return Response(card.jsonify()), 201

    @staticmethod
    def create_card(data: dict, user: User) -> Card:
        desc = data.get('description', '')  # Some cards might just be Beatsticks.
        card = Card(power=to_int(data['power']), name=data['name'], description=desc)
        user.cards.append(card)
        return card

    def _filter(self, args):
        if not args:
            return current_user.cards
        query = Card.query
        if name := args.get('name'):
            query = query.filter(Card.name.contains(name))
        if power := args.get('power'):
            query = query.filter(Card.power == power)
        if desc := args.get('description'):
            query = query.filter(Card.description.contains(desc))
        if current_user.admin and (id := args.get('user')):
            query = query.filter(Card.user_id == id)
        else:
            query = query.filter(Card.user_id == current_user.id)
        return query.all()

    @CRUD.gets_by_id(needs_permission=True)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        card = kwargs['model']
        if deck_id := data.get('deck_id'):
            if not (deck := Deck.query.get(to_int(deck_id))):
                raise abort(404)
            if not deck.can_be_accessed_by(current_user):
                raise abort(403)
        card = CRUD._update_model(card, data)
        db.session.commit()
        return Response(data=card.jsonify()), 200

    @CRUD.gets_by_id(needs_permission=True)
    def delete(self, **kwargs) -> jsonify:
        card = kwargs['model']
        db.session.delete(card)
        db.session.commit()
        return Response(message=f"Deleted {card.name}"), 200


class Users(CRUD):

    def __init__(self):
        super().__init__("/users", ["GET", "PUT", "POST", "DELETE"], db, User)

    @staticmethod
    def needs_admin(func):
        def _inner(self, **kwargs):
            if not current_user.admin:
                return abort(403)
            return func(self, **kwargs)
        return _inner

    @needs_admin
    @CRUD.needs_data('username', 'password', 'real_name')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        username = data['username']
        password = data['password']
        real_name = data['real_name']
        if User.query.filter_by(username=username).first():
            return abort(400)
        p_hash = bcrypt.generate_password_hash(password)
        user = User(username=username, hash=p_hash, real_name=real_name, admin=data.get('admin', False))
        db.session.add(user)
        db.session.commit()
        return Response(user.jsonify()), 201

    @needs_admin
    def read(self, **kwargs) -> jsonify:
        if id := kwargs.get('id'):
            user = User.query.get(to_int(id))
            if user:
                return Response(user.jsonify()), 200
            else:
                return Response(), 404
        result = User.query.all()
        return Response([r.jsonify() for r in result]), 200

    @needs_admin
    @CRUD.gets_by_id(needs_permission=False)
    def update(self, **kwargs) -> jsonify:
        data = dict(request.json)
        user = kwargs['model']
        if password := data.pop("password", None):  # NOTE: We need to hash the password before replacing.
            user.hash = bcrypt.generate_password_hash(password)
        user = CRUD._update_model(user, data)
        db.session.commit()
        return Response(data=user.jsonify()), 200

    @needs_admin
    @CRUD.gets_by_id(needs_permission=False)
    def delete(self, **kwargs) -> jsonify:
        user = kwargs['model']
        if user == current_user:
            return abort(403)
        db.session.delete(user)
        db.session.commit()
        return Response(message=f"Deleted {user.username}"), 200
