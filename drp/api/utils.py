from functools import wraps
from flask import request, g

from ..models import User, UserRole
from ..utils import decode_authorization_header


def error(code: int, message: str = None, type: str = None):
    body = {}

    if type:
        body["type"] = type

    if message:
        body["message"] = message

    return body, code, {"Content-Type": "application/json"}


def require_auth(f):
    @wraps(f)
    def decorated_f(*args, **kwargs):
        claims = decode_authorization_header(request)
        if claims is None:
            return error(401, type="InvalidAuthToken")

        g.user = User.query.filter(
            User.email == claims.get("sub")).one_or_none()

        if g.user is None:
            return error(401, type="InvalidAuthToken")

        return f(*args, **kwargs)

    return decorated_f


def require_admin(f):
    @wraps(f)
    def decorated_f(*args, **kwargs):
        claims = decode_authorization_header(request)
        if claims is None:
            return error(401, type="InvalidAuthToken")

        g.user = User.query.filter(
            User.email == claims.get("sub")).one_or_none()

        if g.user is None:
            return error(401, type="InvalidAuthToken")

        if g.user.role != UserRole.ADMIN:
            return error(401, type="InsufficientPermissions")

        return f(*args, **kwargs)

    return decorated_f
