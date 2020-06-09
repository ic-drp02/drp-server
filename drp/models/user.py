import enum

from ..db import db


class UserRole(enum.Enum):
    NORMAL = 1
    ADMIN = 2


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Text())

    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    role = db.Column(db.Enum(UserRole), nullable=False,
                     default=UserRole.NORMAL)

    confirmed = db.Column(db.Boolean, nullable=False, server_default="false")
    email_confirmation_token = db.Column(db.Text())

    def __repr__(self):
        return f"<User '{self.username}'>"
