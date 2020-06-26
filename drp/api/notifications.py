from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from ..db import db
from ..models import Device, User

from .utils import abort

notifications = Blueprint("notifications", __name__)


@notifications.route("/register", methods=["POST"])
def register():
    token = request.args.get("token")
    user = request.args.get("user")

    if not token:
        abort(400, "Missing `token` query parameter")

    user = User.query.filter(User.id == user).one_or_none()
    if not user:
        abort(400, "Missing `user` query parameter")

    device = Device(expo_push_token=token, user=user)

    db.session.add(device)

    try:
        db.session.commit()
    except IntegrityError as err:
        if err.orig.pgcode == "23505":
            # Ignore if device has already been registered
            pass
        else:
            raise

    return "", 200
