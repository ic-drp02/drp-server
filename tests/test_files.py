import json
import os
from io import BytesIO
from hashlib import sha256

from drp.models import File, Post


def create_test_post(app, db):
    with app.app_context():
        post = Post(title="A title", summary="A summary", content="A content")
        db.session.add(post)
        db.session.commit()
        post_id = post.id
    return (post, post_id)


def create_files(app, db, files):
    with app.app_context():
        for file in files:
            db.session.add(file)
        db.session.commit()


def test_get_all_files(app, db):
    post, post_id = create_test_post(app, db)
    name = "test.pdf"
    filename = "file.pdf"

    count = 3
    create_files(app, db, [File(name=name, filename=filename,
                                post=post)
                           for i in range(0, count)])

    with app.test_client() as client:
        response = client.get('/api/files')

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert len(data) == count

        for file in data:
            assert "id" in file
            assert name == file["name"]
            assert post_id == file["post"]


def test_create_file(app, db):

    tests_path = os.path.join(os.path.dirname(app.root_path), "tests")
    input_path = os.path.join(tests_path, "input")

    with open(os.path.join(input_path, "Frankenstein.pdf"), 'rb') as file:
        read = file.read()
        input_hash = sha256(read).hexdigest()
        file_bytes = BytesIO(read)

    _, post_id = create_test_post(app, db)

    file = {
        "file": (file_bytes, "file1.pdf"),
        "name": "Frankenstein.pdf",
        "post": post_id
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "id" in data
        assert file["name"] == data["name"]
        assert file["post"] == post_id

        post = Post.query.filter(
            Post.id == post_id).one_or_none()

        assert data["id"] == post.files[0].id
        assert file["name"] == post.files[0].name

        filename = File.query.filter(
            File.id == data["id"]).one_or_none().filename

        file_path = os.path.join(tests_path, "output", filename)

        with open(file_path, 'rb') as file:
            output_hash = sha256(file.read()).hexdigest()
            assert input_hash == output_hash


def test_create_bad_file_type(app, db):

    _, post_id = create_test_post(app, db)

    file = {
        "file": (BytesIO(b"<html></html>"), 'test.html'),
        "name": "bad.html",
        "post": post_id
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "security" in data["message"]
        assert "not allowed" in data["message"]


def test_create_file_invalid_post(app, db):

    file = {
        "file": (BytesIO(b"A test"), 'test.pdf'),
        "name": "test.pdf",
        "post": 42
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "post ID" in data["message"]


def test_create_file_no_name(app, db):

    file = {
        "file": (BytesIO(b"A test"), 'test.pdf'),
        "post": 42
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "required" in data["message"]


def test_create_file_no_file(app, db):

    file = {
        "name": "test.pdf",
        "post": 42
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "required" in data["message"]


def test_create_file_no_post(app, db):

    file = {
        "file": (BytesIO(b"A test"), 'test.pdf'),
        "name": "test.pdf"
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "post ID" in data["message"]


def test_delete_file(app, db):

    _, post_id = create_test_post(app, db)

    file = {
        "file": (BytesIO(b"A test"), 'test.pdf'),
        "name": "My test.pdf",
        "post": post_id
    }

    with app.test_client() as client:
        response = client.post('/api/files',
                               content_type='multipart/form-data',
                               data=file)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        filename = File.query.filter(
            File.id == data["id"]).one_or_none().filename
        file_path = os.path.join(os.path.dirname(
            app.root_path), "tests", "output", filename)

        assert os.path.isfile(file_path)

        response = client.delete(f"/api/files/{data['id']}")

        assert "204" in response.status

        assert not os.path.isfile(file_path)


def test_delete_file_that_doesnt_exist(app, db):

    with app.test_client() as client:

        response = client.delete("/api/files/42")

        assert "404" in response.status
