from flask import request
from flask_restful import Resource

from ..db import db
from ..models.post import Post


class PostListResource(Resource):
    def get(self):
        return [post.serialize() for post in Post.query.all()]

    def post(self):
        body = request.json

        title = body["title"]
        summary = body.get("summary")
        content = body["content"]

        post = Post(title=title, summary=summary, content=content)

        db.session.add(post)
        db.session.commit()

        return post.serialize()
