from flask import Blueprint, jsonify

from app.routes import paths

bp = Blueprint("health", __name__)


@bp.get(paths.HEALTH)
def health():
    return jsonify({"status": "ok"})
