from config.texts import get_default_template, get_description, get_param_descriptions
from database.db import engine
from database.models import TextPiece
from util.datatypes import Language

from sqlmodel import Session

import typing as tp

from util.identifiers import TextPieceID


def get_template(piece_id: TextPieceID, lang: Language) -> str:
    with Session(engine) as session:
        result = session.get(TextPiece, (piece_id, lang))
    return result.template if result else get_default_template(piece_id, lang)


def update_template(piece_id: TextPieceID, lang: Language, new_text: str) -> None:
    with Session(engine) as session:
        piece = session.get(TextPiece, (piece_id, lang))
        if piece:
            piece.template = new_text
        else:
            piece = TextPiece(id=piece_id, language=lang, template=new_text)
        session.add(piece)
        session.commit()


def reset_template(piece_id: TextPieceID, lang: Language) -> None:
    with Session(engine) as session:
        piece = session.get(TextPiece, (piece_id, lang))
        if not piece:
            return
        session.delete(piece)
        session.commit()


def render_text(piece_id: TextPieceID, lang: Language, substitutions: dict[str, tp.Any] = None) -> str:
    if substitutions is None:
        substitutions = {}

    s = get_template(piece_id, lang)
    for key, value in substitutions.items():
        s = s.replace('{' + key + '}', str(value))
    return s


def explain(piece_id: TextPieceID) -> str:
    desc = get_description(piece_id)
    param_desc = get_param_descriptions(piece_id)

    explanation = desc
    explanation += "\n\n**Параметры:**"
    if param_desc:
        for param_name, param_description in param_desc.items():
            explanation += f"\n`{param_name}` - {param_description}"
    else:
        explanation += "\nДанный шаблон не принимает параметров"

    return explanation
