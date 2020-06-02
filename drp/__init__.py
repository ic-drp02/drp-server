from flask import Flask, escape, request
from flask_restful import Api

from . import config, api as res
from .db import db
from .swag import swag

import os


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(
        app.root_path), "uploads")
    app.config['ALLOWED_FILE_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg',
                                             'jpeg', 'gif', 'doc', 'docx',
                                             'xls', 'xlsx', 'ppt', 'pptx',
                                             'ods', 'fods', 'ods', 'fods',
                                             'odp', 'fodp', 'md'}

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

    api.add_resource(res.PostResource, "/api/posts/<int:id>")
    api.add_resource(res.PostListResource, "/api/posts")

    api.add_resource(res.TagResource, "/api/tags/<int:id>")
    api.add_resource(res.TagListResource, "/api/tags")

    api.add_resource(res.FileResource, '/api/files/<int:id>')
    api.add_resource(res.FileListResource, "/api/files")

    api.add_resource(res.RawFileViewResource, '/api/rawfiles/view/<int:id>')
    api.add_resource(res.RawFileDownloadResource,
                     '/api/rawfiles/download/<int:id>')

    @ app.route("/")
    def hello():
        name = request.args.get("name", "World")
        return f"Hello, {escape(name)}!"

    return app
