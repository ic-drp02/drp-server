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
    """

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
