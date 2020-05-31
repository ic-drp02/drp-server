from flask import request
from flask_restful import Resource, abort

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import encode
from datetime import datetime, timedelta

from .. import config
from ..db import db
from ..models import User, UserRole
from ..swag import swag


@swag.definition("TokenResponse")
def token_response(token):
    """
    A response containing a jwt token for authentication with the api.
    ---
    properties:
      token:
        type: integer
    """
    return {
        "token": token
    }


class AuthResource(Resource):

    def post(self):
        """
        Authenticates the user with the supplied credentials, returning
        an authentication token for subsequent use with the api.
        ---
        parameters:
          - in: body
            name: credentials
            schema:
              type: object
              properties:
                username:
                  type: string
                  required: true
                password:
                  type: string
                  required: true
        """
        body = request.json

        username = body.get("username")
        password = body.get("password")

        if username is None or password is None:
            return abort(400,
                         message="`username` and `password` fields"
                         "are required.")

        user = User.query.filter(User.username == username).one_or_none()

        if user is None:
            return abort(401)

        hasher = PasswordHasher()

        try:
            hasher.verify(user.password_hash, password)
        except VerifyMismatchError:
            return abort(401)

        if hasher.check_needs_rehash(user.password_hash):
            hash = hasher.hash(password)
            user.password_hash = hash
            db.session.commit()

        now = datetime.utcnow()
        expiration_time = now + timedelta(hours=2)

        claims = {
            "iat": now.strftime("%s"),
            "exp": expiration_time.strftime("%s"),
            "iss": config.JWT_ISSUER,
            "aud": config.JWT_AUDIENCE,
            "sub": username,
            "rol": "admin" if user.role == UserRole.ADMIN else "normal",
        }

        token = encode(claims, config.JWT_SECRET_KEY, algorithm="HS256")

        return token_response(token.decode("utf-8"))
