from flask import Blueprint, jsonify
from .models import Post

posts = Blueprint("posts", __name__)


@posts.route("/posts")
def get_all():
    posts = [post.serialize() for post in Post.query.all()]
    return jsonify(posts)
