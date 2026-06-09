from flask import Blueprint, jsonify, request

from app.services.importer import CsvImportError
from app.services.movie_service import get_movie_service

bp = Blueprint("upload", __name__)


@bp.post("/api/movies/upload")
def upload_movies():
    if "file" in request.files:
        stream = request.files["file"].stream
    else:
        stream = request.stream

    try:
        summary = get_movie_service().import_csv(stream)
    except CsvImportError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(summary), 201
