import re
import typing as tp
from datetime import timedelta
from enum import auto, Enum, StrEnum


class CantParseError(Exception):
    """
    Raised when the format of the non-normalized value doesn't match the expected one
    """
    pass


class DurationType(Enum):
    RELATIVE = auto()
    ABSOLUTE = auto()


class DurationElementUnit(StrEnum):
    SECOND = "s"
    MINUTE = "min"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "m"
    QUARTER = "q"
    YEAR = "y"


ELEMENT_UNIT_PATTERN = '|'.join(DurationElementUnit)
ELEMENT_AMOUNT_PATTERN = r'\d+'
ELEMENT_PATTERN = rf'{ELEMENT_AMOUNT_PATTERN}({ELEMENT_UNIT_PATTERN})'


def normalize_duration(raw_non_normalized_value: str, allowed_types: set[DurationType]) -> str:
    assert allowed_types, "At least one duration type must be allowed to normalize the raw value"

    cleaned = re.sub(r'[^\dA-Za-z+\-]', '', raw_non_normalized_value.lower())

    pattern = rf'({ELEMENT_PATTERN})+'
    if allowed_types == {DurationType.RELATIVE}:
        pattern = r'[+\-]' + pattern
    elif allowed_types == {DurationType.RELATIVE, DurationType.ABSOLUTE}:
        pattern = r'[+\-]?' + pattern

    if re.fullmatch(pattern, cleaned) or is_null_duration(cleaned) or is_infinite_duration(cleaned):
        return cleaned
    raise CantParseError


def is_null_duration(raw_normalized_value: str) -> bool:
    return raw_normalized_value == "0"


def is_infinite_duration(raw_normalized_value: str) -> bool:
    return raw_normalized_value == "inf"


def get_duration_type(raw_normalized_value: str) -> DurationType:
    return DurationType.RELATIVE if raw_normalized_value.startswith(("-", "+")) else DurationType.ABSOLUTE


def parse_abs_duration(raw_normalized_value: str) -> timedelta:
    delta = timedelta()
    for amount_str, unit in re.findall(rf'({ELEMENT_AMOUNT_PATTERN})({ELEMENT_UNIT_PATTERN})', raw_normalized_value):
        amount = int(amount_str)
        match DurationElementUnit(unit):
            case DurationElementUnit.SECOND:
                delta += timedelta(seconds=amount)
            case DurationElementUnit.MINUTE:
                delta += timedelta(minutes=amount)
            case DurationElementUnit.HOUR:
                delta += timedelta(hours=amount)
            case DurationElementUnit.DAY:
                delta += timedelta(days=amount)
            case DurationElementUnit.WEEK:
                delta += timedelta(days=amount * 7)
            case DurationElementUnit.MONTH:
                delta += timedelta(days=amount * 30)
            case DurationElementUnit.QUARTER:
                delta += timedelta(days=amount * 120)
            case DurationElementUnit.YEAR:
                delta += timedelta(days=amount * 365)
            case _:
                tp.assert_never(DurationElementUnit(unit))
    return delta


def parse_rel_duration(raw_normalized_value: str) -> timedelta:
    abs_delta = parse_abs_duration(raw_normalized_value[1:])
    return abs_delta if raw_normalized_value[0] == "+" else -abs_delta


def parse_finite_nonzero_duration(raw_normalized_value: str) -> timedelta:
    return parse_abs_duration(raw_normalized_value) if get_duration_type(raw_normalized_value) == DurationType.RELATIVE else parse_rel_duration(raw_normalized_value)