import click
import json
import flask_migrate
from flask.cli import with_appcontext

from .db import db
from .models import Tag, Post


@click.command("seed", help="Seed the database with data from a json file.")
@click.option("--drop-all", default=False, is_flag=True,
              help="Delete all existing data and recreate tables.")
@click.argument("filename")
@with_appcontext
def seed(filename, drop_all):
    with open(filename) as f:
        data = json.load(f)

    if drop_all:
        flask_migrate.downgrade(revision="base")
        db.drop_all()
        flask_migrate.upgrade(revision="head")

    if tags := data.get("tags"):
        db.session.add_all([Tag(name=tag) for tag in tags])

    if posts := data.get("posts"):
        def create_post(post):
            tags = []
            if "tags" in post:
                tags = [Tag.query.filter(Tag.name == tag).one()
                        for tag in post["tags"]]
            return Post(title=post.get("title"), summary=post.get("summary"),
                        content=post.get("content"), tags=tags)

        posts = map(create_post, posts)
        db.session.add_all(posts)

    db.session.commit()
