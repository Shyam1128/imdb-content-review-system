from flask import Flask, jsonify

from app.config import Config
from app.db import init_db
from app.routes import movies, upload
from app.services.movie_service import MovieService


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Config)

    collection = init_db(app)
    app.extensions["movie_service"] = MovieService(
        collection,
        batch_size=app.config["IMPORT_BATCH_SIZE"],
        default_page_size=app.config["DEFAULT_PAGE_SIZE"],
        max_page_size=app.config["MAX_PAGE_SIZE"],
    )

    app.register_blueprint(upload.bp)
    app.register_blueprint(movies.bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
