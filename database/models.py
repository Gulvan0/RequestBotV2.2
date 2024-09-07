from sqlmodel import Field, SQLModel

from util.datatypes import Language
from util.identifiers import RouteID, TextPieceID


class TextPiece(SQLModel, table=True):
    id: TextPieceID = Field(primary_key=True)
    language: Language = Field(primary_key=True)
    template: str


class Route(SQLModel, table=True):
    id: RouteID = Field(primary_key=True)
    channel_id: int | None
    enabled: bool

