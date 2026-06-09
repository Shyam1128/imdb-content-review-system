from flask import current_app

from app.services.importer import CsvMovieImporter
from app.services.query import MovieListQuery


class MovieService:
    def __init__(self, collection, *, batch_size, default_page_size, max_page_size):
        self._collection = collection
        self._importer = CsvMovieImporter(batch_size=batch_size)
        self._default_page_size = default_page_size
        self._max_page_size = max_page_size

    def import_csv(self, stream):
        return self._importer.import_into(stream, self._collection)

    def list_movies(self, args):
        query = MovieListQuery.from_args(
            args, self._default_page_size, self._max_page_size
        )

        cursor = self._collection.find(query.filter)
        if query.sort:
            cursor = cursor.sort(query.sort)
        cursor = cursor.skip(query.skip).limit(query.page_size)

        data = [self._serialize(doc) for doc in cursor]
        total = self._collection.count_documents(query.filter)

        return {
            "data": data,
            "page": query.page,
            "page_size": query.page_size,
            "total": total,
        }

    @staticmethod
    def _serialize(doc):
        doc["id"] = str(doc.pop("_id"))
        if doc.get("release_date") is not None:
            doc["release_date"] = doc["release_date"].date().isoformat()
        return doc


def get_movie_service():
    return current_app.extensions["movie_service"]
