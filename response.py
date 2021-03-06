data_key = "data"
message_key = "message"


class Response:
    """
    Simple response dict generator.
    """
    def __new__(cls, data=None, message: str = None, **kwargs) -> dict:
        return {data_key: data, message_key: message} | kwargs
