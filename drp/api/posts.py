import pytz

from flask import request
from flask_restful import Resource, abort

from ..db import db
from ..models import Post, Tag
from ..swag import swag


@swag.definition("Post")
def serialize_post(post):
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
      tags:
        type: array
        items:
          type: string
    """
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "content": post.content,
        "created_at": post.created_at.astimezone(pytz.utc).isoformat(),
        "tags": [tag.serialize() for tag in post.tags]
    }


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
        return serialize_post(post) if post is not None else abort(404)

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
        return [serialize_post(post) for post in Post.query.all()]

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
                tags:
                  required: false
                  type: array
                  items:
                    type: string
        responses:
          200:
            schema:
              $ref: "#/definitions/Post"
        """
        body = request.json

        title = body.get("title")
        summary = body.get("summary")
        content = body.get("content")
        tag_names = body.get("tags") or []

        if title is None or content is None:
            return abort(400,
                         message="`title` and `content` fields are required.")

        def error_message(name, count):
            return f"`{name}` must not be more than {count} characters."

        if len(title) > 120:
            return abort(400, message=error_message("title", 120))

        if summary is not None and len(summary) > 120:
            return abort(400, message=error_message("summary", 200))

        tags = None

        if len(tag_names) != 0:
            tags = Tag.query.filter(Tag.name.in_(tag_names))
            if tags.count() < len(tag_names):
                return abort(400, message="Invalid tags - all tags must be"
                             " predefined through the tags api.")

        tags = tags.all() if tags is not None else []

        post = Post(title=title, summary=summary,
                    content=content, tags=tags)

        db.session.add(post)
        db.session.commit()

        return serialize_post(post)
