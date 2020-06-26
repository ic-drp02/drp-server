import pytz
import os
import werkzeug
import secrets
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import joinedload

from .. import notifications
from ..models import Post, PostRevision, Tag, PostRev_Tag, File, Question
from ..db import db

from .utils import abort
from .files import allowed_file

posts = Blueprint("posts", __name__)


def serialize_tag(tag):
    return {
        "id": tag.id,
        "name": tag.name
    }


def serialize_file(f):
    return {
        "id": f.id,
        "name": f.name,
        "filename": f.filename
    }


def serialize_revision(rev):
    return {
        "id": rev.id,
        "title": rev.title,
        "summary": rev.summary,
        "content": rev.content,
        "created_at": rev.created_at.astimezone(pytz.utc).isoformat(),
        "tags": [serialize_tag(tag) for tag in rev.tags],
        "files": [serialize_file(f) for f in rev.files]
    }


def serialize_post(post):
    return {
        "id": post.id,
        "type": "guideline" if post.is_guideline else "update",
        "latest_revision": serialize_revision(post.latest_rev)
    }


@posts.route("/", methods=["GET", "POST"])
def all_posts():
    if request.method == "GET":
        return get_posts()

    elif request.method == "POST":
        return create_post()


def get_posts():
    ids = request.args.getlist("ids")
    type = request.args.get("type")
    tag = request.args.get("tag")
    page = request.args.get("page")
    per_page = request.args.get("per_page")

    query = Post.query.join(Post.latest_rev).options(
        joinedload("latest_rev").options(
            joinedload("tags"),
            joinedload("files")))

    # Filter by id
    if len(ids) == 1 and ',' in ids[0]:
        ids = ids[0].split(',')

    if len(ids) == 1 and ids[0] == "":
        return jsonify([])

    if not all(id.isdigit() for id in ids):
        abort(400, message="IDs must be integers")

    if len(ids) > 0:
        query = query.filter(Post.id.in_(ids))

    # Filter by type
    if type == "update":
        query = query.filter(Post.is_guideline == False)  # noqa

    elif type == "guideline":
        query = query.filter(Post.is_guideline == True)  # noqa

    elif type and type != "any":
        abort(400, "type must be one of `any`, `update` or `guideline`")

    # Filter by tag name
    if tag:
        tag = Tag.query.filter(Tag.name == tag).one_or_none()
        if not tag:
            abort(400, f"the tag `{tag}` does not exist")
        query = query.join(PostRev_Tag).join(
            Tag).filter(Tag.id == tag.id)

    query = query.join(Post.latest_rev).order_by(
        PostRevision.created_at.desc())

    # Pagination
    if per_page:
        if not page:
            page = 0
        else:
            page = int(page)

        per_page = int(per_page)
        query = query.limit(per_page).offset(page * per_page)

    return jsonify([serialize_post(post) for post in query])


def create_post():
    # return serialize_post(post)
    title = request.form.get("title")
    summary = request.form.get("summary")
    content = request.form.get("content")
    tag_names = request.form.getlist("tags")
    type = request.form.get("type")
    resolves = request.form.getlist("resolves")
    files = request.form.getlist("files")
    names = request.form.getlist("file_names")

    validate_rev_data(title, summary, content, files, names)

    tags = validate_rev_tags(tag_names)
    resolved_questions = validate_rev_resolved_questions(resolves)

    # # Check that type is valid
    if type is not None and type != "update" and type != "guideline":
        abort(400, message="type must be one of `update` \
            or `guideline`")

    post = Post(is_guideline=type == "guideline")
    db.session.add(post)
    db.session.commit()

    revision = create_rev(title, summary, content, post, tags)

    link_questions_to_post(resolved_questions, post)
    save_files_for_revision(files, names, revision)

    db.session.commit()

    notify_resolved_questions(resolved_questions, post)
    notify_new_post_rev(revision)

    return jsonify(serialize_post(post))


@posts.route("/<int:id>", methods=["GET", "DELETE"])
def single_post(id):
    if request.method == "GET":
        return get_post(id)

    elif request.method == "DELETE":
        return delete_post(id)


def get_post(id):
    post = Post.query.filter(Post.id == id).one_or_none()

    if post is None:
        abort(404)

    return jsonify(serialize_post(post))


def delete_post(id):
    for question in Question.query.filter(Question.post_id == id):
        question.resolved_by = None

    rows_deleted = Post.query.filter(Post.id == id).delete()

    if rows_deleted == 0:
        abort(404)

    db.session.commit()

    return jsonify({"message": "deleted"}), 204


@posts.route("/<int:id>/revisions", methods=["GET", "POST"])
def post_revisions(id):
    post = Post.query.filter(Post.id == id).one_or_none()

    if post is None:
        abort(404)

    if request.method == "GET":
        return get_post_revisions(post)

    elif request.method == "POST":
        return create_post_revision(post)


def get_post_revisions(post):
    order = request.args.get("order")
    query = PostRevision.query.filter(PostRevision.post_id == post.id)

    if not order or order == "desc":
        query = query.order_by(PostRevision.created_at.desc())

    elif order == "asc":
        query = query.order_by(PostRevision.created_at.asc())

    else:
        abort(400, message="order must be one of `asc` or `desc`")

    return jsonify([serialize_revision(rev) for rev in query])


