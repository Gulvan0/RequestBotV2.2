from sqlmodel import Field, SQLModel

from util.datatypes import Language
from util.identifiers import TextPieceID


class TextPiece(SQLModel, table=True):
    id: TextPieceID = Field(primary_key=True)
    language: Language = Field(primary_key=True)
    template: str
