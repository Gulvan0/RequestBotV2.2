from dataclasses import dataclass

from config.parameters import get_default_raw, get_description, get_displayed_type, normalize_raw_value
from database.db import engine
from database.models import ParameterValue

from sqlmodel import Session

import typing as tp

from util.exceptions import AlreadySatisfiesError
from util.identifiers import ParameterID


T = tp.TypeVar('T')


class RestrictionNotSatisfiedError(Exception):
    """
    An exception occurring when the parameter's new value passed by the user doesn't adhere to the type of this parameter
    """


@dataclass
class ParameterDetails:
    description: str
    displayed_type: str
    default_value: str
    current_value: str


def get_value(parameter_id: ParameterID, casting_type: type[T]) -> T:
    with Session(engine) as session:
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


def update_value(parameter_id: ParameterID, non_normalized_raw_value: str) -> None:
    try:
        normalized_raw_value = normalize_raw_value(parameter_id, non_normalized_raw_value)
    except ValueError:
        raise RestrictionNotSatisfiedError

    with Session(engine) as session:
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


def reset_value(parameter_id: ParameterID) -> None:
    with Session(engine) as session:
        value_row = session.get(ParameterValue, parameter_id)
        if not value_row:
            raise AlreadySatisfiesError
        session.delete(value_row)
        session.commit()


def explain(parameter_id: ParameterID) -> ParameterDetails:
    return ParameterDetails(
        description=get_description(parameter_id),
        displayed_type=get_displayed_type(parameter_id),
        default_value=get_default_raw(parameter_id),
        current_value=get_value(parameter_id, str)
    )
