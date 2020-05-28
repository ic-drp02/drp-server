from flask import request
from flask_restful import Resource, abort

from ..db import db
from ..models import Post


class PostResource(Resource):

    def get(self, id):
        """
        Gets a single post by id.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          200:
            schema:
              $ref: "#/definitions/Post"
          404:
            description: Not found
        """
        post = Post.query.filter(Post.id == id).one_or_none()
        return post.serialize() if post is not None else abort(404)

    def delete(self, id):
        """
        Deletes a single post by id.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        post = Post.query.filter(Post.id == id).one_or_none()

        if post is None:
            return abort(404)

        db.session.delete(post)
        db.session.commit()

        return '', 204


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
        parameters:
          - in: body
            name: post
            schema:
              type: object
              properties:
                title:
                  type: string
                  required: true
                  maxLength: 120
                summary:
                  type: string
                  required: false
                  maxLength: 200
                content:
                  required: true
                  type: string
        responses:
          200:
            schema:
              $ref: "#/definitions/Post"
        """
        body = request.json

        title = body["title"]
        summary = body.get("summary")
        content = body["content"]

        def error_message(name, count):
            return f"{name} must not be more than {count} characters."

        if len(title) > 120:
            return abort(400, message=error_message("Title", 120))

        if summary is not None and len(summary) > 120:
            return abort(400, message=error_message("Summary", 200))

        post = Post(title=title, summary=summary, content=content)

        db.session.add(post)
        db.session.commit()

        return post.serialize()
