from datetime import datetime, UTC
from enum import StrEnum

import typing as tp

from discord import Member


class TimestampStyle(StrEnum):
    SHORT_TIME = "t"
    LONG_TIME = "T"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_DATETIME = "f"
    LONG_DATETIME = "F"
    RELATIVE = "R"


def as_code(line: str | int | float) -> str:
    return f'`{str(line)}`'


def as_code_block(text: str, syntax: str | None = None) -> str:
    syntax_part = syntax or ""
    return f'```{syntax_part}\n{text.strip()}\n```'


def as_timestamp(ts: int | float | datetime, style: TimestampStyle = TimestampStyle.RELATIVE) -> str:
    match ts:
        case datetime():
            if not ts.tzinfo:
                ts = ts.replace(tzinfo=UTC)
            unix_secs = int(ts.timestamp())
        case int():
            unix_secs = ts
        case float():
            unix_secs = int(ts)
        case _:
            tp.assert_never(ts)
    return f'<t:{unix_secs}:{style.value}>'


def as_user(user_id: int) -> str:
    return f'<@{user_id}>'


def as_channel(channel_id: int) -> str:
    return f'<#{channel_id}>'


def as_role(role_id: int) -> str:
    return f'<@&{role_id}>'


def logs_member_ref(member: Member | None) -> str:
    return f'{member.name}/{member.id}' if member else 'bot'


def list_values(values: tp.Iterable[str]) -> list[str]:
    return list(map(as_code, values))


def list_described_values(descriptions: dict[str, str]) -> list[str]:
    lines = []

    for text_piece_id, description in descriptions.items():
        lines.append(f'`{text_piece_id}`: {description}')

    return lines
