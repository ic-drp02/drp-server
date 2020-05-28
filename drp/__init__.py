from flask import Flask, escape, request

from . import config
from .db import db
from .posts import posts


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

    # Register blueprints with app
    app.register_blueprint(posts)

    @app.route("/")
    def hello():
        name = request.args.get("name", "World")
        return f"Hello, {escape(name)}!"

    return app
