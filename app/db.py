from flask import current_app
from pymongo import ASCENDING, MongoClient


def init_db(app):
    client = MongoClient(app.config["MONGO_URI"])
    collection = client[app.config["MONGO_DB"]][app.config["MONGO_COLLECTION"]]

    app.extensions["mongo_client"] = client
    app.extensions["movie_collection"] = collection

    _ensure_indexes(collection)
    return collection


def get_collection():
    return current_app.extensions["movie_collection"]


def _ensure_indexes(collection):
    collection.create_index([("year", ASCENDING)])
    collection.create_index([("language", ASCENDING)])
    collection.create_index([("release_date", ASCENDING)])
    collection.create_index([("ratings", ASCENDING)])
    collection.create_index([("language", ASCENDING), ("year", ASCENDING)])
