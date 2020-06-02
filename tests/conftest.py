import os
import pytest

from drp import create_app
from drp.db import db as _db


@pytest.fixture
def app():
    options = {"TEST": True}
    db = os.environ.get("TEST_DATABASE_URI")

    if db is not None:
        options["SQLALCHEMY_DATABASE_URI"] = db

    return create_app(options)


@pytest.fixture
def db(app):
    with app.app_context():
        _db.create_all()

    yield _db

    with app.app_context():
        _db.drop_all()


@pytest.fixture(autouse=True)
def handle_upload(app):
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(app.root_path), "tests", "output")

    yield

    output_path = os.path.join(os.path.dirname(
        app.root_path), "tests", "output")
    filenames = os.listdir(output_path)

    for filename in filenames:
        if filename != "README.md" and filename != ".pytest_cache":
            os.remove(os.path.join(output_path, filename))
