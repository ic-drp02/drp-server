import json

from drp.models import Post, Tag


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

        response = client.post("/api/posts", json=post)

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

        response = client.post("/api/posts", json=post)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert post["title"] == data["title"]
        assert post["content"] == data["content"]

        assert "id" in data
        assert "created_at" in data

        assert data.get("summary") is None


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
            "content": "A few paragraphs of content...",
            "tags": ["Tag 1", "Tag 2"]
        }

        response = client.post("/api/posts", json=post)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert post["title"] == data["title"]
        assert post["content"] == data["content"]

        assert "id" in data
        assert "created_at" in data

        assert data.get("summary") is None

        print(f"______TAGS_____: {post['tags']}")

        assert {"id": id1, "name": "Tag 1"} in data["tags"]
        assert {"id": id2, "name": "Tag 2"} in data["tags"]


def test_create_post_with_missing_title(app, db):
    with app.test_client() as client:
        post = {
            "content": "A few paragraphs of content..."
        }

        response = client.post("/api/posts", json=post)

        assert "400" in response.status


def test_create_post_with_missing_content(app, db):
    with app.test_client() as client:
        post = {
            "title": "A title",
        }

        response = client.post("/api/posts", json=post)

        assert "400" in response.status


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
