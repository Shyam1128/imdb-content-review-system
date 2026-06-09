from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.db import init_db
from app.routes import movies, upload
from app.services.movie_service import MovieService


def _register_error_handlers(app):
    """Return JSON (not Flask's default HTML) for all errors, so every API
    response — success or failure — has a consistent shape."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        # 404, 405, etc. — preserve the status code, JSON-ify the body.
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        # Anything not already an HTTPException is an unexpected 500.
        app.logger.exception("unhandled error: %s", exc)
        return jsonify({"error": "internal server error"}), 500


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

    _register_error_handlers(app)
    return app
