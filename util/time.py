from datetime import date, datetime, timedelta, UTC


def get_date(dt: datetime | date) -> date:
    return dt.date() if isinstance(dt, datetime) else dt


def to_start_of_day(dt: datetime | date) -> datetime:
    return datetime(dt.year, dt.month, dt.day, tzinfo=UTC)


def to_start_of_week(day: date | datetime) -> date:
    normalized_day = get_date(day)
    return normalized_day - timedelta(days=normalized_day.weekday())


def to_end_of_week(day: date | datetime) -> date:
    normalized_day = get_date(day)
    return normalized_day + timedelta(days=6-normalized_day.weekday())