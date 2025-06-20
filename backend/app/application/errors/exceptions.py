class AppException(RuntimeError):
    def __init__(
        self,
        code: int,
        msg: str,
        status_code: int = 400,
    ):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, msg: str = "Resource not found"):
        super().__init__(code=404, msg=msg, status_code=404)


class BadRequestError(AppException):
    def __init__(self, msg: str = "Bad request parameters"):
        super().__init__(code=400, msg=msg, status_code=400)


class ServerError(AppException):
    def __init__(self, msg: str = "Internal server error"):
        super().__init__(code=500, msg=msg, status_code=500)


class UnauthorizedError(AppException):
    def __init__(self, msg: str = "Unauthorized"):
        super().__init__(code=401, msg=msg, status_code=401)


class UserAlreadyExistsError(BadRequestError):
    def __init__(self, msg: str = "User already exists"):
        super().__init__(msg=msg)


class UserNotFoundError(NotFoundError):
    def __init__(self, msg: str = "User not found"):
        super().__init__(msg=msg)


class InvalidCredentialsError(UnauthorizedError):
    def __init__(self, msg: str = "Invalid credentials"):
        super().__init__(msg=msg) 