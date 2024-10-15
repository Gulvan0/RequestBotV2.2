from datetime import datetime, UTC

from sqlmodel import Field, SQLModel

from util.datatypes import Language
from util.identifiers import LoggedEventTypeID, ParameterID, RouteID, TextPieceID, PermissionFlagID, UserPreferenceID


class TextPiece(SQLModel, table=True):
    id: TextPieceID = Field(primary_key=True)
    language: Language = Field(primary_key=True)
    template: str


class Route(SQLModel, table=True):
    id: RouteID = Field(primary_key=True)
    channel_id: int | None
    enabled: bool


class ParameterValue(SQLModel, table=True):
    id: ParameterID = Field(primary_key=True)
    value: str


class UserPreference(SQLModel, table=True):
    id: UserPreferenceID = Field(primary_key=True)
    user_id: int = Field(primary_key=True)
    value: str


class PermissionFlag(SQLModel, table=True):
    id: PermissionFlagID = Field(primary_key=True)
    role_id: int = Field(primary_key=True)


class LoggedEvent(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: LoggedEventTypeID
    user_id: int | None
    custom_data: str = Field(default="{}")
