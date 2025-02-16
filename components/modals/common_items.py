from discord import TextStyle
from discord.ui import TextInput

import facades.texts
from util.datatypes import Language
from util.identifiers import TextPieceID


def get_review_text_input(custom_id: str, language: Language, required: bool = True) -> TextInput:
    return TextInput(
        label=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_REVIEW_LABEL, language)[:100],
        placeholder=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_REVIEW_PLACEHOLDER, language)[:100],
        required=required,
        min_length=40,
        max_length=4000,
        style=TextStyle.long,
        custom_id=custom_id
    )


def get_reason_text_input(custom_id: str, language: Language, required: bool) -> TextInput:
    return TextInput(
        label=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_REASON_LABEL, language)[:100],
        placeholder=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_REASON_PLACEHOLDER, language)[:100],
        required=required,
        min_length=4,
        max_length=4000,
        style=TextStyle.long,
        custom_id=custom_id
    )