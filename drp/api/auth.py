import uuid
from urllib.parse import urlencode

from flask import Blueprint, request
from flask_mail import Message

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jwt import encode
from datetime import datetime, timedelta

from .. import config
from ..db import db
from ..models import User, UserRole
from ..mail import mail
from ..swag import swag

from .users import serialize_role
from .utils import error

auth = Blueprint("auth", __name__)


@swag.definition("TokenResponse")
def token_response(id, token, role):
    """
    A response containing a jwt token for authentication with the api.
    ---
    properties:
      id:
        type: integer
      token:
        type: string
      role:
        type: string
    """
    return {
        "id": id,
        "token": token,
        "role": serialize_role(role),
    }


@auth.route("/authenticate", methods=["POST"])
def authenticate():
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
            email:
                type: string
                required: true
            password:
                type: string
                required: true
    """
    body = request.json

    email = body.get("email")
    password = body.get("password")

    if email is None or password is None:
        return error(400,
                     message="`email` and `password` fields"
                     "are required.")

    user = User.query.filter(User.email == email).one_or_none()

    if user is None:
        return error(401, type="InvalidCredentials")

    hasher = PasswordHasher()

    try:
        hasher.verify(user.password_hash, password)
    except VerifyMismatchError:
        return error(401, type="InvalidCredentials")

    if hasher.check_needs_rehash(user.password_hash):
        hash = hasher.hash(password)
        user.password_hash = hash
        db.session.commit()

    if not user.confirmed:
        return error(401, type="Unconfirmed")

    now = datetime.utcnow()
    expiration_time = now + timedelta(hours=2)

    claims = {
        "iat": now.strftime("%s"),
        "exp": expiration_time.strftime("%s"),
        "iss": config.JWT_ISSUER,
        "aud": config.JWT_AUDIENCE,
        "sub": email,
        "rol": "admin" if user.role == UserRole.ADMIN else "normal",
    }

    token = encode(claims, config.JWT_SECRET_KEY, algorithm="HS256")

    return token_response(user.id, token.decode("utf-8"), user.role)


@auth.route("/register", methods=["POST"])
def register():
    body = request.json

    email = body.get("email")
    if not email:
        return error(400, message="`email` is required")

    password = body.get("password")
    if not password:
        return error(400, message="`password` is required")

    email = email.lower()
    parts = email.split("@")
    if len(parts) != 2:
        return error(400, type="InvalidEmail")

    domain = parts[1]
    if domain != "nhs.net" and domain != "ic.ac.uk" \
            and domain != "imperial.ac.uk":
        return error(400, type="UnauthorisedDomain")

    if User.query.filter(User.email == email).one_or_none() is not None:
        return error(400, type="Registered")

    hasher = PasswordHasher()
    hash = hasher.hash(password)

    token = uuid.uuid4()
    user = User(email=email, password_hash=hash,
                role=UserRole.NORMAL, email_confirmation_token=token)

    db.session.add(user)
    db.session.commit()

    url = f"{request.host_url}/auth/register/confirm?" + \
        urlencode({"token": token})

    message = Message("Confirm your account: " + email, recipients=[email])
    message.html = "<p>Thanks for registering for the ICON guidelines app." \
        f"</p><p>Click <a href=\"{url}\">here</a> to confirm your account.</p>"

    mail.send(message)

    return "", 200


@auth.route("/register/confirm")
def confirm_registration():
    token = request.args.get("token")
    if token is None:
        return error(400, "missing `token` query parameter")

    user = User.query.filter(
        User.email_confirmation_token == token).one_or_none()

    if user is None:
        return "Invalid registration token. Please ensure you have " \
            "registered for an account in the ICON app.", 400

    if user.confirmed:
        return "This email has already been confirmed.", 400

    user.confirmed = True

    db.session.commit()

    return "Thanks for confirming your email. You should now be able to " \
        "login to the app."