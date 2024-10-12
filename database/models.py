from sqlmodel import Field, SQLModel

from util.datatypes import Language
from util.identifiers import ParameterID, RouteID, TextPieceID, UserPreferenceID


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
