from dataclasses import dataclass

from discord import Member

from config.parameters import get_default_raw, get_description, get_displayed_type, normalize_raw_value
from db import EngineProvider
from db.models import ParameterValue

import typing as tp

from util.exceptions import AlreadySatisfiesError
from util.identifiers import LoggedEventTypeID, ParameterID
from facades.eventlog import add_entry


T = tp.TypeVar('T')


@dataclass
class ParameterDetails:
    description: str
    displayed_type: str
    default_value: str
    current_value: str


def get_value(parameter_id: ParameterID, casting_type: type[T] = str) -> T:
    with EngineProvider.get_session() as session:
        result = session.get(ParameterValue, parameter_id)

    raw = result.value if result else get_default_raw(parameter_id)

    match casting_type:
        case x if x is bool:
            return raw == 'true'
        case x if x is int:
            return int(raw)
        case x if x is float:
            return float(raw)
        case x if x is str:
            return raw
        case _:
            return casting_type(raw)


async def update_value(parameter_id: ParameterID, non_normalized_raw_value: str, invoker: Member | None = None) -> None:
    normalized_raw_value = normalize_raw_value(parameter_id, non_normalized_raw_value)

    with EngineProvider.get_session() as session:
        value_row = session.get(ParameterValue, parameter_id)
        if value_row:
            if value_row.value == normalized_raw_value:
                raise AlreadySatisfiesError
            value_row.value = normalized_raw_value
        else:
            if get_default_raw(parameter_id) == normalized_raw_value:
                raise AlreadySatisfiesError
            value_row = ParameterValue(id=parameter_id, value=normalized_raw_value)
        session.add(value_row)
        session.commit()

    await add_entry(LoggedEventTypeID.PARAMETER_EDITED, invoker, dict(
        parameter_id=parameter_id.value,
        value=normalized_raw_value
    ))


async def reset_value(parameter_id: ParameterID, invoker: Member | None = None) -> None:
    with EngineProvider.get_session() as session:
        value_row = session.get(ParameterValue, parameter_id)
        if not value_row:
            raise AlreadySatisfiesError
        session.delete(value_row)
        session.commit()

    await add_entry(LoggedEventTypeID.PARAMETER_EDITED, invoker, dict(
        parameter_id=parameter_id.value,
        value=get_default_raw(parameter_id)
    ))


def explain(parameter_id: ParameterID) -> ParameterDetails:
    return ParameterDetails(
        description=get_description(parameter_id),
        displayed_type=get_displayed_type(parameter_id),
        default_value=get_default_raw(parameter_id),
        current_value=get_value(parameter_id, str)
    )
