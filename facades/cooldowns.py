from dataclasses import dataclass
from datetime import datetime, timedelta, UTC

from discord import Member
from sqlalchemy import Select

from database.models import Cooldown
from database.db import engine

from sqlmodel import col, select, Session

import facades
from facades.eventlog import add_entry
from globalconf import CONFIG
from util.datatypes import CooldownEntity
from util.exceptions import AlreadySatisfiesError
from util.identifiers import LoggedEventTypeID, ParameterID
from util.parsers import is_infinite_duration, is_null_duration, parse_abs_duration


@dataclass
class AlreadyOnCooldownError(Exception):
    """
    Raised when attempting to manually overwrite the existing cooldown without the force flag
    """
    current: Cooldown


class CooldownEndlessError(Exception):
    """
    Raised when attempting to manually increase or decrease the endless cooldown
    """
    pass


@dataclass
class CooldownEndIsInPast(Exception):
    """
    Raised when attempting to manually decrease the existing cooldown in such a way that its new finish time will be in the past
    """
    ends_at: datetime
    pass


@dataclass
class CooldownInfo:
    entity_id: int
    ends_at: datetime
    reason: str | None


class NO_COOLDOWN:  # noqa
    pass


def _update_or_create(
    current: Cooldown | None,
    entity_type: CooldownEntity,
    entity_id: int,
    casted_at: datetime,
    ends_at: datetime | None = None,
    reason: str | None = None,
    caster_user_id: int | None = None,
    causing_request_id: int | None = None
) -> Cooldown:
    params = dict(
        ends_at=ends_at,
        casted_at=casted_at,
        reason=reason,
        caster_user_id=caster_user_id or CONFIG.bot.user.id,
        causing_request_id=causing_request_id
    )

    if not current:
        current = Cooldown(
            entity=entity_type,
            entity_id=entity_id
        )
    
    for key, value in params.items():
        setattr(current, key, value)

    return current


def _stringify_cooldown(ends_at: datetime | None | type[NO_COOLDOWN]) -> str:
    if ends_at == NO_COOLDOWN:
        return "not on cooldown"
    if ends_at:
        return f"until {ends_at.isoformat()}"
    else:
        return "forever"


async def __log_user_cooldown_update(
    updater: Member,
    entity: CooldownEntity,
    entity_id: int,
    old_ends_at: datetime | None | type[NO_COOLDOWN],
    new_ends_at: datetime | None | type[NO_COOLDOWN],
    reason: str | None
) -> None:
    event_type = LoggedEventTypeID.USER_COOLDOWN_UPDATED if entity == CooldownEntity.USER else LoggedEventTypeID.LEVEL_COOLDOWN_UPDATED
    entity_id_key = "target_user_id" if entity == CooldownEntity.USER else "target_level_id"
    
    custom_data = {
        entity_id_key: entity_id,
        "old": _stringify_cooldown(old_ends_at),
        "new": _stringify_cooldown(new_ends_at),
        "reason": reason or "no reason"
    }
    
    await add_entry(event_type, updater, custom_data)


def exceeds_current(current_ends_at: datetime | None, new_ends_at: datetime | None) -> bool:
    # Accounts for endless cooldowns
    return current_ends_at and (not new_ends_at or new_ends_at > current_ends_at)


def clean_table() -> None:
    select_query = select(
        Cooldown
    ).where(
        col(Cooldown.ends_at).is_not(None),
        Cooldown.ends_at <= datetime.now(UTC)
    )
    with Session(engine) as session:
        for entry in session.exec(select_query):  # noqa
            session.delete(entry)
        session.commit()


def get_current_cooldown(entity_type: CooldownEntity, entity_id: int) -> Cooldown | None:
    clean_table()

    with Session(engine) as session:
        return session.get(Cooldown, (entity_type, entity_id))


