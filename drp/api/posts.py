import pytz

import os
import werkzeug
import secrets
from datetime import datetime

from flask import request, current_app
from flask_restful import Resource, abort

from ..db import db
from ..models import Post, Post_Tag, Tag, File, Question
from ..swag import swag

from .. import notifications
from .tags import serialize_tag
from .files import serialize_file, allowed_file


def delete_post(post):
    for file in post.files:
        try:
            os.remove(os.path.join(
                current_app.config['UPLOAD_FOLDER'], file.filename))
        except OSError as e:
            print("Could not delete file, " + repr(e))

        db.session.delete(file)

    db.session.delete(post)


def migrate_resolved_questions(questions, revision):
    for question in questions:
        question.resolved_by = revision


def unresolve_all(questions):
    for question in questions:
        question.resolved = False


def get_current_post_by_id(id):
    return Post.query.filter(Post.is_current & (Post.post_id == id)) \
        .one_or_none()


@swag.definition("Post")
def serialize_post(post):
    """
    Represents a post revision.
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
      is_current:
        type: boolean
      revision_id:
        type: integer
    """
    return {
        "id": post.post_id,
        "title": post.title,
        "summary": post.summary,
        "content": post.content,
        "is_guideline": post.is_guideline,
        "is_current": post.is_current,
        "revision_id": post.id,
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
          - name: include_old
            in: query
            type: boolean
            required: false
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
        include_old = request.args.get("include_old")
        reverse = request.args.get("reverse")

        query = Post.query.filter(Post.post_id == id)

        if include_old != "true":
            query = query.filter(Post.is_current)

        if reverse == "true":
            query = query.order_by(Post.id.desc())
        else:
            query = query.order_by(Post.id)

        posts = query.all()

        if len(posts) == 0:
            return abort(404)

        return [serialize_post(post) for post in posts]

    def delete(self, id):
        """
        Deletes all revisions of a post by ID.
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
        revisions = Post.query.filter(Post.post_id == id).all()

        if len(revisions) == 0:
            return abort(404)

        for revision in revisions:
            delete_post(revision)
            #  Mark associated questions as unresolved
            unresolve_all(revision.resolves)

        db.session.commit()

        return "", 204


class PostListResource(Resource):

    def get(self):
        """
        Gets a list of all posts.
        ---
        parameters:
          - name: guidelines_only
            in: query
            type: boolean
            required: false
          - name: include_old
            in: query
            type: boolean
            required: false
          - name: tag
            in: query
            type: string
            required: false
          - name: page
            in: query
            type: integer
          - name: per_page
            in: query
            type: integer
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"

        """
        guidelines_only = request.args.get("guidelines_only")
        include_old = request.args.get("include_old")
        tag = request.args.get("tag")

        page = request.args.get("page")
        if page is None:
            page = 0
        else:
            page = int(page)

        per_page = request.args.get("per_page")
        if per_page is not None:
            per_page = int(per_page)

        query = Post.query

        if guidelines_only == "true":
            query = query.filter(Post.is_guideline)
        if include_old != "true":
            query = query.filter(Post.is_current)
        if tag is not None:
            query = query.join(Post_Tag).join(Tag).filter(Tag.name == tag)

        query = query.order_by(Post.created_at.desc())

        if per_page is not None:
            query = query.limit(per_page).offset(page * per_page)

        return [serialize_post(post) for post in query]

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
            name: updates
            description: ID of the post that is to be updated.
          - in: formData
            type: array
            name: resolves
            description: The IDs of questions that are resolved by this post.
            items:
              type: number
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
        updates = request.form.get('updates')
        resolves = request.form.getlist('resolves')

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

        # Check that all resolved questions exist and are not resolved already
        resolved_questions = []
        if resolves is not None:
            if len(resolves) == 1 and ',' in resolves[0]:
                resolves = resolves[0].split(',')
            for question_id in resolves:
                question = Question.query.filter(
                    Question.id == question_id).one_or_none()
                if question is None:
                    abort(400, message="One of the resolved questions does "
                          "not exist")
                if question.resolved:
                    abort(
                        400, message="Cannot resolve question that is already "
                        "resolved.")
                resolved_questions.append(question)

        # Add post to the database
        if is_guideline == "true" and updates is not None:
            old_post = get_current_post_by_id(updates)
            if old_post is None or not old_post.is_guideline:
                return abort(400, message="Invalid updated post ID.")
            post = Post(title=title, summary=summary, content=content,
                        is_guideline=True, post_id=updates, tags=tags)
            old_post.is_current = False
            migrate_resolved_questions(old_post.resolves, post)
        else:
            post = Post(title=title, summary=summary, content=content,
                        is_guideline=(is_guideline == "true"), tags=tags)

        # Link resolved questions to the post
        if len(resolved_questions) > 0:
            post.resolves = resolved_questions
            for question in resolved_questions:
                question.resolved = True
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

        if len(resolved_questions) > 0:
            for q in resolved_questions:
                notifications.send_user(
                    q.user, "Your question has been resolved",
                    q.text, data={"id": post.id, "resolves": q.id})

        notifications.broadcast(title, summary, data={"id": post.id})

        return serialize_post(post)


class RevisionResource(Resource):

    def get(self, id):
        """
        Gets a single revision by ID.
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
        revision = Post.query.filter(Post.id == id).one_or_none()

        if revision is None:
            return abort(404)

        return serialize_post(revision)

    def delete(self, id):
        """
        Deletes a revision of a post by ID.
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
        revision = Post.query.filter(Post.id == id).one_or_none()

        if revision is None:
            return abort(404)

        delete_post(revision)

        if revision.is_current:
            revisions = Post.query.filter(
                Post.post_id == revision.post_id) \
                .order_by(Post.id.desc()).all()
            if len(revisions) > 0:
                newest = revisions[0]
                newest.is_current = True

                # Make resolved questions point to the new current revison
                migrate_resolved_questions(revision.resolves, newest)
            else:
                unresolve_all(revision.resolves)

        db.session.commit()

        return "", 204


class PostFetchResource(Resource):

    def get(self):
        """
        Returns a list of posts identified by the supplied IDs.
        ---
        parameters:
          - name: ids
            in: query
            type: array
            items:
              type: number
            required: true
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"
          404:
            description: Not found
        """
        ids = request.args.getlist("ids")

        if len(ids) == 1 and ',' in ids[0]:
            ids = ids[0].split(',')

        if len(ids) == 1 and ids[0] == "":
            return []

        if not all(id.isdigit() for id in ids):
            abort(400, message="IDs must be integers")

        posts = Post.query.filter(
            Post.is_current & Post.post_id.in_(ids)).all()

        return [serialize_post(post) for post in posts]
