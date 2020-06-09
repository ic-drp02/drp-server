from sqlalchemy.sql import func
from sqlalchemy.sql.expression import cast
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from ..db import db


def create_tsvector(*components):
    """Creates a postgresql text search vector from the provided components."""
    coalesced = list(
        map(lambda c: cast(func.coalesce(c, ''), postgresql.TEXT), components))
    expression = coalesced[0]
    for e in coalesced[1:]:
        expression += ' ' + e
    return func.to_tsvector('english', expression)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    summary = db.Column(db.String(200))
    content = db.Column(db.Text())
    is_guideline = db.Column(db.Boolean())
    superseding_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    superseding = relationship(
        'Post', uselist=False, remote_side=[id],
        backref=db.backref('superseded_by', uselist=False))

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           server_default=func.now())

    tags = relationship("Tag", secondary="post_tag")

    files = relationship("File", back_populates="post")

    __ts_vector__ = create_tsvector(
        title,
        summary,
        content
    )

    __table_args__ = (
        db.Index(
            'idx_post_fulltextsearch',
            __ts_vector__,
            postgresql_using='gin'
        ),
    )

    def __repr__(self):
        return f"<Post '{self.title}'>"


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)

    posts = relationship("Post", secondary="post_tag")

    def __repr__(self):
        return f"<Tag '{self.name}'>"


class Post_Tag(db.Model):
    __tablename__ = "post_tag"

    post_id = db.Column(db.Integer,
                        db.ForeignKey("posts.id"),
                        primary_key=True)

    tag_id = db.Column(db.Integer,
                       db.ForeignKey("tags.id"),
                       primary_key=True)

    post = relationship(Post)
    tag = relationship(Tag)

    def __repr__(self):
        return f"<Post_Tag {self.post} <-> {self.tag}>"


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    filename = db.Column(db.String(300))

    post_id = db.Column(db.Integer,
                        db.ForeignKey("posts.id"))
    post = relationship('Post', back_populates='files')

    def __repr__(self):
        return f"<File '{self.name}'>"
