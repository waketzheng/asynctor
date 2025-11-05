class AsynctorError(Exception):
    pass


class ParamsError(AsynctorError):
    pass


class UnsupportedError(AsynctorError, ValueError):
    pass
