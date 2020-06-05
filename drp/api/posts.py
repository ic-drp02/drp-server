import pytz

import os
import werkzeug
import secrets
from datetime import datetime

from flask import request, current_app
from flask_restful import Resource, abort

from ..db import db
from ..models import Post, Tag, File
from ..swag import swag

from .tags import serialize_tag
from .files import serialize_file, allowed_file


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
          $ref: "#/definitions/Tag"
      files:
        type: array
        items:
          $ref: "#/definitions/File"
    """
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "content": post.content,
        "created_at": post.created_at.astimezone(pytz.utc).isoformat(),
        "tags": [serialize_tag(tag) for tag in post.tags],
        "files": [serialize_file(file) for file in post.files]
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

        for file in post.files:
            os.remove(os.path.join(
                current_app.config['UPLOAD_FOLDER'], file.filename))

            db.session.delete(file)

        db.session.delete(post)
        db.session.commit()

        return '', 204


class PostListResource(Resource):

    def get(self):
        """
        Gets a list of all posts.
        ---
        parameters:
          - in: query
            name: sort
            type: string
            enum:
              - views
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"

        """
        sort = request.args.get("sort")

        if sort == "views":
            posts = Post.query.order_by(Post.views.desc())
        else:
            posts = Post.query.all()

        return [serialize_post(post) for post in posts]

    def post(self):
        """
        Creates a new post.
        ---
        parameters:
          - in: formData
            name: title
            type: string
            required: true
            maxLength: 120
            description: The title of the post.
          - in: formData
            name: summary
            type: string
            required: true
            maxLength: 200
            description: A short summary of the post.
          - in: formData
            name: content
            type: string
            required: true
          - in: formData
            name: tags
            required: false
            type: array
            description: The tags associated with the post.
            items:
              type: string
          - in: formData
            name: files
            type: array
            description: The files attached to the post.
            items:
              type: file
          - in: formData
            type: array
            name: names
            description: The names of files attached to the post.
            items:
              type: string
        responses:
          200:
            schema:
              $ref: "#/definitions/Post"
        """
        title = request.form.get('title')
        summary = request.form.get('summary')
        content = request.form.get('content')
        tag_names = request.form.getlist('tags')
        files = request.files.getlist('files')
        names = request.form.getlist('names')

        if title is None or summary is None or content is None:
            return abort(400,
                         message="`title`, `summary` and `content` \
                         fields are required.")

        if title == "":
            return abort(400, message="`title` field cannot be empty.")

        def error_message(name, count):
            return f"`{name}` must not be more than {count} characters."

        if len(title) > 120:
            return abort(400, message=error_message("title", 120))

        if summary is not None and len(summary) > 200:
            return abort(400, message=error_message("summary", 200))

        tags = None

        if len(tag_names) != 0:
            tags = Tag.query.filter(Tag.name.in_(tag_names))
            if tags.count() < len(tag_names):
                return abort(400, message="Invalid tags - all tags must be"
                             " predefined through the tags api.")

        tags = tags.all() if tags is not None else []

        if len(files) != len(names):
            return abort(400, message="The number of files must match "
                         "the number of supplied names.")

        for name in names:
            if len(name) > 200:
                return abort(400, message=error_message("file name", 200))

            if not allowed_file(name,
                                current_app.config["ALLOWED_FILE_EXTENSIONS"]):
                return abort(400, message=f"The file extension of {name} is "
                             "not allowed for security reasons. If "
                             "you believe that this file type is safe "
                             "to upload, contact the developer.")

        post = Post(title=title, summary=summary,
                    content=content, tags=tags)
        db.session.add(post)

        # Save files
        for i in range(0, len(files)):
            # Prefix file name with current time and random number to allow
            # files with the same name
            filename = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f_') + \
                str(secrets.randbelow(10000000000)) + "_" + \
                werkzeug.utils.secure_filename(names[i])

            path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], filename)
            if (os.path.isfile(path)):
                return abort(422, message="An unexpected file collision "
                             "ocurred. This error was thought to be "
                             "impossible to arise in practice. Please "
                             "contact the developer quoting this error "
                             "message.")
            files[i].save(path)

            file = File(name=names[i], filename=filename, post=post)

            db.session.add(file)

        db.session.commit()

        return serialize_post(post)


class PostStatsResource(Resource):

    def get(self, id):
        post = Post.query.filter(Post.id == id).one_or_none()

        if post is None:
            return abort(404)

        return {
            "views": post.views,
            "votes": post.votes,
        }

    def put(self, id):
        post = Post.query.filter(Post.id == id).one_or_none()

        if post is None:
            return abort(404)

        body = request.json

        views = body.get("views")
        votes = body.get("votes")

        if views is not None:
            if not isinstance(views, int):
                return abort(400, message="`views` must be an integer")
            post.views = views

        if votes is not None:
            if not isinstance(votes, int):
                return abort(400, message="`votes` must be an integer")
            post.votes = votes

        db.session.commit()

        return {
            "views": post.views,
            "votes": post.votes,
        }
