status_key = "success"
data_key = "data"
message_key = "message"


class Response:
    def __new__(cls, status: bool = False, data=None, message: str = None, **kwargs) -> dict:
        return {status_key: status, data_key: data, message_key: message} | kwargs
