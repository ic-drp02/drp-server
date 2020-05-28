from flask import Flask, escape, request
from flask_restful import Api

from . import config
from .db import db
from .swag import swag
from .api.posts import PostResource, PostListResource


def create_app(test_config=None):
    app = Flask(__name__)

    # Load configuration
    if test_config is None:
        app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
        app.config["SQLALCHEMY_ECHO"] = config.IS_DEV_ENV
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    else:
        app.config.from_mapping(test_config)

    # Register app with database
    db.init_app(app)

    # Initialise flasggr
    swag.init_app(app)

    # Register api routes
    api = Api(app)
    api.add_resource(PostResource, "/posts/<int:id>")
    api.add_resource(PostListResource, "/posts")

    @app.route("/")
    def hello():
        name = request.args.get("name", "World")
        return f"Hello, {escape(name)}!"

    return app
