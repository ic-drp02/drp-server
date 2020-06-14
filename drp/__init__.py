from flask import Flask, escape, request
from flask_restful import Api

from . import config, api as res
from .db import db
from .mail import mail
from .swag import swag


def init_cli(app):
    from . import cli
    with app.app_context():
        app.cli.add_command(cli.seed)
        app.cli.add_command(cli.create_user)
        app.cli.add_command(cli.delete_user)


def init_api(app):
    api = Api(app)

    api.add_resource(res.PostResource, "/api/posts/<int:id>")
    api.add_resource(res.PostListResource, "/api/posts")
    api.add_resource(res.RevisionResource, "/api/revisions/<int:id>")

    api.add_resource(res.PostSearchResource,
                     "/api/search/posts/<string:searched>")

    api.add_resource(res.TagResource, "/api/tags/<int:id>")
    api.add_resource(res.TagListResource, "/api/tags")

    api.add_resource(res.FileResource, '/api/files/<int:id>')
    api.add_resource(res.FileListResource, "/api/files")

    api.add_resource(res.RawFileViewResource, '/api/rawfiles/view/<int:id>')
    api.add_resource(res.RawFileDownloadResource,
                     '/api/rawfiles/download/<int:id>')

    api.add_resource(res.SubjectResource, "/api/questions/subjects/<int:id>")
    api.add_resource(res.SubjectListResource, "/api/questions/subjects")

    api.add_resource(res.QuestionResource, "/api/questions/<int:id>")
    api.add_resource(res.QuestionListResource, "/api/questions")

    api.add_resource(res.SiteResource, "/api/sites/<int:id>")
    api.add_resource(res.SiteListResource, "/api/sites")

    app.register_blueprint(res.questions, url_prefix="/api/questions")
    app.register_blueprint(res.notifications, url_prefix="/api/notifications")
    app.register_blueprint(res.users, url_prefix="/api/users")

    app.register_blueprint(res.auth, url_prefix="/auth")


def create_app(test_config=None):
    app = Flask(__name__)

    # Load configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
    app.config["SQLALCHEMY_ECHO"] = config.IS_DEV_ENV
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["ALLOWED_FILE_EXTENSIONS"] = config.ALLOWED_FILE_EXTENSIONS

    app.config["MAIL_SERVER"] = config.MAIL_SERVER
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = config.MAIL_USERNAME
    app.config["MAIL_PASSWORD"] = config.MAIL_PASSWORD
    app.config["MAIL_DEFAULT_SENDER"] = config.MAIL_DEFAULT_SENDER

    if test_config is not None:
        app.config.update(test_config)

    # Register app with database
    db.init_app(app)

    # Run database migrations
    # with app.app_context():
    #     import flask_migrate
    #     flask_migrate.upgrade()

    mail.init_app(app)

    # Register cli commands
    init_cli(app)

    # Initialise flasggr
    swag.init_app(app)

    # Register api routes
    init_api(app)

    @app.route("/")
    def hello():
        name = request.args.get("name", "World")
        return f"Hello, {escape(name)}!"

    return app
