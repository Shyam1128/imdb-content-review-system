# IMDb Content Upload & Review System

A Flask + MongoDB service that lets the content team upload movie data via CSV
and consume it through paginated, filterable, sortable APIs.

## Features

- **CSV upload** — streamed and bulk-inserted in batches, so files up to ~1GB
  are processed without loading the whole file into memory.
- **List API** — pagination, filtering by `year` and `language`, sorting by
  `release_date` and `ratings` (ascending/descending).

## Tech stack

Python 3.11 · Flask · MongoDB (PyMongo) · Docker Compose · pytest

## Quick start (Docker — recommended)

```bash
docker compose up --build
```

App: <http://localhost:5000> · MongoDB on `localhost:27017`.

Load the sample data:

```bash
curl -F "file=@sample/movies_sample.csv" http://localhost:5000/api/v1/movies/import
```

## Run locally without Docker

Requires a running MongoDB (default `mongodb://localhost:27017`).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # adjust if needed
python run.py
```

## API

### `POST /api/v1/movies/import`

Upload a CSV. Send a multipart form field named `file`, or post the raw CSV
body.

```bash
curl -F "file=@sample/movies_sample.csv" http://localhost:5000/api/v1/movies/import
```

Response:

```json
{ "inserted": 10, "skipped": 0, "errors_sample": [] }
```

The importer maps the assignment dataset
(`movies_data_assignment.csv`) onto the fields the APIs need. Headers are
matched case-insensitively; **all other columns** (`budget`, `revenue`,
`runtime`, `overview`, …) are preserved on the document as-is.

| CSV column          | stored as      | type | notes                                  |
|---------------------|----------------|------|----------------------------------------|
| `title`             | `title`        | str  |                                        |
| `original_language` | `language`     | str  | used for the `language` filter         |
| `release_date`      | `release_date` | date | parsed to a real date                  |
| `vote_average`      | `ratings`      | float| used for `ratings` sort                |
| _(derived)_         | `year`         | int  | taken from `release_date` for `year` filtering |

> The dataset has no `year` column, so **year of release is derived from
> `release_date`**. Rows with an empty `release_date` therefore have no `year`
> and sort first under `order=asc` (standard MongoDB null ordering).

### `GET /api/v1/movies`

| param       | description                                              |
|-------------|----------------------------------------------------------|
| `page`      | page number (default 1)                                  |
| `page_size` | items per page (default 20, max 100)                     |
| `year`      | filter by year of release                                |
| `language`  | filter by language                                       |
| `sort_by`   | `release_date` or `ratings`                              |
| `order`     | `asc` or `desc` (default `asc`)                          |

```bash
curl "http://localhost:5000/api/v1/movies?year=2016&language=hi&sort_by=ratings&order=desc"
```

Response:

```json
{ "data": [ ... ], "page": 1, "page_size": 20, "total": 2 }
```

## Testing

Integration tests run against a real MongoDB (uses DB `imdb_test`):

```bash
pip install -r requirements.txt
pytest                                  # MongoDB on localhost:27017
# or point at another instance:
MONGO_URI=mongodb://localhost:27017 pytest
```

A Postman collection is included: `postman_collection.json`.

## Database design

Single `movies` collection. Indexes are created on startup for `year`,
`language`, `release_date`, `ratings`, plus a compound `(language, year)` index
to back the common combined filter — keeping reads fast as the collection grows.

## Notes / possible extensions

Kept intentionally lean. If scale demands it later: async/background import with
a job-status endpoint, cursor-based pagination, authentication, and a stricter
schema-validation layer.
