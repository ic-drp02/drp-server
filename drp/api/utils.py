from functools import wraps
from flask import request, g, jsonify, abort as flask_abort

from ..models import User, UserRole
from ..utils import decode_authorization_header


def abort(code: int, message: str = None, type: str = None):
    if not type:
        type = "error"

    body = {"type": type}

    if message:
        body["message"] = message

    response = jsonify(body)
    response.status_code = code

    flask_abort(response)


def require_auth(f):
    @wraps(f)
    def decorated_f(*args, **kwargs):
        claims = decode_authorization_header(request)
        if claims is None:
            abort(401, type="InvalidAuthToken")

        g.user = User.query.filter(
            User.email == claims.get("sub")).one_or_none()

        if g.user is None:
            abort(401, type="InvalidAuthToken")

        return f(*args, **kwargs)

    return decorated_f


def require_admin(f):
    @wraps(f)
    def decorated_f(*args, **kwargs):
        claims = decode_authorization_header(request)
        if claims is None:
            abort(401, type="InvalidAuthToken")

        g.user = User.query.filter(
            User.email == claims.get("sub")).one_or_none()

        if g.user is None:
            abort(401, type="InvalidAuthToken")

        if g.user.role != UserRole.ADMIN:
            abort(401, type="InsufficientPermissions")

        return f(*args, **kwargs)

    return decorated_f
