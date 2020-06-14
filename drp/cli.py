import click
import json
import flask_migrate
from flask.cli import with_appcontext

from .db import db
from .models import Tag, Post, Site, Subject, Grade, Question, User, UserRole


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

    tags = data.get("tags")
    if tags:
        db.session.add_all([Tag(name=tag) for tag in tags])

    posts = data.get("posts")
    if posts:
        def create_post(post):
            tags = []
            if "tags" in post:
                tags = [Tag.query.filter(Tag.name == tag).one()
                        for tag in post["tags"]]
            return Post(title=post.get("title"), summary=post.get("summary"),
                        content=post.get("content"), tags=tags)

        posts = map(create_post, posts)
        db.session.add_all(posts)

    sites = data.get("sites")
    if sites:
        db.session.add_all([Site(name=site) for site in sites])

    subjects = data.get("questionSubjects")
    if subjects:
        db.session.add_all([Subject(name=subject) for subject in subjects])

    questions = data.get("questions")
    if questions:
        def create_question(question):
            site = Site.query.filter(Site.name == question.get("site")).one()
            grade = Grade[question.get("grade").upper()]
            subject = Subject.query.filter(
                Subject.name == question.get("subject")).one()
            return Question(site=site, grade=grade,
                            specialty=question.get("specialty"),
                            subject=subject, text=question.get("text"))

        questions = map(create_question, questions)
        db.session.add_all(questions)

    db.session.commit()


@click.command("create_user", help="Create a new user.")
@click.argument("email")
@click.argument("password")
@click.option("-r", "--role",
              type=click.Choice(["normal", "admin"], case_sensitive=False),
              default="normal")
@with_appcontext
def create_user(email, password, role):
    from argon2 import PasswordHasher

    hasher = PasswordHasher()
    hash = hasher.hash(password)

    user = User(email=email, password_hash=hash,
                role=UserRole.ADMIN if role == "admin" else UserRole.NORMAL,
                confirmed=True)

    db.session.add(user)
    db.session.commit()


@click.command("delete_user", help="Delete a user.")
@click.argument("email")
@with_appcontext
def delete_user(email):
    user = User.query.filter(User.email == email).one_or_none()

    if not user:
        print("Not found")

    else:
        db.session.delete(user)
        db.session.commit()