def cast_after_request(entity_type: CooldownEntity, entity_id: int, request_id: int) -> None:
    raw_cooldown_duration = facades.parameters.get_value(ParameterID.COOLDOWN_POST_REQUEST_USER_CD)
    if is_null_duration(raw_cooldown_duration):
        return

    current = get_current_cooldown(entity_type, entity_id)

    now_datetime = datetime.now(UTC)
    new_ends_at = None if is_infinite_duration(raw_cooldown_duration) else now_datetime + parse_abs_duration(raw_cooldown_duration)

    if current and not exceeds_current(current.exact_ends_at, new_ends_at):
        return

    reason_main_part = "Recently requested a level" if entity_type == CooldownEntity.USER else "Was recently requested"

    current = _update_or_create(
        current=current,
        entity_type=entity_type,
        entity_id=entity_id,
        casted_at=now_datetime,
        ends_at=new_ends_at,
        reason=f"{reason_main_part} (request ID: {request_id})",
        causing_request_id=request_id
    )

    with Session(engine) as session:
        session.add(current)
        session.commit()


async def manually_set(entity_type: CooldownEntity, entity_id: int, caster: Member, duration: timedelta | None = None, reason: str | None = None, force: bool = False) -> None:
    now_datetime = datetime.now(UTC)
    new_ends_at = now_datetime + duration if duration else None

    if duration and duration.total_seconds() <= 0:
        raise CooldownEndIsInPast(ends_at=new_ends_at)

    current = get_current_cooldown(entity_type, entity_id)
    old_ends_at = current.exact_ends_at if current else NO_COOLDOWN

    if current and not force:
        raise AlreadyOnCooldownError(current)

    current = _update_or_create(
        current=current,
        entity_type=entity_type,
        entity_id=entity_id,
        casted_at=now_datetime,
        ends_at=new_ends_at,
        reason=reason,
        caster_user_id=caster.id
    )

    with Session(engine) as session:
        session.add(current)
        session.commit()

    await __log_user_cooldown_update(caster, entity_type, entity_id, old_ends_at, new_ends_at, reason)


async def manually_modify(entity_type: CooldownEntity, entity_id: int, caster: Member, delta_with_current: timedelta, reason: str | None = None) -> None:
    current = get_current_cooldown(entity_type, entity_id)

    if current and not current.exact_ends_at:
        raise CooldownEndlessError

    now_datetime = datetime.now(UTC)
    old_ends_at = current.exact_ends_at if current else NO_COOLDOWN
    origin_point = current.exact_ends_at if current else now_datetime
    new_ends_at = origin_point + delta_with_current

    if new_ends_at <= now_datetime:
        raise CooldownEndIsInPast(ends_at=new_ends_at)

    current = _update_or_create(
        current=current,
        entity_type=entity_type,
        entity_id=entity_id,
        casted_at=now_datetime,
        ends_at=new_ends_at,
        reason=reason,
        caster_user_id=caster.id
    )

    with Session(engine) as session:
        session.add(current)
        session.commit()

    await __log_user_cooldown_update(caster, entity_type, entity_id, old_ends_at, new_ends_at, reason)


async def manually_amend(entity_type: CooldownEntity, entity_id: int,  amending_user: Member, reason: str | None = None) -> None:
    current = get_current_cooldown(entity_type, entity_id)

    if not current:
        raise AlreadySatisfiesError

    old_ends_at = current.exact_ends_at

    with Session(engine) as session:
        session.delete(current)
        session.commit()

    await __log_user_cooldown_update(amending_user, entity_type, entity_id, old_ends_at, NO_COOLDOWN, reason)


def list_temporary_cooldowns(entity: CooldownEntity, limit: int, offset: int = 0) -> list[CooldownInfo]:
    if offset == 0:
        clean_table()

    query: Select[Cooldown] = select(  # noqa
        Cooldown
    ).where(
        Cooldown.entity == entity,
        col(Cooldown.ends_at).is_not(None)
    ).order_by(
        col(Cooldown.ends_at).desc(),
        col(Cooldown.casted_at)
    ).limit(
        limit
    ).offset(
        offset
    )

    with Session(engine) as session:
        return [
            CooldownInfo(
                entity_id=entry.entity_id,
                ends_at=entry.exact_ends_at,
                reason=entry.reason
            )
            for entry in session.exec(query)
        ]


def list_endless_cooldowns(entity: CooldownEntity, limit: int, offset: int = 0) -> dict[int, str | None]:
    query: Select[Cooldown] = select(  # noqa
        Cooldown
    ).where(
        Cooldown.entity == entity,
        col(Cooldown.ends_at).is_(None)
    ).order_by(
        Cooldown.casted_at
    ).limit(
        limit
    ).offset(
        offset
    )

    with Session(engine) as session:
        return {
            entry.entity_id: entry.reason
            for entry in session.exec(query)
        }
