import typing as tp

import discord

from database.db import engine
from database.models import UserPreference
from sqlmodel import Session

from facades.eventlog import add_entry
from util.identifiers import LoggedEventTypeID, UserPreferenceID

T = tp.TypeVar('T')


def get_value(preference_id: UserPreferenceID, user: discord.Member, casting_type: type[T]) -> T | None:
    with Session(engine) as session:
        result = session.get(UserPreference, (preference_id, user.id))

    if not result:
        return None

    match casting_type:
        case x if x is bool:
            return result.value == 'true'
        case x if x is int:
            return int(result.value)
        case x if x is float:
            return float(result.value)
        case x if x is str:
            return result.value
        case _:
            return casting_type(result.value)


async def update_value(preference_id: UserPreferenceID, user: discord.Member, normalized_raw_value: str) -> None:
    with Session(engine) as session:
        value_row = session.get(UserPreference, (preference_id, user.id))
        if value_row:
            value_row.value = normalized_raw_value
        else:
            value_row = UserPreference(id=preference_id, user_id=user.id, value=normalized_raw_value)
        session.add(value_row)
        session.commit()

    await add_entry(LoggedEventTypeID.USER_PREFERENCE_UPDATED, user, dict(
        preference_id=preference_id.value,
        value=normalized_raw_value
    ))