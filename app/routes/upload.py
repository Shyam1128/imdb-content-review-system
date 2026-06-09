from flask import Blueprint, current_app, jsonify, request

from app.routes import paths
from app.services.importer import CsvImportError
from app.services.movie_service import get_movie_service

bp = Blueprint("upload", __name__)


@bp.post(paths.MOVIES_IMPORT)
def upload_movies():
    if "file" in request.files:
        stream = request.files["file"].stream
    else:
        stream = request.stream

    try:
        summary = get_movie_service().import_csv(stream)
    except CsvImportError as exc:
        current_app.logger.warning("rejected upload: %s", exc)
        return jsonify({"error": str(exc)}), 400

    current_app.logger.info(
        "imported movies: inserted=%s skipped=%s",
        summary["inserted"],
        summary["skipped"],
    )
    return jsonify(summary), 201
