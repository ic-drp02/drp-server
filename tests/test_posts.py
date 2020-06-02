import json
import os
from io import BytesIO
from hashlib import sha256

from drp.models import Post, Tag, File


def create_posts(app, db, posts):
    with app.app_context():
        for post in posts:
            db.session.add(post)
        db.session.commit()


def test_get_all_posts(app, db):
    title = "A title"
    summary = "A short summary"
    content = "A few paragraphs of content..."
    count = 3

    create_posts(app, db, [Post(title=title, summary=summary, content=content)
                           for i in range(0, count)])

    with app.test_client() as client:
        response = client.get("/api/posts")

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert len(data) == count

        for post in data:
            assert post["title"] == title
            assert post["summary"] == summary
            assert post["content"] == content


def test_create_post(app, db):
    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A short summary",
            "content": "A few paragraphs of content..."
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert post["title"] == data["title"]
        assert post["summary"] == data["summary"]
        assert post["content"] == data["content"]

        assert "id" in data
        assert "created_at" in data


def test_create_post_with_no_summary(app, db):
    with app.test_client() as client:
        post = {
            "title": "A title",
            "content": "A few paragraphs of content..."
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "400" in response.status


def test_create_post_with_tags(app, db):

    with app.app_context():
        t1 = Tag(name="Tag 1")
        t2 = Tag(name="Tag 2")

        db.session.add(t1)
        db.session.add(t2)
        db.session.commit()

        id1 = t1.id
        id2 = t2.id

    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A summary",
            "content": "A few paragraphs of content...",
            "tags": ["Tag 1", "Tag 2"]
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert post["title"] == data["title"]
        assert post["content"] == data["content"]
        assert post["summary"] == data["summary"]

        assert "id" in data
        assert "created_at" in data

        print(f"______TAGS_____: {post['tags']}")

        assert {"id": id1, "name": "Tag 1"} in data["tags"]
        assert {"id": id2, "name": "Tag 2"} in data["tags"]


def test_create_post_with_files(app, db):

    tests_path = os.path.join(os.path.dirname(app.root_path), "tests")
    input_path = os.path.join(tests_path, "input")

    with open(os.path.join(input_path, "Frankenstein.pdf"), 'rb') as file:
        read = file.read()
        file1 = BytesIO(read)
        hash1 = sha256(read).hexdigest()
    with open(os.path.join(input_path, "Medical.png"), 'rb') as file:
        read = file.read()
        file2 = BytesIO(read)
        hash2 = sha256(read).hexdigest()

    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A summary",
            "content": "A content",
            "files": [(file1, "file1.pdf"), (file2, "file2.png")],
            "names": ["name1.pdf", "name2.jpg"]
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert post["title"] == data["title"]
        assert post["content"] == data["content"]
        assert post["summary"] == data["summary"]

        assert "id" in data
        assert "created_at" in data

        assert len(data["files"]) == 2

        files = data["files"]

        assert post["names"][0] == files[0]["name"]
        assert data["id"] == files[0]["post"]
        assert "id" in files[0]

        assert post["names"][1] == files[1]["name"]
        assert data["id"] == files[1]["post"]
        assert "id" in files[1]

        filename1 = File.query.filter(
            File.id == files[0]["id"]).one_or_none().filename
        filename2 = File.query.filter(
            File.id == files[1]["id"]).one_or_none().filename

        output_path = os.path.join(tests_path, "output")

        file_path = os.path.join(output_path, filename1)
        with open(file_path, 'rb') as file:
            hash = sha256(file.read()).hexdigest()
            assert hash1 == hash
        file_path = os.path.join(output_path, filename2)
        with open(file_path, 'rb') as file:
            hash = sha256(file.read()).hexdigest()
            assert hash2 == hash


def test_create_post_with_missing_title(app, db):
    with app.test_client() as client:
        post = {
            "summary": "A summary",
            "content": "A few paragraphs of content..."
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "400" in response.status


def test_create_post_with_missing_content(app, db):
    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A summary"
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "400" in response.status


def test_create_post_with_bad_file_type(app, db):

    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A summary",
            "content": "A content",
            "files": [(BytesIO(b"<html></html>"), 'test.html')],
            "names": ["name1.html"]
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "security" in data["message"]
        assert "not allowed" in data["message"]


def test_create_post_with_files_names_mismatch(app, db):

    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A summary",
            "content": "A content",
            "files": [(BytesIO(b"A test file"), 'test.pdf')],
            "names": ["name1.pdf", "name2.png"]
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "400" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert "must match" in data["message"]


def test_get_single_post(app, db):
    title = "A title"
    summary = "A short summary"
    content = "A few paragraphs of content..."

    with app.app_context():
        post = Post(title=title, summary=summary, content=content)
        db.session.add(post)
        db.session.commit()
        id = post.id

    with app.test_client() as client:
        response = client.get(f"/api/posts/{id}")

        assert "200" in response.status

        post = json.loads(response.data.decode("utf-8"))

        assert post["title"] == title
        assert post["summary"] == summary
        assert post["content"] == content


def test_get_single_post_that_doesnt_exist(app, db):
    with app.test_client() as client:
        response = client.get("/posts/5")
        assert "404" in response.status


def test_delete_post(app, db):
    title = "A title"
    summary = "A short summary"
    content = "A few paragraphs of content..."

    with app.app_context():
        post = Post(title=title, summary=summary, content=content)
        db.session.add(post)
        db.session.commit()
        id = post.id

    with app.test_client() as client:
        response = client.delete(f"/api/posts/{id}")
        assert "204" in response.status

    with app.app_context():
        assert Post.query.count() == 0


def test_delete_post_with_file(app, db):
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(app.root_path), "tests", "output")

    tests_path = os.path.join(os.path.dirname(app.root_path), "tests")
    input_path = os.path.join(tests_path, "input")

    with open(os.path.join(input_path, "Frankenstein.pdf"), 'rb') as file:
        read = file.read()
        file_bytes = BytesIO(read)

    with app.test_client() as client:
        post = {
            "title": "A title",
            "summary": "A summary",
            "content": "A content",
            "files": [(file_bytes, "file1.pdf")],
            "names": ["name1.pdf"]
        }

        response = client.post('/api/posts',
                               content_type='multipart/form-data',
                               data=post)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        filename = File.query.filter(
            File.id == data["files"][0]["id"]).one_or_none().filename

        file_path = os.path.join(tests_path, "output", filename)
        assert os.path.isfile(file_path)

        response = client.delete(f"/api/posts/{data['id']}")

        assert "204" in response.status

        assert not os.path.isfile(file_path)


def test_delete_single_post_that_doesnt_exist(app, db):
    title = "A title"
    summary = "A short summary"
    content = "A few paragraphs of content..."

    with app.app_context():
        post = Post(title=title, summary=summary, content=content)
        db.session.add(post)
        db.session.commit()
        id = post.id

    with app.test_client() as client:
        response = client.delete(f"/api/posts/{id + 1}")
        assert "404" in response.status

    with app.app_context():
        assert Post.query.count() == 1


def test_timezone_utc(app, db):
    """
    Ensure that api returns datetimes in utc.
    """

    title = "A title"
    summary = "A short summary"
    content = "A few paragraphs of content..."

    with app.app_context():
        post = Post(title=title, summary=summary, content=content)
        db.session.add(post)
        db.session.commit()
        id = post.id

    with app.test_client() as client:
        response = client.get(f"/api/posts/{id}")

        assert "200" in response.status

        post = json.loads(response.data.decode("utf-8"))

        from datetime import datetime, timedelta

        utc_now = datetime.utcnow()
        created_at = datetime.fromisoformat(
            post["created_at"]).replace(tzinfo=None)

        assert utc_now - created_at < timedelta(milliseconds=5000)
