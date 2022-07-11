from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required


class CRUD:

    def __init__(self, prefix: str, methods: list, database: SQLAlchemy) -> None:
        self.prefix = prefix
        self.methods = methods
        self.database = database
        self.mappings = {"GET": self.read, "PUT": self.update,
                         "POST": self.create, "DELETE": self.delete}

    def create(self, **kwargs) -> jsonify:
        self._check_implemented('POST')

    def read(self, id: int = None, **kwargs) -> jsonify:
        self._check_implemented('GET')

    def update(self, id: int, **kwargs) -> jsonify:
        self._check_implemented('PUT')

    def delete(self, id: int, **kwargs) -> jsonify:
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

    @login_required
    def manager(self, id: int = None, **kwargs) -> jsonify:
        return self.mappings[request.method](id=id, args=request.args, **kwargs)
