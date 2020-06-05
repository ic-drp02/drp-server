from ..db import db


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    expo_push_token = db.Column(db.Text, nullable=False, unique=True)
