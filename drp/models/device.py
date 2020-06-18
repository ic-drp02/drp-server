from ..db import db

from sqlalchemy.orm import relationship


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    expo_push_token = db.Column(db.Text, nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", name="devices_user_id_fkey", ondelete="SET NULL"))

    user = relationship("User")
