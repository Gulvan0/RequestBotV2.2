from discord import app_commands
from discord.app_commands.translator import TranslationContextTypes, locale_str
from discord.enums import Locale

from facades.texts import render_text
from util.datatypes import Language
from util.identifiers import TextPieceID


class Translator(app_commands.Translator):
    async def translate(self, translated_str: locale_str, locale: Locale, context: TranslationContextTypes) -> str | None:
        if translated_str.message not in TextPieceID:
            return None
        return render_text(TextPieceID(translated_str.message), Language.RU if locale == Locale.russian else Language.EN)
