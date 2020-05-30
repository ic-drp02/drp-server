import pytz

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

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

    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    summary = db.Column(db.String(200))
    content = db.Column(db.Text())

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           server_default=func.now())

    tags = relationship("Tag", secondary="post_tag")

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "created_at": self.created_at.astimezone(pytz.utc).isoformat(),
            "tags": [tag.serialize() for tag in self.tags]
        }

    def __repr__(self):
        return f"<Post '{self.title}'>"


class Tag(db.Model):
    __tablename__ = "tag"

    name = db.Column(db.String(30), primary_key=True)

    posts = relationship("Post", secondary="post_tag")

    def serialize(self):
        return self.name

    def __repr__(self):
        return f"<Tag '{self.name}'>"


class Post_Tag(db.Model):
    __tablename__ = "post_tag"

    post_id = db.Column(db.Integer,
                        db.ForeignKey("post.id"),
                        primary_key=True)

    tag_name = db.Column(db.String(30),
                         db.ForeignKey("tag.name"),
                         primary_key=True)

    post = relationship(Post)
    tag = relationship(Tag)

    def __repr__(self):
        return f"<Post_Tag {self.post} <-> {self.tag}>"
