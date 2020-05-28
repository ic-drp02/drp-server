from ..db import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    summary = db.Column(db.String(200))
    content = db.Column(db.Text())

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
        }

    def __repr__(self):
        return f"<Post '{self.title}'>"
