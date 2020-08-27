"""Separate posts into posts and revisions

Revision ID: ef0a345b0640
Revises: 63246e4d9192
Create Date: 2020-06-25 15:37:09.352559

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = 'ef0a345b0640'
down_revision = '63246e4d9192'
branch_labels = None
depends_on = None

Base = declarative_base()


class Post_old(Base):
    __tablename__ = "posts"

    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.String(120))
    summary = sa.Column(sa.String(200))
    content = sa.Column(sa.Text())
    is_guideline = sa.Column(sa.Boolean())
    is_current = sa.Column(sa.Boolean())
    post_id = sa.Column(sa.Integer)
    created_at = sa.Column(sa.DateTime(timezone=True))


class Post_new_1(Base):
    __tablename__ = "posts_new"

    id = sa.Column(sa.Integer(), primary_key=True)
    is_guideline = sa.Column(sa.Boolean())
    latest_rev_id = sa.Column(sa.Integer())


class PostRevision(Base):
    __tablename__ = "post_revisions"

    id = sa.Column(sa.Integer, primary_key=True)
    post_id = sa.Column(sa.Integer, sa.ForeignKey("posts_new.id"))

    title = sa.Column(sa.Text(), nullable=False)
    summary = sa.Column(sa.Text())
    content = sa.Column(sa.Text())

    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)


class Post_Tag_old(Base):
    __tablename__ = "post_tag"

    post_id = sa.Column(sa.Integer,
                        sa.ForeignKey("posts.id"),
                        primary_key=True)

    tag_id = sa.Column(sa.Integer,
                       sa.ForeignKey("tags.id"),
                       primary_key=True)


class PostRev_Tag(Base):
    __tablename__ = "post_rev_tag"

    revision_id = sa.Column(sa.Integer,
                            sa.ForeignKey("post_revisions.id"),
                            primary_key=True)

    tag_id = sa.Column(sa.Integer,
                       sa.ForeignKey("tags.id"),
                       primary_key=True)


class Tag(Base):
    __tablename__ = "tags"

    id = sa.Column(sa.Integer, primary_key=True)


class File_new(Base):
    __tablename__ = "files"

    id = sa.Column(sa.Integer, primary_key=True)

    post_id = sa.Column(sa.Integer,
                        sa.ForeignKey("posts.id"))

    post_rev_id = sa.Column(sa.Integer,
                            sa.ForeignKey("post_revisions.id"))


class Question(Base):
    __tablename__ = "questions"

    id = sa.Column(sa.Integer, primary_key=True)

    post_id = sa.Column(sa.Integer)
    post_id_new = sa.Column(sa.Integer,
                            sa.ForeignKey("posts_new.id"))


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    # Create the new posts table
    op.create_table("posts_new",
                    sa.Column("id", sa.Integer(), nullable=False),
                    sa.Column("is_guideline", sa.Boolean(), nullable=False),
                    sa.Column("latest_rev_id", sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint("id")
                    )

    # Create the post revisions table
    op.create_table('post_revisions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('post_id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.Text(), nullable=False),
                    sa.Column('summary', sa.Text(), nullable=False),
                    sa.Column('content', sa.Text(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=False),
                              server_default=sa.text('now()'), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['post_id'], ['posts_new.id'], ondelete="CASCADE"),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create linking table for revisions <-> tags
    op.create_table('post_rev_tag',
                    sa.Column('revision_id', sa.Integer(), nullable=False),
                    sa.Column('tag_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['revision_id'], ['post_revisions.id'], ),
                    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
                    sa.PrimaryKeyConstraint('revision_id', 'tag_id')
                    )

    op.add_column('files', sa.Column(
        'post_rev_id', sa.Integer(), nullable=True))
    op.drop_constraint('files_post_id_fkey', 'files', type_='foreignkey')

    op.add_column("questions", sa.Column(
        "post_id_new", sa.Integer(), nullable=True))
    op.drop_constraint("questions_post_id_fkey",
                       "questions", type_="foreignkey")

    # Copy existing posts to the new tables
    for post in session.query(Post_old).filter(Post_old.is_current).all():
        # Create post entry for the latest version of this post
        new_post = Post_new_1(is_guideline=post.is_guideline)
        session.add(new_post)
        session.commit()
        # Create revision entries for each version of this post
        for p in session.query(Post_old).filter(
                Post_old.post_id == post.post_id).all():
            revision = PostRevision(post_id=new_post.id, title=p.title,
                                    summary=p.summary, content=p.content,
                                    created_at=p.created_at)
            session.add(revision)
            session.commit()
            # Copy over all the tags
            for post_tag in session.query(Post_Tag_old).filter(
                    Post_Tag_old.post_id == p.id):
                rev_tag = PostRev_Tag(revision_id=revision.id,
                                      tag_id=post_tag.tag_id)
                session.add(rev_tag)
            session.commit()
            # Update references from files
            for file in session.query(File_new).filter(
                    File_new.post_id == p.id):
                file.post_rev_id = revision.id
            session.commit()
            # Link latest version back to the owning post
            if p.is_current:
                new_post.latest_rev_id = revision.id
                session.commit()
        # Update references from questions
        for q in session.query(Question).filter(Question.post_id == post.id):
            q.post_id_new = new_post.id
            session.commit()

    op.drop_table("post_tag")
    op.drop_column("files", "post_id")
    op.alter_column("files", "post_rev_id", nullable=False)
    op.drop_column("questions", "post_id")
    op.alter_column("questions", "post_id_new", new_column_name="post_id")

    op.drop_table("posts")
    op.rename_table("posts_new", "posts")

    op.create_foreign_key(None, 'posts', 'post_revisions',
                          ['latest_rev_id'], ['id'])

    op.create_foreign_key(None, 'files',
                          'post_revisions', ['post_rev_id'], ['id'])

    op.create_foreign_key("post_revisions_post_id_fkey", 'questions',
                          'posts', ['post_id'], ['id'])


def downgrade():
    raise Exception("Not implemented :(")
