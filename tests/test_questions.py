import json

from drp.models import Question, Site, Subject, Grade


def test_get_all_questions(app, db):
    site = Site(name="Site 1")
    subject = Subject(name="Subject 1")

    with app.app_context():
        db.session.add(site)
        db.session.add(subject)

        db.session.add(Question(site=site,
                                grade=Grade.CONSULTANT,
                                specialty="Specialty 1",
                                subject=subject,
                                text="An example question..."))

        db.session.add(Question(site=site,
                                grade=Grade.FY1,
                                specialty="Specialty 2",
                                subject=subject,
                                text="Another question..."))

        db.session.commit()

    with app.test_client() as client:
        response = client.get("/api/questions")

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert len(data) == 2

        assert data[0]["site"]["name"] == "Site 1"
        assert data[0]["grade"] == "consultant"
        assert data[0]["specialty"] == "Specialty 1"
        assert data[0]["subject"]["name"] == "Subject 1"
        assert data[0]["text"] == "An example question..."

        assert data[1]["site"]["name"] == "Site 1"
        assert data[1]["grade"] == "fy1"
        assert data[1]["specialty"] == "Specialty 2"
        assert data[1]["subject"]["name"] == "Subject 1"
        assert data[1]["text"] == "Another question..."


def test_create_question(app, db):
    site = Site(name="Site 1")
    subject = Subject(name="Subject 1")

    with app.app_context():
        db.session.add(site)
        db.session.add(subject)
        db.session.commit()

    question = {
        "site": "Site 1",
        "grade": "core_trainee",
        "specialty": "Specialty 1",
        "subject": "Subject 1",
        "text": "An example question"
    }

    with app.test_client() as client:
        response = client.post("/api/questions", json=question)

        assert "200" in response.status

        data = json.loads(response.data.decode("utf-8"))

        assert data["site"]["name"] == question["site"]
        assert data["grade"] == question["grade"]
        assert data["specialty"] == question["specialty"]
        assert data["subject"]["name"] == question["subject"]
        assert data["text"] == question["text"]


def test_delete_question(app, db):
    with app.app_context():
        site = Site(name="Site 1")
        subject = Subject(name="Subject 1")

        question = Question(site=site,
                            grade=Grade.FY2,
                            specialty="Specialty 1",
                            subject=subject,
                            text="An example question...")

        db.session.add(site)
        db.session.add(subject)
        db.session.add(question)

        db.session.commit()

        id = question.id

    with app.test_client() as client:
        response = client.delete(f"/api/questions/{id}")
        assert "204" in response.status

    with app.app_context():
        assert Question.query.count() == 0
