from dataclasses import dataclass

from discord import Member

from config.texts import get_default_template, get_description, get_param_descriptions
from db import EngineProvider
from db.models import TextPiece
from facades.eventlog import add_entry
from util.datatypes import Language

import typing as tp

from util.exceptions import AlreadySatisfiesError
from util.identifiers import LoggedEventTypeID, TextPieceID


@dataclass
class TextPieceDetails:
    description: str
    parameter_descriptions: dict[str, str]
    current_templates: dict[Language, str]


def get_template(piece_id: TextPieceID, lang: Language) -> str:
    with EngineProvider.get_session() as session:
        result = session.get(TextPiece, (piece_id, lang))
    return result.template if result else get_default_template(piece_id, lang)


async def update_template(piece_id: TextPieceID, lang: Language, new_text: str, invoker: Member | None = None) -> None:
    with EngineProvider.get_session() as session:
        piece = session.get(TextPiece, (piece_id, lang))
        if piece:
            if piece.template == new_text:
                raise AlreadySatisfiesError
            piece.template = new_text
        else:
            if get_default_template(piece_id, lang) == new_text:
                raise AlreadySatisfiesError
            piece = TextPiece(id=piece_id, language=lang, template=new_text)
        session.add(piece)
        session.commit()

    await add_entry(LoggedEventTypeID.TEXT_PIECE_EDITED, invoker, dict(
        piece_id=piece_id.value,
        lang=lang.value,
        new_text=new_text
    ))


async def reset_template(piece_id: TextPieceID, lang: Language, invoker: Member | None = None) -> None:
    with EngineProvider.get_session() as session:
        piece = session.get(TextPiece, (piece_id, lang))
        if not piece:
            raise AlreadySatisfiesError
        session.delete(piece)
        session.commit()

    await add_entry(LoggedEventTypeID.TEXT_PIECE_EDITED, invoker, dict(
        piece_id=piece_id.value,
        lang=lang.value,
        new_text=get_default_template(piece_id, lang)
    ))


def render_text(piece_id: TextPieceID, lang: Language, substitutions: dict[str, tp.Any] = None) -> str:
    if substitutions is None:
        substitutions = {}

    s = get_template(piece_id, lang)
    for key, value in substitutions.items():
        s = s.replace(
            '{' + key + '}',
            render_text(value, lang) if isinstance(value, TextPieceID) else str(value)
        )
    return s


def explain(piece_id: TextPieceID) -> TextPieceDetails:
    return TextPieceDetails(
        description=get_description(piece_id),
        parameter_descriptions=get_param_descriptions(piece_id),
        current_templates={lang: get_template(piece_id, lang) for lang in Language}
    )
