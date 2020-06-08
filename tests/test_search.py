import json

from drp.models import Post


def add_test_posts(app, db):

    posts = [
        {
            "title": "Every thing must have a beginning",
            "summary": "Text by Marry Shelley",
            "content": """Every thing must have a beginning, to \
speak in Sanchean phrase; and that beginning must be \
linked to something that went before. The Hindoos give \
the world an elephant to support it, but they make the \
elephant stand upon a tortoise. Invention, it must be humbly \
admitted, does not consist in creating out of void, but out \
of chaos; the materials must, in the first place, be afforded: \
it can give form to dark, shapeless substances, but cannot \
bring into being the substance itself. In all matters of \
discovery and invention, even of those that appertain to \
the imagination, we are continually reminded of the story of \
Columbus and his egg. Invention consists in the capacity of \
seizing on the capabilities of a subject, and in the power of \
moulding and fashioning ideas suggested to it."""
        },
        {
            "title": "World Turtle",
            "summary": "Text from Wikipedia, CC-BY-SA",
            "content": """The World Turtle (also referred to as \
the Cosmic Turtle or the World-bearing Turtle) is a mytheme of a \
giant turtle (or tortoise) supporting or containing the world. \
The mytheme, which is similar to that of the World Elephant and \
World Serpent, occurs in Hindu mythology, Chinese mythology and the \
mythologies of the indigenous peoples of the Americas. The "World-Tortoise" \
mytheme was discussed comparatively by Edward Burnett Tylor (1878:341)."""
        },
        {
            "title": "Test 1",
            "summary": "Alpha is a letter.",
            "content": "So is beta."
        },
        {
            "title": "Test 2",
            "summary": "Text from Wikipedia, CC-BY-SA",
            "content": """Alpha /ˈælfə/[1] (uppercase Α, lowercase α; \
Ancient Greek: ἄλφα, álpha, modern pronunciation álfa) is the first letter of \
the Greek alphabet. In the system of Greek numerals, it has a value of 1. \
Beta (UK: /ˈbiːtə/, US: /ˈbeɪtə/; uppercase Β, lowercase β, or cursive ϐ; \
Ancient Greek: βῆτα, romanized: bē̂ta or Greek: βήτα, romanized: víta) is \
the second letter of the Greek alphabet.""",
        },
        {
            "title": "Test 3",
            "summary": "Test summary",
            "content": "Alpha beta"
        }
    ]
    with app.app_context():
        for post in posts:
            post = Post(title=post["title"],
                        summary=post["summary"], content=post["content"])
            db.session.add(post)
        db.session.commit()


def test_search_single_content(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/elephant")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 2
        assert "beginning" in posts[0]["title"]
        assert "Turtle" in posts[1]["title"]


def test_search_two_content(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/elephant tortoise")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 2
        assert "beginning" in posts[0]["title"]
        assert "Turtle" in posts[1]["title"]


def test_search_three_across_columns(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/elephant Shelley tortoise")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 1
        assert "beginning" in posts[0]["title"]


def test_search_order_by_rank(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/alpha beta")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 3
        assert posts[0]["title"] == "Test 3"
        assert posts[1]["title"] == "Test 1"
        assert posts[2]["title"] == "Test 2"


def test_search_form(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/create")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 1
        assert "beginning" in posts[0]["title"]


def test_search_prefix(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/capab")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 1
        assert "beginning" in posts[0]["title"]

        response = client.get("/api/search/posts/conta")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 1
        assert "Turtle" in posts[0]["title"]


def test_search_stop_word(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("/api/search/posts/the")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 0


def test_search_special_chars(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get("""/api/search/posts/:"';""")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 0

        response = client.get("""/api/search/posts/*'""")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 0


def test_search_invalid_pagination(app, db):
    with app.test_client() as client:
        response = client.get(
            "/api/search/posts/alpha?page=1&results_per_page=invalid")

        assert "400" in response.status

        result = json.loads(response.data.decode("utf-8"))

        assert "number" in result["message"]


def test_search_first_page(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get(
            "/api/search/posts/alpha beta?page=0&results_per_page=2")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 2
        assert posts[0]["title"] == "Test 3"
        assert posts[1]["title"] == "Test 1"


def test_search_second_page(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get(
            "/api/search/posts/alpha beta?page=1&results_per_page=2")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 1
        assert posts[0]["title"] == "Test 2"


def test_search_high_page(app, db):
    add_test_posts(app, db)

    with app.test_client() as client:
        response = client.get(
            "/api/search/posts/alpha beta?page=20&results_per_page=2")

        assert "200" in response.status

        posts = json.loads(response.data.decode("utf-8"))

        assert len(posts) == 0
