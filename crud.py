from flask import jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, current_user
from response import Response

NotProvided = "Not provided: "
NoWithID = "Doesn't exist."
Unauthorized = "Unauthorized."


class CRUD:

    def __init__(self, prefix: str, methods: list, database: SQLAlchemy, model) -> None:
        self.prefix = prefix
        self.methods = methods
        self.database = database
        self.mappings = {"GET": self.read, "PUT": self.update,
                         "POST": self.create, "DELETE": self.delete}
        self.model = model

    def create(self, **kwargs) -> jsonify:
        self._check_implemented('POST')

    def read(self, **kwargs) -> jsonify:
        self._check_implemented('GET')

    def update(self, **kwargs) -> jsonify:
        self._check_implemented('PUT')

    def delete(self, **kwargs) -> jsonify:
        self._check_implemented('DELETE')

    def _check_implemented(self, method: str):
        if method in self.methods:
            raise NotImplementedError(f"Method {method} not allowed.")

    @staticmethod
    def _update_model(obj, data):
        for column in data:
            if hasattr(obj, column):
                setattr(obj, column, data[column])
        return obj

    @staticmethod
    def needs_data(*args: str):
        def _outer(func):
            def _inner(self, **kwargs):
                data = kwargs.get("data", {})
                for d in args:
                    if d not in data:
                        return Response(message=NotProvided + d), 400
                return func(self, **kwargs)
            return _inner
        return _outer

    @staticmethod
    def gets_by_id(needs_permission: bool = False):
        def _outer(func):
            def _inner(self, **kwargs):
                id = kwargs.get('id')
                if not id:
                    return Response(message=NotProvided+'id'), 400
                if not (model := self.model.query.get(try_int(id))):
                    return Response(message=NoWithID), 404
                if needs_permission and not model.can_be_accessed_by(current_user):
                    return Response(message=Unauthorized), 403
                return func(self, model=model, **kwargs)
            return _inner
        return _outer

    @login_required
    def manager(self, id: int = None, **kwargs) -> jsonify:
        return self.mappings[request.method](id=id, data=request.json if request.is_json else None,
                                             args=request.args, **kwargs)


# TODO: Change to make these return JSON
def try_int(i):
    try:
        return int(i)
    except ValueError:
        abort(400)
