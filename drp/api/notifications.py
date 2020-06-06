from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from ..db import db
from ..models import Device

from .utils import error

notifications = Blueprint("notifications", __name__)


@notifications.route("/register", methods=["POST"])
def register():
    token = request.args.get("token")

    if not token:
        return error(400, "Missing `token` query parameter")

    device = Device(expo_push_token=token)

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
