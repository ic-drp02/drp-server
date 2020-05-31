from flask import request
from flask_restful import Resource, abort

from sqlalchemy.exc import IntegrityError
from argon2 import PasswordHasher

from ..db import db
from ..models import User, UserRole
from ..utils import decode_authorization_header
from ..swag import swag


def serialize_role(role):
    if role == UserRole.ADMIN:
        return "admin"
    else:
        return "normal"


@swag.definition("User")
def serialize_user(user):
    """
    Represents a user.
    ---
    properties:
      id:
        type: integer
      username:
        type: string
      first_name:
        type: string
      last_name:
        type: string
      role:
        type: string
        enum: [normal, admin]
    """
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": serialize_role(user.role)
    }


class UserResource(Resource):

    def get(self, id):
        """
        Gets a single user by id.
        ---
        security:
          Bearer: []
        responses:
          200:
            schema:
              $ref: "#/definitions/User"
          401:
            description: Unauthorizaed
          404:
            description: Not found
        """
        claims = decode_authorization_header(request)
        if claims is None:
            return abort(401)

        user = User.query.filter(User.id == id).one_or_none()

        # If the authenticated user is not an admin we
        # may still accept the request if they are trying
        # to get their own data.
        if claims["rol"] != "admin":
            if user is None or user.username != claims["sub"]:
                return abort(401)

        if user is None:
            return abort(404)

        return serialize_user(user)

    def put(self, id):
        """
        Updates a user.
        ---
        security:
          Bearer: []
        responses:
          200:
            schema:
              $ref: "#/definitions/User"
          400:
            description: Invalid request
          401:
            description: Unauthorized
          404:
            description: Not found
        """
        claims = decode_authorization_header(request)
        if claims is None:
            return abort(401)

        user = User.query.filter(User.id == id).one_or_none()

        # If the authenticated user is not an admin we
        # may still accept the request if they are trying
        # to modify their own data.
        if claims["rol"] != "admin":
            if user is None or user.username != claims["sub"]:
                return abort(401)

        if user is None:
            return abort(404)

        body = request.json

        username = body.get("username")
        password = body.get("password")
        first_name = body.get("first_name")
        last_name = body.get("last_name")
        role = body.get("role")

        def error_message(name, count):
            return f"`{name}` must not be more than {count} characters."

        if username is not None and len(username) > 80:
            return abort(400, message=error_message("username", 80))

        if first_name is not None and len(first_name) > 80:
            return abort(400, message=error_message("first_name", 80))

        if last_name is not None and len(last_name) > 80:
            return abort(400, message=error_message("last_name", 80))

        if role is not None and role != "normal" and role != "admin":
            return abort(400, message="`role` must be one of {normal, admin}.")

        role = UserRole.ADMIN if (role == "admin") else UserRole.NORMAL

        if username is not None:
            user.username = username

        if password is not None:
            hasher = PasswordHasher()
            hash = hasher.hash(password)
            user.password_hash = hash

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if role is not None:
            role = UserRole.ADMIN if role == "admin" else UserRole.NORMAL
            user.role = role

        try:
            db.session.commit()
        except IntegrityError as err:
            if err.orig.pgcode == "23505":
                return abort(
                    422, message="A user with this username already exists.")
            else:
                raise

        return serialize_user(user)

    def delete(self, id):
        """
        Deletes a user.
        ---
        security:
          Bearer: []
        responses:
          204:
            description: Success
          401:
            description: Unauthorizaed
          404:
            description: Not found
        """
        claims = decode_authorization_header(request)
        if claims is None:
            return abort(401)

        user = User.query.filter(User.id == id).one_or_none()

        # If the authenticated user is not an admin we
        # may still accept the request if they are trying
        # to delete their own account.
        if claims["rol"] != "admin":
            if user is None or user.username != claims["sub"]:
                return abort(401)

        if user is None:
            return abort(404)

        db.session.delete(user)
        db.session.commit()

        return "", 204


class UserListResource(Resource):

    def get(self):
        """
        Gets a list of all users.
        ---
        security:
          Bearer: []
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/User"
        """
        claims = decode_authorization_header(request)
        if claims is None or claims["rol"] != "admin":
            return abort(401)

        users = User.query.all()
        return [serialize_user(user) for user in users]

    def post(self):
        """
        Creates a new user.
        ---
        security:
          Bearer: []
        parameters:
          - in: body
            name: user
            schema:
              type: object
              properties:
                username:
                  type: string
                  required: true
                  maxLength: 80
                password:
                  type: string
                  required: true
                first_name:
                  type: string
                  required: false
                  maxLength: 80
                last_name:
                  type: string
                  required: false
                  maxLength: 80
                role:
                  type: string
                  required: false
                  enum:
                    - normal
                    - admin
        responses:
          200:
            schema:
              $ref: "#/definitions/User"
          400:
            description: Invalid request
          401:
            description: Unauthorized
        """
        claims = decode_authorization_header(request)
        if claims is None or claims["rol"] != "admin":
            return abort(401)

        body = request.json

        username = body.get("username")
        password = body.get("password")
        first_name = body.get("first_name")
        last_name = body.get("last_name")
        role = body.get("role")

        if username is None or password is None:
            return abort(400,
                         message="`username` and `password` fields"
                         "are required.")

        def error_message(name, count):
            return f"`{name}` must not be more than {count} characters."

        if len(username) > 80:
            return abort(400, message=error_message("username", 80))

        if first_name is not None and len(first_name) > 80:
            return abort(400, message=error_message("first_name", 80))

        if last_name is not None and len(last_name) > 80:
            return abort(400, message=error_message("last_name", 80))

        if role is not None and role != "normal" and role != "admin":
            return abort(400, message="`role` must be one of {normal, admin}.")

        role = UserRole.ADMIN if (role == "admin") else UserRole.NORMAL

        hasher = PasswordHasher()
        hash = hasher.hash(password)

        user = User(username=username,
                    password_hash=hash,
                    first_name=first_name,
                    last_name=last_name,
                    role=role)

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError as err:
            if err.orig.pgcode == "23505":
                return abort(
                    422, message="A user with this username already exists.")
            else:
                raise

        return serialize_user(user)
