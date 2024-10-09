from enum import StrEnum


class TimestampStyle(StrEnum):
    SHORT_TIME = "t"
    LONG_TIME = "T"
    SHORT_DATE = "d"
    LONG_DATE = "D"
    SHORT_DATETIME = "f"
    LONG_DATETIME = "F"
    RELATIVE = "R"


def as_code(line: str) -> str:
    return f'`{line}`'


def as_code_block(text: str, syntax: str | None = None) -> str:
    syntax_part = syntax or ""
    return f'```{syntax_part}\n{text.strip()}\n```'


def as_timestamp(ts: int, style: TimestampStyle = TimestampStyle.RELATIVE) -> str:
    return f'<t:{ts}:{style.value}>'


def as_user(user_id: int) -> str:
    return f'<@{user_id}>'


def as_channel(channel_id: int) -> str:
    return f'<#{channel_id}>'


def as_role(role_id: int) -> str:
    return f'<@&{role_id}>'