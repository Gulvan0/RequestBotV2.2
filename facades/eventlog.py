from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime

import yaml
import typing as tp

import discord
from sqlmodel.sql._expression_select_cls import Select, SelectOfScalar

from database.models import LoggedEvent, StoredLogFilter
from util.exceptions import AlreadySatisfiesError
from util.format import as_code_block, logs_member_ref
from util.identifiers import LoggedEventTypeID, RouteID
from sqlmodel import select, Session, col, func

from database.db import engine


class AlreadyExistsError(Exception):
    """
    An exception occurring when an entity with the same name as the one being saved already exists. Raised only when the `force` flag is set to `False`
    """
    pass


class NotExistsError(Exception):
    """
    An exception occurring when an entity with the provided name doesn't exist when it is assumed to (for example, when trying to select a filter by name, but no filter with such name exists)
    """
    pass


@dataclass
class LoadedLogFilter:
    user_id: int | None = None
    event_type: LoggedEventTypeID | None = None
    custom_data_values: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_stored(cls, stored_filter: StoredLogFilter) -> LoadedLogFilter:
        return LoadedLogFilter(
            user_id=stored_filter.user_id,
            event_type=stored_filter.event_type,
            custom_data_values=json.loads(stored_filter.custom_data_values)
        )


async def add_entry(event_type: LoggedEventTypeID, user: discord.Member | None = None, custom_data: dict[str, str] | None = None) -> None:
    user_str = logs_member_ref(user)

    printed_message = f'{event_type.name} by {user_str}'
    if custom_data:
        pairs = ', '.join([f'{key}={value}' for key, value in custom_data.items()])
        printed_message += f' ({pairs})'
    print(printed_message)

    event_dict = dict(
        event=event_type.name,
        user=user_str,
        timestamp=datetime.now().isoformat()
    )
    event_dict.update(custom_data)
    posted_message = as_code_block(yaml.safe_dump(event_dict, sort_keys=False, allow_unicode=True), "yaml")
    import services.disc
    await services.disc.post_raw_text(RouteID.LOG, posted_message)

    custom_data_str = json.dumps(custom_data, ensure_ascii=False) if custom_data else "{}"
    with Session(engine) as session:
        new_entry = LoggedEvent(event_type=event_type, user_id=user.id if user else None, custom_data=custom_data_str)
        session.add(new_entry)
        session.commit()


def _current_filter_name(user: discord.Member) -> str:
    return f'@{user.id}'


def get_filter(name: str) -> StoredLogFilter | None:
    with Session(engine) as session:
        return session.get(StoredLogFilter, name)  # noqa


def get_current_filter(user: discord.Member) -> StoredLogFilter:
    filter_name = _current_filter_name(user)
    return get_filter(filter_name) or StoredLogFilter(name=filter_name)


def save_filter(name: str, log_filter: StoredLogFilter, force: bool = False) -> None:
    with Session(engine) as session:
        stored_filter = session.get(StoredLogFilter, name)

        if not stored_filter:
            stored_filter = StoredLogFilter(name=name)
        elif not force:
            raise AlreadyExistsError

        stored_filter.user_id = log_filter.user_id
        stored_filter.event_type = log_filter.event_type
        stored_filter.custom_data_values = log_filter.custom_data_values

        session.add(stored_filter)
        session.commit()


def select_filter(user: discord.Member, name: str) -> None:
    log_filter = get_filter(name)
    if not log_filter:
        raise NotExistsError
    save_filter(_current_filter_name(user), log_filter, force=True)


def update_filter_user(current_filter_owner: discord.Member, restricted_user: discord.Member | None) -> None:
    stored_filter = get_current_filter(current_filter_owner)

    passed_user_id = restricted_user.id if restricted_user else None

    if stored_filter.user_id == passed_user_id:
        raise AlreadySatisfiesError

    stored_filter.user_id = passed_user_id

    with Session(engine) as session:
        session.add(stored_filter)
        session.commit()


def update_filter_event_type(current_filter_owner: discord.Member, restricted_event_type: LoggedEventTypeID | None) -> None:
    stored_filter = get_current_filter(current_filter_owner)

    if stored_filter.event_type == restricted_event_type:
        raise AlreadySatisfiesError

    stored_filter.event_type = restricted_event_type

    with Session(engine) as session:
        session.add(stored_filter)
        session.commit()


def update_filter_custom_field(current_filter_owner: discord.Member, key: str, value: str | None) -> None:
    stored_filter = get_current_filter(current_filter_owner)

    custom_data_dict: dict[str, str] = json.loads(stored_filter.custom_data_values)

    if custom_data_dict.get(key) == value:
        raise AlreadySatisfiesError

    if value is not None:
        custom_data_dict[key] = value
    else:
        custom_data_dict.pop(key, None)
    stored_filter.custom_data_values = json.dumps(custom_data_dict, ensure_ascii=False)

    with Session(engine) as session:
        session.add(stored_filter)
        session.commit()


def clear_filter_custom_fields(current_filter_owner: discord.Member) -> None:
    stored_filter = get_current_filter(current_filter_owner)

    if stored_filter.custom_data_values == "{}":
        raise AlreadySatisfiesError

    stored_filter.custom_data_values = "{}"

    with Session(engine) as session:
        session.add(stored_filter)
        session.commit()


def delete_filter(filter_name: str) -> None:
    with Session(engine) as session:
        stored_filter = session.get(StoredLogFilter, filter_name)
        if not stored_filter:
            raise AlreadySatisfiesError
        session.delete(stored_filter)
        session.commit()


def clear_current_filter(current_filter_owner: discord.Member) -> None:
    delete_filter(_current_filter_name(current_filter_owner))


def list_filters() -> set[str]:
    with Session(engine) as session:
        query = select(StoredLogFilter.name).where(col(StoredLogFilter.name).startswith("@") == False)
        return set(session.exec(query).all())  # noqa


def _apply_filter(log_filter: StoredLogFilter | LoadedLogFilter | None, query: Select | SelectOfScalar) -> Select | SelectOfScalar:
    match log_filter:
        case None:
            return query
        case StoredLogFilter():
            loaded = LoadedLogFilter.from_stored(log_filter)
        case LoadedLogFilter():
            loaded = log_filter
        case _:
            tp.assert_never(log_filter)

    if loaded.user_id:
        query = query.where(LoggedEvent.user_id == loaded.user_id)
    if loaded.event_type:
        query = query.where(LoggedEvent.event_type == loaded.event_type)
    for key, value in loaded.custom_data_values.items():
        query = query.where(col(LoggedEvent.custom_data).contains(f'"{key}": "{value}"'))
    return query


def get_entries(limit: int, offset: int = 0, log_filter: StoredLogFilter | LoadedLogFilter | None = None) -> list[LoggedEvent]:
    query = select(LoggedEvent)
    query = _apply_filter(log_filter, query)
    query = query.limit(limit).offset(offset)
    with Session(engine) as session:
        return list(session.exec(query).all())


def get_offset_at_datetime(ts: datetime, log_filter: StoredLogFilter | LoadedLogFilter | None = None) -> int:
    query = select(func.count(LoggedEvent.id))
    query = _apply_filter(log_filter, query)
    query = query.where(LoggedEvent.timestamp < ts)
    with Session(engine) as session:
        return session.exec(query).one()  # noqa


def find_filters_by_prefix(pref: str) -> list[str]:
    query = select(
        StoredLogFilter.name
    ).where(
        col(StoredLogFilter.name).startswith(pref),
        col(StoredLogFilter.name).startswith("@") == False
    )
    with Session(engine) as session:
        return list(session.exec(query).all())  # noqa
