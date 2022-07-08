from response import Response
from flask import jsonify


class CRUD:

    def __init__(self, methods: list) -> None:
        self.methods = methods

    def create(self, data=None, **kwargs) -> jsonify:
        self._check_implemented('POST')

    def read(self, id: int = None, **kwargs) -> jsonify:
        self._check_implemented('GET')

    def update(self, id: int, data=None, **kwargs) -> jsonify:
        self._check_implemented('PUT')

    def delete(self, id: int, **kwargs) -> jsonify:
        self._check_implemented('DELETE')

    def _check_implemented(self, method: str):
        if method in self.methods:
            raise NotImplementedError(f"Method {method} not allowed.")
