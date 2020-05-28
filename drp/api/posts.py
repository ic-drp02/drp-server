from flask import request
from flask_restful import Resource

from ..db import db
from ..models.post import Post


class PostListResource(Resource):

    def get(self):
        """
        Gets a list of all posts.
        ---
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"

        """
        return [post.serialize() for post in Post.query.all()]

    def post(self):
        """
        Creates a new post.
        ---
        responses:
          200:
            schema:
              $ref: "#/definitions/Post"
        """
        body = request.json

        title = body["title"]
        summary = body.get("summary")
        content = body["content"]

        post = Post(title=title, summary=summary, content=content)

        db.session.add(post)
        db.session.commit()

        return post.serialize()
