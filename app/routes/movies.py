from flask import Blueprint, jsonify, request

from app.services.movie_service import get_movie_service
from app.services.query import QueryError

bp = Blueprint("movies", __name__)


@bp.get("/api/movies")
def list_movies():
    try:
        result = get_movie_service().list_movies(request.args)
    except QueryError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)
