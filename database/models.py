from datetime import datetime, UTC
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from util.datatypes import Opinion, CooldownEntity, Language
from util.format import as_code, as_user
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

    causing_request_id: int | None = Field(default=None, foreign_key="request.id")
    causing_request: Optional["Request"] = Relationship()

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


class Request(SQLModel, table=True):
    id: int | None = Field(primary_key=True)

    level_id: int
    language: Language
    level_name: str | None
    yt_link: str | None
    additional_comment: str | None

    request_author: str
    is_author_user_id: bool = True

    details_message_id: int | None  # reviewers' widget when unresolved, else archive entry
    details_message_channel_id: int | None
    resolution_message_id: int | None
    resolution_message_channel_id: int | None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))  # on command executed successfully
    requested_at: datetime | None  # on modal submitted successfully

    opinions: list["RequestOpinion"] = Relationship(back_populates="request")
    reviews: list["RequestReview"] = Relationship(back_populates="request")

    @property
    def request_author_mention(self) -> str:
        return as_user(int(self.request_author)) if self.is_author_user_id else as_code(self.request_author)


class RequestOpinion(SQLModel, table=True):
    id: int | None = Field(primary_key=True)

    author_user_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    opinion: Opinion
    is_resolution: bool = False

    request_id: int = Field(foreign_key="request.id")
    request: Request = Relationship(back_populates="opinions", sa_relationship_kwargs=dict(foreign_keys="RequestOpinion.request_id"))

    associated_review_id: int | None = Field(default=None, foreign_key="requestreview.id")
    associated_review: Optional["RequestReview"] = Relationship()


class RequestReview(SQLModel, table=True):
    id: int | None = Field(primary_key=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    author_user_id: int
    text: str
    message_id: int
    opinion: Opinion

    request_id: int = Field(foreign_key="request.id")
    request: Request = Relationship(back_populates="reviews")
