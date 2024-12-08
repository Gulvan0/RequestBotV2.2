from datetime import datetime, UTC

import yaml
from sqlmodel import Field, SQLModel

from util.datatypes import CooldownEntity, Language
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


class StoredLogFilter(SQLModel, table=True):
    name: str = Field(primary_key=True)
    user_id: int | None
    event_type: LoggedEventTypeID | None
    custom_data_values: str = Field(default="{}")

    def is_empty(self) -> bool:
        return self.user_id is None and self.event_type is None and self.custom_data_values == "{}"


class Cooldown(SQLModel, table=True):
    entity: CooldownEntity = Field(primary_key=True)
    entity_id: int = Field(primary_key=True)
    casted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ends_at: datetime | None
    reason: str | None
    caster_user_id: int
    causing_request_id: int | None

    @property
    def exact_casted_at(self) -> datetime:
        if self.casted_at.tzinfo:
            return self.casted_at
        else:
            return self.casted_at.replace(tzinfo=UTC)

    @property
    def exact_ends_at(self) -> datetime | None:
        if not self.ends_at:
            return None
        elif self.ends_at.tzinfo:
            return self.ends_at
        else:
            return self.ends_at.replace(tzinfo=UTC)