import os


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "imdb")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "movies")

    IMPORT_BATCH_SIZE = int(os.getenv("IMPORT_BATCH_SIZE", "5000"))

    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
