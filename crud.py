from flask import jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, current_user
from response import Response

NotProvided = "Not provided: "
NoWithID = "Doesn't exist."
Unauthorized = "Unauthorized."


class CRUD:
    """
    HTTP method router. Maps POST, GET, PUT, DELETE methods to CRUD methods.
    """
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
        """
        Patches a resource from PUT data.
        # TODO: Consider PATCH or POST and re-design updating to better conform to convention.
        """
        for column in data:
            if hasattr(obj, column):
                setattr(obj, column, data[column])
        return obj

    @staticmethod
    def needs_data(*args: str):
        """
        Decorator function. Use this to decorate methods that need certain elements from a JSON request.
        Returns 400 if requirements are not satisfied.
        """
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
        """
        Decorator function. Use this to decorate methods that need to access a resource from an ID from the URL.
        If needs_permission is set to True, it will return 403 if the caller has no access to the resource.
        Returns 400 if ID is invalid or missing; Returns 404 if corresponding resource does not exist.
        """
        def _outer(func):
            def _inner(self, **kwargs):
                id = kwargs.get('id')
                if not id:
                    return Response(message=NotProvided+'id'), 400
                if not (model := self.model.query.get(to_int(id))):
                    return Response(message=f'No {self.model.__name__} with ID {id}'), 404
                if needs_permission and not model.can_be_accessed_by(current_user):
                    return Response(message=f''), 403
                return func(self, model=model, **kwargs)
            return _inner
        return _outer

    @login_required
    def router(self, id: int = None, **kwargs) -> jsonify:
        """
        Receives all CRUD requests and routes them to the appropriate CRUD function.
        """
        return self.mappings[request.method](id=id, data=request.json if request.is_json else None,
                                             args=request.args, **kwargs)


def to_int(i):
    """
    utility method to throw 400 when failing to convert request data to int.
    """
    try:
        return int(i)
    except ValueError:
        abort(400)
