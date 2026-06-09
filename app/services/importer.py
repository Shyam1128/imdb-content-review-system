import csv
import io
from datetime import datetime


class CsvImportError(ValueError):
    pass


class EmptyUploadError(CsvImportError):
    pass


class InvalidCsvError(CsvImportError):
    pass


class _RawStreamReader(io.RawIOBase):
    def __init__(self, stream):
        self._stream = stream

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self._stream.read(len(buffer))
        if not data:
            return 0
        n = len(data)
        buffer[:n] = data
        return n


class CsvMovieImporter:
    COLUMN_ALIASES = {
        "title": "title",
        "name": "title",
        "year": "year",
        "year of release": "year",
        "year_of_release": "year",
        "language": "language",
        "original_language": "language",
        "release_date": "release_date",
        "release date": "release_date",
        "ratings": "ratings",
        "rating": "ratings",
        "vote_average": "ratings",
    }

    DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y")

    REQUIRED_FIELDS = {"title", "language", "release_date", "ratings"}

    def __init__(self, batch_size=5000):
        self._batch_size = batch_size

    def import_into(self, stream, collection):
        buffered = io.BufferedReader(_RawStreamReader(stream))
        text_stream = io.TextIOWrapper(
            buffered, encoding="utf-8", errors="replace", newline=""
        )
        reader = csv.DictReader(text_stream)

        if not reader.fieldnames:
            raise EmptyUploadError("empty file / no header")

        field_map = {
            self._normalise_header(h): self.COLUMN_ALIASES.get(self._normalise_header(h))
            for h in reader.fieldnames
        }

        recognised = {canonical for canonical in field_map.values() if canonical}
        if not (recognised & self.REQUIRED_FIELDS):
            raise InvalidCsvError(
                "CSV has no recognised movie columns; expected at least one of "
                f"{sorted(self.REQUIRED_FIELDS)}"
            )

        inserted = 0
        skipped = 0
        errors_sample = []
        batch = []

        for line_no, row in enumerate(reader, start=2):
            try:
                batch.append(self._build_document(row, field_map))
            except (ValueError, TypeError) as exc:
                skipped += 1
                if len(errors_sample) < 10:
                    errors_sample.append(f"line {line_no}: {exc}")
                continue

            if len(batch) >= self._batch_size:
                collection.insert_many(batch, ordered=False)
                inserted += len(batch)
                batch = []

        if batch:
            collection.insert_many(batch, ordered=False)
            inserted += len(batch)

        return {"inserted": inserted, "skipped": skipped, "errors_sample": errors_sample}

    @classmethod
    def _build_document(cls, row, field_map):
        doc = {}
        for raw_key, value in row.items():
            canonical = field_map.get(cls._normalise_header(raw_key))
            if canonical == "year":
                doc["year"] = cls._parse_int(value)
            elif canonical == "ratings":
                doc["ratings"] = cls._parse_float(value)
            elif canonical == "release_date":
                doc["release_date"] = cls._parse_date(value)
            elif canonical:
                doc[canonical] = (value or "").strip() or None
            else:
                key = (raw_key or "").strip()
                if key:
                    doc[key] = (value or "").strip() or None

        if doc.get("year") is None and doc.get("release_date") is not None:
            doc["year"] = doc["release_date"].year

        return doc

    @staticmethod
    def _normalise_header(header):
        return (header or "").strip().lower()

    @staticmethod
    def _parse_int(value):
        value = (value or "").strip()
        return int(float(value)) if value else None

    @staticmethod
    def _parse_float(value):
        value = (value or "").strip()
        return float(value) if value else None

    @classmethod
    def _parse_date(cls, value):
        value = (value or "").strip()
        if not value:
            return None
        for fmt in cls.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"unrecognised date format: {value!r}")
