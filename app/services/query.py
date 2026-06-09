from pymongo import ASCENDING, DESCENDING


class QueryError(ValueError):
    pass


class MovieListQuery:
    SORTABLE_FIELDS = {"release_date", "ratings"}

    def __init__(self, filter, sort, skip, page, page_size):
        self.filter = filter
        self.sort = sort
        self.skip = skip
        self.page = page
        self.page_size = page_size

    @classmethod
    def from_args(cls, args, default_page_size, max_page_size):
        page = cls._parse_int("page", args.get("page", 1))
        page_size = cls._parse_int("page_size", args.get("page_size", default_page_size))
        if page < 1:
            raise QueryError("'page' must be >= 1")
        if page_size < 1:
            raise QueryError("'page_size' must be >= 1")
        page_size = min(page_size, max_page_size)
        skip = (page - 1) * page_size

        mongo_filter = {}
        if "year" in args:
            mongo_filter["year"] = cls._parse_int("year", args.get("year"))
        if "language" in args:
            mongo_filter["language"] = args.get("language")

        sort = []
        sort_by = args.get("sort_by")
        if sort_by:
            if sort_by not in cls.SORTABLE_FIELDS:
                raise QueryError(f"'sort_by' must be one of {sorted(cls.SORTABLE_FIELDS)}")
            order = args.get("order", "asc").lower()
            if order not in ("asc", "desc"):
                raise QueryError("'order' must be 'asc' or 'desc'")
            sort.append((sort_by, ASCENDING if order == "asc" else DESCENDING))

        return cls(mongo_filter, sort, skip, page, page_size)

    @staticmethod
    def _parse_int(name, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise QueryError(f"'{name}' must be an integer")
