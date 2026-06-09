import io
import os

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    MONGO_DB = os.getenv("TEST_MONGO_DB", "imdb_test")


SAMPLE_CSV = (
    "title,year,language,release_date,ratings\n"
    "Alpha,2020,en,2020-01-15,7.5\n"
    "Beta,2019,fr,2019-06-01,8.1\n"
    "Gamma,2020,fr,2020-12-31,6.4\n"
    "Delta,2021,en,2021-03-03,9.0\n"
)


@pytest.fixture
def client():
    app = create_app(TestConfig)
    app.testing = True
    with app.app_context():
        from app.db import get_collection

        get_collection().delete_many({})
    with app.test_client() as c:
        yield c


def _upload(client, csv_text=SAMPLE_CSV):
    data = {"file": (io.BytesIO(csv_text.encode("utf-8")), "movies.csv")}
    return client.post(
        "/api/movies/upload", data=data, content_type="multipart/form-data"
    )


def test_upload_inserts_rows(client):
    resp = _upload(client)
    assert resp.status_code == 201
    assert resp.get_json()["inserted"] == 4


def test_pagination(client):
    _upload(client)
    resp = client.get("/api/movies?page=1&page_size=2")
    body = resp.get_json()
    assert body["total"] == 4
    assert len(body["data"]) == 2
    assert body["page"] == 1


def test_filter_by_year_and_language(client):
    _upload(client)
    resp = client.get("/api/movies?year=2020&language=fr")
    body = resp.get_json()
    assert body["total"] == 1
    assert body["data"][0]["title"] == "Gamma"


def test_sort_by_ratings_desc(client):
    _upload(client)
    resp = client.get("/api/movies?sort_by=ratings&order=desc")
    titles = [m["title"] for m in resp.get_json()["data"]]
    assert titles[0] == "Delta"


def test_sort_by_release_date_asc(client):
    _upload(client)
    resp = client.get("/api/movies?sort_by=release_date&order=asc")
    titles = [m["title"] for m in resp.get_json()["data"]]
    assert titles[0] == "Beta"


def test_invalid_sort_field_returns_400(client):
    resp = client.get("/api/movies?sort_by=title")
    assert resp.status_code == 400


def test_empty_upload_returns_400(client):
    data = {"file": (io.BytesIO(b""), "empty.csv")}
    resp = client.post(
        "/api/movies/upload", data=data, content_type="multipart/form-data"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_upload_unrecognised_columns_returns_400(client):
    # A CSV with a valid header but none of the movie columns is the wrong file.
    # (Avoid 'name', which is an alias for 'title'.)
    csv_text = "id,email,address\n1,a@b.com,Earth\n"
    data = {"file": (io.BytesIO(csv_text.encode("utf-8")), "users.csv")}
    resp = client.post(
        "/api/movies/upload", data=data, content_type="multipart/form-data"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_upload_partial_columns_is_accepted(client):
    # Lenient: title + release_date present (no ratings/language) is still usable.
    csv_text = "title,release_date\nAlpha,2020-01-15\n"
    data = {"file": (io.BytesIO(csv_text.encode("utf-8")), "partial.csv")}
    resp = client.post(
        "/api/movies/upload", data=data, content_type="multipart/form-data"
    )
    assert resp.status_code == 201
    assert resp.get_json()["inserted"] == 1


def test_unknown_route_returns_json_404(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.content_type.startswith("application/json")
    assert "error" in resp.get_json()


def test_unexpected_error_returns_json_500():
    app = create_app(TestConfig)
    app.config["PROPAGATE_EXCEPTIONS"] = False  # let the 500 handler run

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    resp = app.test_client().get("/boom")
    assert resp.status_code == 500
    assert resp.get_json() == {"error": "internal server error"}


def test_real_schema_aliases_and_derived_year(client):
    csv_text = (
        "original_title,original_language,release_date,vote_average,title\n"
        "Toy Story,en,1995-10-30,7.7,Toy Story\n"
    )
    _upload(client, csv_text)
    resp = client.get("/api/movies?year=1995&language=en")
    body = resp.get_json()
    assert body["total"] == 1
    movie = body["data"][0]
    assert movie["year"] == 1995
    assert movie["ratings"] == 7.7
    assert movie["language"] == "en"
