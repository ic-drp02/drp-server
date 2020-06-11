from argon2 import PasswordHasher

from drp import create_app
from drp.models import User, UserRole
from drp.db import db

hasher = PasswordHasher()
hash = hasher.hash("password")

with create_app().app_context():
    user = User(email="ham418@imperial.ac.uk", password_hash=hash,
                role=UserRole.ADMIN, confirmed=True)

    db.session.add(user)
    db.session.commit()
