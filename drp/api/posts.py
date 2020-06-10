import pytz

import os
import werkzeug
import secrets
from datetime import datetime

from flask import request, current_app
from flask_restful import Resource, abort

from collections import deque

from ..db import db
from ..models import Post, Tag, File
from ..swag import swag

from .. import notifications
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
      is_guideline:
        type: boolean
      superseding:
        type: integer
      superseded_by:
        type:integer
    """
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "content": post.content,
        "is_guideline": post.is_guideline,
        "superseding": post.superseding_id,
        "superseded_by": post.superseded_by.id
        if post.superseded_by is not None else None,
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
            try:
                os.remove(os.path.join(
                    current_app.config['UPLOAD_FOLDER'], file.filename))
            except OSError as e:
                print("Could not delete file, " + repr(e))

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
          - name: include_old
            in: query
            type: boolean
            required: false
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"

        """
        include_old = request.args.get("include_old")

        query = Post.query
        if include_old != "true":
            query = query.filter(Post.superseded_by == None)
        return [serialize_post(post)
                for post in query.order_by(Post.created_at.desc())]

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
          - in: formData
            type: boolean
            name: is_guideline
            description: Indicates whether a post is a guideline.
          - in: formData
            type: integer
            name: superseding
            description: ID of older version of the guideline.
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
        is_guideline = request.form.get('is_guideline')
        superseding = request.form.get('superseding')

        # Check that required fields are present
        if title is None or summary is None or content is None:
            return abort(400,
                         message="`title`, `summary` and `content` \
                         fields are required.")

        if title == "":
            return abort(400, message="`title` field cannot be empty.")

        # Check that no field exceeds permitted length
        def error_message(name, count):
            return f"`{name}` must not be more than {count} characters."

        if len(title) > 120:
            return abort(400, message=error_message("title", 120))

        if summary is not None and len(summary) > 200:
            return abort(400, message=error_message("summary", 200))

        # Check that tags are valid
        tags = None

        if len(tag_names) != 0:
            tags = Tag.query.filter(Tag.name.in_(tag_names))
            if tags.count() < len(tag_names):
                return abort(400, message="Invalid tags - all tags must be"
                             " predefined through the tags api.")

        tags = tags.all() if tags is not None else []

        # Check that files and the associated names are valid
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

        # Check that the fields for posting guidelines are valid
        if is_guideline is not None and is_guideline != "false" \
                and is_guideline != "true":
            return abort(400, message="The value is_guideline="
                         f"{is_guideline} is invalid.")

        if is_guideline == "true" and superseding is not None:
            old_post = Post.query.filter(Post.id == superseding) \
                .one_or_none()
            if old_post is None:
                return abort(400, message="Invalid old post ID.")
            if old_post.superseded_by is not None:
                return abort(400, message="Selected old post has already "
                             "been superseded.")
            post = Post(title=title, summary=summary, content=content,
                        is_guideline=True, superseding=old_post, tags=tags)
        elif is_guideline == "true":
            post = Post(title=title, summary=summary, content=content,
                        is_guideline=True, tags=tags)
        else:
            post = Post(title=title, summary=summary, content=content,
                        is_guideline=False, tags=tags)
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

        notifications.broadcast(title, summary, data={"id": post.id})

        return serialize_post(post)


class GuidelineListResource(Resource):

    def get(self):
        """
        Gets a list of all guidelines.
        ---
        parameters:
          - name: include_old
            in: query
            type: boolean
            required: false
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"

        """
        include_old = request.args.get("include_old")

        query = Post.query.filter(Post.is_guideline)
        if include_old != "true":
            query = query.filter(Post.superseded_by == None)
        return [serialize_post(post)
                for post in query.order_by(Post.created_at.desc())]


class GuidelineResource(Resource):

    def get(self, id):
        """
        Gets a list of all revisions of a guideline.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
          - name: reverse
            in: query
            type: boolean
            required: false
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"
          404:
            description: Not found
        """

        post = Post.query.filter(Post.id == id).one_or_none()
        if post is None or not post.is_guideline:
            return abort(404)

        d = deque([post])

        while d[0].superseding is not None:
            post = d[0].superseding
            d.appendleft(post)

        while d[-1].superseded_by is not None:
            post = d[-1].superseded_by
            d.append(post)

        reverse = request.args.get("reverse")

        if reverse == "true":
            d.reverse()

        return [serialize_post(post)
                for post in d]
