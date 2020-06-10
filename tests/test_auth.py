import json
from argon2 import PasswordHasher

from drp.models import User


def create_user(app, db, email, password):
    with app.app_context():
        hasher = PasswordHasher()
        hash = hasher.hash(password)

        user = User(email=email, password_hash=hash, confirmed=True)

        db.session.add(user)
        db.session.commit()


def test_authentication_for_valid_email_and_password(app, db):
    email = "test@nhs.net"
    password = "some secure password, but who am I kidding :("
    create_user(app, db, email, password)

    with app.test_client() as client:
        credentials = {
            "email": email,
            "password": password
        }

        response = client.post("/auth/authenticate", json=credentials)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "token" in data


def test_authentication_for_invalid_email_and_password(app, db):
    email = "test@nhs.net"
    password = "some secure password, but who am I kidding :("
    create_user(app, db, email, password)

    with app.test_client() as client:
        credentials = {
            "email": "rando69@nhs.net",
            "password": password
        }

        response = client.post("/auth/authenticate", json=credentials)

        assert "401" in response.status

    with app.test_client() as client:
        credentials = {
            "email": email,
            "password": "password123"
        }

        response = client.post("/auth/authenticate", json=credentials)

        assert "401" in response.status
