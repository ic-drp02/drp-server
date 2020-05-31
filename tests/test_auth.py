import json
from argon2 import PasswordHasher

from drp.models import User


def create_user(app, db, username, password):
    with app.app_context():
        hasher = PasswordHasher()
        hash = hasher.hash(password)

        user = User(username=username, password_hash=hash)

        db.session.add(user)
        db.session.commit()


def test_authentication_for_valid_username_and_password(app, db):
    username = "username"
    password = "some secure password, but who am I kidding :("
    create_user(app, db, username, password)

    with app.test_client() as client:
        credentials = {
            "username": username,
            "password": password
        }

        response = client.post("/api/authenticate", json=credentials)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "token" in data


def test_authentication_for_invalid_username_and_password(app, db):
    username = "username"
    password = "some secure password, but who am I kidding :("
    create_user(app, db, username, password)

    with app.test_client() as client:
        credentials = {
            "username": "rando69",
            "password": password
        }

        response = client.post("/api/authenticate", json=credentials)

        assert "401" in response.status

    with app.test_client() as client:
        credentials = {
            "username": username,
            "password": "password123"
        }

        response = client.post("/api/authenticate", json=credentials)

        assert "401" in response.status
