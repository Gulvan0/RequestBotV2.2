from config.parameters import get_default_raw, get_description, get_displayed_type
from database.db import engine
from database.models import ParameterValue

from sqlmodel import Session

import typing as tp

from util.format import as_code
from util.identifiers import ParameterID


T = tp.TypeVar('T')


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


def update_value(parameter_id: ParameterID, assigned_raw_value: str) -> None:
    with Session(engine) as session:
        value_row = session.get(ParameterValue, parameter_id)
        if value_row:
            value_row.value = assigned_raw_value
        else:
            value_row = ParameterValue(id=parameter_id, value=assigned_raw_value)
        session.add(value_row)
        session.commit()


def reset_value(parameter_id: ParameterID) -> None:
    with Session(engine) as session:
        value_row = session.get(ParameterValue, parameter_id)
        if not value_row:
            return
        session.delete(value_row)
        session.commit()


def explain(parameter_id: ParameterID) -> str:
    desc = get_description(parameter_id)
    displayed_type = get_displayed_type(parameter_id)
    default_value = get_default_raw(parameter_id)
    current_value = get_value(parameter_id, str)

    return f"{desc}\n\n**Тип:** {displayed_type}\n**Значение по умолчанию:** {as_code(default_value)}\n**Текущее значение:** {as_code(current_value)}"
