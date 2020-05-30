from flask import Flask, escape, request
from flask_restful import Api

from . import config, api as res
from .db import db
from .swag import swag


def create_app(test_config=None):
    app = Flask(__name__)

    # Load configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
    app.config["SQLALCHEMY_ECHO"] = config.IS_DEV_ENV
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config is not None:
        app.config.update(test_config)

    # Register app with database
    db.init_app(app)

    # Run database migrations
    # with app.app_context():
    #     import flask_migrate
    #     flask_migrate.upgrade()

    # Initialise flasggr
    swag.init_app(app)

    # Register api routes
    api = Api(app)

    api.add_resource(res.PostResource, "/posts/<int:id>")
    api.add_resource(res.PostListResource, "/posts")

    api.add_resource(res.TagResource, "/tags/<int:id>")
    api.add_resource(res.TagListResource, "/tags")

    @app.route("/")
    def hello():
        name = request.args.get("name", "World")
        return f"Hello, {escape(name)}!"

    return app
