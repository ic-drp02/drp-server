from enum import Enum

from sqlalchemy.orm import relationship

from ..db import db


class Grade(Enum):
    CONSULTANT = 1
    SPR = 2
    CORE_TRAINEE = 3
    FY2 = 4
    FY1 = 5
    FIY1 = 6


class Site(db.Model):
    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)

    def __repr__(self):
        return f"<Site '{self.name}'>"


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)

    def __repr__(self):
        return f"<Subject '{self.name}''>"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"))
    grade = db.Column(db.Enum(Grade))
    specialty = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"))
    text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", name="questions_user_id_fkey", ondelete="SET NULL"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))

    site = relationship("Site")
    subject = relationship("Subject")
    user = relationship("User")
    resolved_by = relationship("Post", back_populates="resolves")

    resolved = db.Column(db.Boolean, nullable=False, server_default="false")

    def __repr__(self):
        return f"<Question '{self.text}'>"
