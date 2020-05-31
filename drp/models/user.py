import enum

from ..db import db


class UserRole(enum.Enum):
    NORMAL = 1
    ADMIN = 2


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    password_hash = db.Column(db.Text(), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False,
                     default=UserRole.NORMAL)

    def __repr__(self):
        return f"<User '{self.username}'>"
