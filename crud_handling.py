from crud import CRUD, try_int
from response import Response
from models import User, Deck, Card, db
from flask_login import current_user
from flask import jsonify, request, abort
from authentication import bcrypt

NoAlterations = "No alterations"


class FilterableCRUD(CRUD):
    def read(self, **kwargs) -> jsonify:
        if id := kwargs.get('id'):
            return self.read_one(id=try_int(id))
        result = self._filter(kwargs.get('args'))
        return Response([r.jsonify() for r in result]), 200

    @CRUD.gets_by_id(needs_permission=True)
    def read_one(self, **kwargs):
        return Response(kwargs['model'].jsonify()), 200

    # TODO: bad request handle JSON
    def _filter(self, args):
        raise NotImplementedError


class RestrictedFilterableCRUD(FilterableCRUD):
    # TODO: bad request handle JSON
    def _filter(self, args):
        if not args:
            return self.model.query.filter(self.model.user_id == current_user.id)
        query = self.model.query
        for arg in args:
            try:
                query = self._filter_by_arg(query, arg, args[arg])
            except AttributeError:
                abort(404)
        if not current_user.admin:
            query = query.filter(self.model.user_id == current_user.id)
        return query.all()

    def _filter_by_arg(self, query, key, value):
        return query.filter(getattr(self.model, key).contains(value)) \
            if isinstance(getattr(self.model, key), str) else query.filter(getattr(self.model, key) == value)


class Decks(RestrictedFilterableCRUD):
    def __init__(self):
        super().__init__("/decks", ["GET", "PUT", "POST", "DELETE"], db, Deck)

    @CRUD.needs_data('name')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        name = data['name']
        cards = data.get('cards', [])
        deck = Deck(name=name, cards=cards)
        user = User.query.get(try_int(id)) if (id := data.get('user')) and current_user.admin else current_user
        if not user:
            return abort(404)
        user.decks.append(deck)
        db.session.commit()
        return Response(data=deck.jsonify()), 201

    @CRUD.gets_by_id(needs_permission=True)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        deck = kwargs['model']
        old = deck.jsonify()
        deck = CRUD._update_model(deck, data)
        db.session.commit()
        return Response(data=deck.jsonify(), message=None if deck.jsonify() != old else NoAlterations), 200

    @CRUD.gets_by_id(needs_permission=True)
    def delete(self, **kwargs) -> jsonify:
        deck = kwargs['model']
        db.session.delete(deck)
        db.session.commit()
        return Response(message=f"Deleted {deck.name}"), 200


class Cards(RestrictedFilterableCRUD):

    def __init__(self):
        super().__init__("/cards", ["GET", "PUT", "POST", "DELETE"], db, Card)

    @CRUD.needs_data('name', 'power')
    def create(self, **kwargs) -> jsonify:
        data = kwargs['data']
        user = User.query.get(try_int(id)) if (id := data.get('user')) and current_user.admin else current_user
        if not user:
            return abort(404)
        card = Cards.create_card(data, user)
        db.session.commit()
        return Response(card.jsonify()), 201

    @staticmethod
    def create_card(data: dict, user: User) -> Card:
        desc = data.get('description', '')  # Some cards might just be Beatsticks.
        card = Card(power=try_int(data['power']), name=data['name'], description=desc)
        user.cards.append(card)
        return card

    # TODO: Fix adding to deck that doesn't exist.
    @CRUD.gets_by_id(needs_permission=True)
    def update(self, **kwargs) -> jsonify:
        data = request.json
        card = kwargs['model']
        # TODO: Fix.
        if deck_id := data.get('deck_id'):
            if not (deck := Deck.query.get(try_int(deck_id))):
                raise abort(404)
            if not deck.can_be_accessed_by(current_user):
                raise abort(403)
        old = card.jsonify()
        card = CRUD._update_model(card, data)
        db.session.commit()
        return Response(data=card.jsonify(), message=None if old != card.jsonify() else NoAlterations), 200

    @CRUD.gets_by_id(needs_permission=True)
    def delete(self, **kwargs) -> jsonify:
        card = kwargs['model']
        db.session.delete(card)
        db.session.commit()
        return Response(message=f"Deleted {card.name}"), 200


class Users(FilterableCRUD):

    def __init__(self):
        super().__init__("/users", ["GET", "PUT", "POST", "DELETE"], db, User)

    def _filter(self, args):
        if not args:
            return User.query.all()
        query = User.query
        for arg in args:
            query = query.filter(getattr(User, arg) == args[arg])
        return query.all()

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
        return super().read(**kwargs)

    @needs_admin
    @CRUD.gets_by_id(needs_permission=False)
    def update(self, **kwargs) -> jsonify:
        data = dict(request.json)
        user = kwargs['model']
        old = user.jsonify()
        if password := data.pop("password", None):
            user.hash = bcrypt.generate_password_hash(password)
        user = CRUD._update_model(user, data)
        db.session.commit()
        return Response(data=user.jsonify(),
                        message=None if old != user.jsonify() else NoAlterations), 200

    @needs_admin
    @CRUD.gets_by_id(needs_permission=False)
    def delete(self, **kwargs) -> jsonify:
        user = kwargs['model']
        if user == current_user:
            return abort(403)
        db.session.delete(user)
        db.session.commit()
        return Response(message=f"Deleted {user.username}"), 200
