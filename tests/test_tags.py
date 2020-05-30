import json

from drp.models import Tag


def test_create_tag(app, db):
    with app.test_client() as client:
        tag = {"name": "Tag 1"}

        response = client.post("/tags", json=tag)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert tag["name"] == data["name"]
        assert "id" in data


def test_get_all_tags(app, db):
    tags = ["Tag 1", "Tag 2", "Tag 3"]

    with app.app_context():
        for tag in tags:
            db.session.add(Tag(name=tag))
        db.session.commit()

    with app.test_client() as client:
        response = client.get("/tags")

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert len(data) == len(tags)

        for i in range(len(tags)):
            assert data[i]["name"] == tags[i]


def test_delete_tag(app, db):
    name = "Tag 1"

    with app.app_context():
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        id = tag.id

    with app.test_client() as client:
        response = client.delete(f"/tags/{id + 1}")
        assert "404" in response.status

    with app.app_context():
        assert Tag.query.count() == 1


def test_delete_tag_that_doesnt_exist(app, db):
    name = "Tag 1"

    with app.app_context():
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        id = tag.id

    with app.test_client() as client:
        response = client.delete(f"/tags/{id}")
        assert "204" in response.status

    with app.app_context():
        assert Tag.query.count() == 0
