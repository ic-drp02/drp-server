from sqlalchemy.sql import func

from ..db import db
from .. import swag


@swag.definition("Post")
class Post(db.Model):
    """
    Represents a post.
    ---
    properties:
      id:
        type: integer
      title:
        type: string
      summary:
        type: string
      content:
        type: string
      created_at:
        type: string
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    summary = db.Column(db.String(200))
    content = db.Column(db.Text())

    created_at = db.Column(db.DateTime, nullable=False,
                           server_default=func.now())

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Post '{self.title}'>"
