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

    is_guideline = db.Column(db.Boolean(), nullable=False)

    latest_rev_id = db.Column(db.Integer, db.ForeignKey(
        "post_revisions.id", name="posts_latest_rev_id_fkey"), nullable=True)

    latest_rev = relationship("PostRevision",
                              foreign_keys=[latest_rev_id])

    revisions = relationship("PostRevision",
                             foreign_keys="[PostRevision.post_id]",
                             back_populates="post")

    resolves = relationship("Question", back_populates="resolved_by")


class PostRevision(db.Model):
    __tablename__ = "post_revisions"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey(
        "posts.id", name="post_revisions_post_id_fkey", ondelete="CASCADE"),
        nullable=False)

    title = db.Column(db.Text(), nullable=False)
    summary = db.Column(db.Text(), nullable=False)
    content = db.Column(db.Text(), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           server_default=func.now())

    post = relationship("Post",
                        foreign_keys=[post_id],
                        back_populates="revisions")

    tags = relationship("Tag", secondary="post_rev_tag")
    files = relationship("File", back_populates="post_revision")

    __ts_vector__ = create_tsvector(
        title,
        summary,
        content
    )

    __table_args__ = (
        db.Index(
            'idx_post_revision_fulltextsearch',
            __ts_vector__,
            postgresql_using='gin'
        ),
    )


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)

    post_revisions = relationship("PostRevision", secondary="post_rev_tag")

    def __repr__(self):
        return f"<Tag '{self.name}'>"


class PostRev_Tag(db.Model):
    __tablename__ = "post_rev_tag"

    revision_id = db.Column(db.Integer,
                            db.ForeignKey("post_revisions.id"),
                            primary_key=True)

    tag_id = db.Column(db.Integer,
                       db.ForeignKey("tags.id"),
                       primary_key=True)

    revision = relationship(PostRevision)
    tag = relationship(Tag)

    def __repr__(self):
        return f"<Post_Tag {self.revision} <-> {self.tag}>"


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    filename = db.Column(db.String(300))

    post_rev_id = db.Column(db.Integer,
                            db.ForeignKey("post_revisions.id"),
                            nullable=False)

    post_revision = relationship('PostRevision', back_populates='files')

    def __repr__(self):
        return f"<File '{self.name}'>"
