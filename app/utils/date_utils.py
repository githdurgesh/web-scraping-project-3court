from datetime import date, datetime


def parse_date(value) -> date | None:

    if value is None:
        return None

    value = str(value).strip()

    if not value or value in {"-", "None", "null"}:
        return None

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None