def create_post_revision(post):
    title = request.form.get("title")
    summary = request.form.get("summary")
    content = request.form.get("content")
    tag_names = request.form.getlist("tags")
    resolves = request.form.getlist("resolves")
    files = request.form.getlist("files")
    names = request.form.getlist("file_names")

    validate_rev_data(title, summary, content, files, names)

    tags = validate_rev_tags(tag_names)
    resolved_questions = validate_rev_resolved_questions(resolves)

    revision = create_rev(title, summary, content, post, tags)

    link_questions_to_post(resolved_questions, post)
    save_files_for_revision(files, names, revision)

    db.session.commit()

    notify_resolved_questions(resolved_questions, post)
    notify_new_post_rev(revision)

    return jsonify(serialize_revision(revision))


@posts.route("/<int:post_id>/revisions/<int:revision_id>",
             methods=["GET", "DELETE"])
def post_revision(post_id, revision_id):
    post = Post.query.filter(Post.id == post_id).one_or_none()

    if post is None:
        abort(404)

    revision = PostRevision.query.filter(
        PostRevision.id == revision_id).one_or_none()

    if revision is None:
        abort(404)

    if request.method == "GET":
        return get_post_revision(post, revision)

    elif request.method == "DELETE":
        return delete_post_revision(post, revision)


def get_post_revision(post, revision):
    return jsonify(serialize_revision(revision))


def delete_post_revision(post, revision):
    # If this is the only revision, delete the whole post
    if len(post.revisions) == 1:
        # Unlink any questions that were resolved by the post
        for question in Question.query.filter(Question.post_id == id):
            question.resolved_by = None

        Post.query.filter(Post.id == post.id).delete()

    else:
        # If this is currently the latest revision,
        # set the post's latest revision to the previous
        # revision
        if post.latest_rev.id == revision.id:
            post.latest_rev = PostRevision.query \
                .filter(PostRevision.post_id == post.id) \
                .order_by(PostRevision.created_at.desc()) \
                .first()

        # Delete the revision
        PostRevision.query \
            .filter(PostRevision.id == revision.id) \
            .delete()

    db.session.commit()


def validate_rev_data(title, summary, content, files, names):
    # Check that required fields are present
    if title is None or summary is None or content is None:
        abort(400, message="`title`, `summary` and `content` \
            fields are required.")

    if not title:
        abort(400, message="`title` field cannot be empty.")

    # Check that files and the associated names are valid
    if len(files) != len(names):
        abort(400, message="The number of files must match "
              "the number of supplied names.")

    for name in names:
        if len(name) > 200:
            abort(400, message="file name must not be more than 200 \
                characters")

        if not allowed_file(name,
                            current_app.config["ALLOWED_FILE_EXTENSIONS"]):
            abort(400, message=f"The file extension of {name} is "
                  "not allowed for security reasons. If "
                  "you believe that this file type is safe "
                  "to upload, contact the developer.")


def validate_rev_tags(tag_names):
    if len(tag_names) > 0:
        tags = Tag.query.filter(Tag.name.in_(tag_names))

        if tags.count() < len(tag_names):
            abort(400, message="Invalid tags - all tags must be \
                predefined through the tags api.")

        tags = tags.all()

    else:
        tags = []

    return tags


def validate_rev_resolved_questions(resolves):
    resolved_questions = []

    # Check that all resolved questions exist and are not resolved already
    if resolves is not None:
        if len(resolves) == 1 and ',' in resolves[0]:
            resolves = resolves[0].split(',')

        for question_id in resolves:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(400,
                      message=f"Question with id `{question_id}` does \
                        not exist.")

            if question.resolved:
                abort(400,
                      message=f"Question with id `{question_id}` has \
                        already been resolved.")

            resolved_questions.append(question)

    return resolved_questions


def create_rev(title, summary, content, post, tags):
    revision = PostRevision(title=title, summary=summary,
                            content=content, post=post, tags=tags)

    db.session.add(revision)
    db.session.commit()

    post.latest_rev = revision
    db.session.commit()

    return revision


def link_questions_to_post(questions, post):
    for question in questions:
        question.resolved = True
        question.resolved_by = post


def save_files_for_revision(files, names, revision):
    for i in range(0, len(files)):
        # Prefix file name with current time and random number to allow
        # files with the same name
        filename = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f_') + \
            str(secrets.randbelow(10000000000)) + "_" + \
            werkzeug.utils.secure_filename(names[i])

        path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], filename)

        if (os.path.isfile(path)):
            abort(422, message="An unexpected file collision "
                  "ocurred. This error was thought to be "
                  "impossible to arise in practice. Please "
                  "contact the developer quoting this error "
                  "message.")

        files[i].save(path)

        file = File(name=names[i], filename=filename, post_revision=revision)

        db.session.add(file)


def notify_resolved_questions(resolved_questions, post):
    for q in resolved_questions:
        notifications.send_user(
            q.user, "Your question has been resolved",
            q.text, data={"id": post.id, "resolves": q.id})


def notify_new_post_rev(revision):
    notifications.broadcast(revision.title, revision.summary,
                            data={"id": revision.post.id})
