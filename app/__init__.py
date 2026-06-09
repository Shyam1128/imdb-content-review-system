import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.db import init_db
from app.routes import health, movies, paths, upload
from app.services.movie_service import MovieService


def _configure_logging(app):
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
    else:
        logging.basicConfig(
            level=app.config["LOG_LEVEL"],
            format="[%(asctime)s] [%(levelname)s] %(message)s",
        )
    app.logger.setLevel(app.config["LOG_LEVEL"])


def _register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        app.logger.exception("unhandled error: %s", exc)
        return jsonify({"error": "internal server error"}), 500


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Config)

    _configure_logging(app)

    collection = init_db(app)
    app.extensions["movie_service"] = MovieService(
        collection,
        batch_size=app.config["IMPORT_BATCH_SIZE"],
        default_page_size=app.config["DEFAULT_PAGE_SIZE"],
        max_page_size=app.config["MAX_PAGE_SIZE"],
    )

    app.register_blueprint(upload.bp, url_prefix=paths.API_PREFIX)
    app.register_blueprint(movies.bp, url_prefix=paths.API_PREFIX)
    app.register_blueprint(health.bp)

    _register_error_handlers(app)
    return app
