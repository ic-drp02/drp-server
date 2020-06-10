import uuid
from urllib.parse import urlencode

from flask import Blueprint, request, jsonify, g
from flask_mail import Message

from sqlalchemy.exc import IntegrityError
from argon2 import PasswordHasher

from ..db import db
from ..models import User, UserRole
from ..mail import mail

from .utils import require_auth, require_admin, error


users = Blueprint("users", __name__)


def serialize_role(role):
    if role == UserRole.ADMIN:
        return "admin"
    else:
        return "normal"


def serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": serialize_role(user.role),
        "confirmed": user.confirmed
    }


@users.route("/", methods=["GET", "POST"])
@require_admin
def index():
    if request.method == "GET":
        return get_all_users()

    elif request.method == "POST":
        return create_user()


def get_all_users():
    users = User.query.all()
    return jsonify([serialize_user(user) for user in users])


def create_user():
    body = request.json

    email = body.get("email")
    password = body.get("password")
    role = body.get("role")

    if email is None or password is None:
        return error(400,
                     message="`email` and `password` fields"
                     "are required.")

    if role is not None and role != "normal" and role != "admin":
        return error(400, message="`role` must be one of {normal, admin}.")

    role = UserRole.ADMIN if (role == "admin") else UserRole.NORMAL

    hasher = PasswordHasher()
    hash = hasher.hash(password)

    token = uuid.uuid4()
    user = User(email=email, password_hash=hash,
                role=role, email_confirmation_token=token)

    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError as err:
        if err.orig.pgcode == "23505":
            return error(
                422, message="A user with this email already exists.")
        else:
            raise

    url = f"{request.host_url}auth/register/confirm?" + \
        urlencode({"token": token})

    message = Message("Confirm your account: " + email, recipients=[email])
    message.html = "<p>Thanks for registering for the ICON guidelines app." \
        f"</p><p>Click <a href=\"{url}\">here</a> to confirm your account.</p>"

    mail.send(message)

    return serialize_user(user)


@users.route("/<int:id>", methods=["GET", "PUT", "DELETE"])
@require_auth
def by_id(id):
    if g.user.role != UserRole.ADMIN and g.user.id != id:
        return error(401, type="InsufficientPermissions")

    if request.method == "GET":
        return get_user_by_id(id)

    elif request.method == "PUT":
        return update_user_by_id(id)

    elif request.method == "DELETE":
        return delete_user_by_id(id)


def get_user_by_id(id):
    if g.user.id == id:
        user = g.user
    else:
        user = User.query.filter(User.id == id).one_or_none()

    if user is None:
        return error(404)

    return serialize_user(user)


def update_user_by_id(id):
    if g.user.id == id:
        user = g.user
    else:
        user = User.query.filter(User.id == id).one_or_none()

    if user is None:
        return error(404)

    body = request.json

    password = body.get("password")
    role = body.get("role")

    if password:
        hasher = PasswordHasher()
        hash = hasher.hash(password)
        user.password_hash = hash

    if role:
        if g.user.role != UserRole.ADMIN:
            return error(401, type="InsufficientPermission")

        if role != "normal" and role != "admin":
            return error(400, message="`role` must be one of {normal, admin}.")

        user.role = UserRole.ADMIN if (role == "admin") else UserRole.NORMAL

    db.session.commit()

    return serialize_user(user)


def delete_user_by_id(id):
    if g.user.id == id:
        user = g.user
    else:
        user = User.query.filter(User.id == id).one_or_none()

    if user is None:
        return error(404)

    db.session.delete(user)
    db.session.commit()

    return "", 204
