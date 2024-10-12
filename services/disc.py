from dataclasses import dataclass

import discord
from discord import Locale, Message

from config.stage_parameters import get_value as get_stage_parameter_value
from routes import get_channel_id, is_enabled
from texts import render_text
from user_preferences import get_value as get_preference_value
from util.datatypes import Language
from util.identifiers import RouteID, StageParameterID, TextPieceID, UserPreferenceID
from string import Template


@dataclass
class MemberLanguageInfo:
    language: Language
    is_assumed: bool


def member_language(member: discord.Member, locale: Locale | None) -> MemberLanguageInfo:
    preferred_language = get_preference_value(UserPreferenceID.LANGUAGE, member, Language)
    if preferred_language:
        return MemberLanguageInfo(preferred_language, False)
    elif locale:
        return MemberLanguageInfo(Language.RU if locale == Locale.russian else Language.EN, False)
    elif member.get_role(get_stage_parameter_value(StageParameterID.SPEAKS_RUSSIAN_ROLE_ID)) is not None:
        return MemberLanguageInfo(Language.RU, True)
    else:
        return MemberLanguageInfo(Language.EN, True)


async def respond(inter: discord.Interaction, template: str | list[str] | Template | TextPieceID, substitutions: dict[str, str] | None = None, ephemeral: bool = False) -> None:
    if isinstance(template, TextPieceID):
        member_language_info = member_language(inter.user, inter.locale)
        message_text = render_text(template, member_language_info.language, substitutions or {})
        if member_language_info.is_assumed:
            subtext_language = Language.EN if member_language_info.language == Language.RU else Language.RU
            subtext = render_text(TextPieceID.COMMON_LANGUAGE_SELECTION_PROPOSAL_SUBTEXT, subtext_language)
            message_text += f"\n-# {subtext}"
    elif isinstance(template, Template):
        message_text = template.safe_substitute(substitutions or {})
    else:
        str_template = "\n".join(template) if isinstance(template, list) else template
        if substitutions:
            message_text = Template(str_template).safe_substitute(substitutions)
        else:
            message_text = str_template

    await inter.response.send_message(message_text, ephemeral=ephemeral)


async def post(
    inter: discord.Interaction,
    route: RouteID,
    text: TextPieceID,
    language: Language | list[Language] | tuple[Language, ...] = (Language.RU, Language.EN),
    substitutions: dict[str, str] | None = None
) -> Message | None:
    if not substitutions:
        substitutions = {}

    if not is_enabled(route):
        return None

    channel_id = get_channel_id(route)
    if isinstance(language, Language):
        message_text = render_text(text, language, substitutions)
    else:
        message_text = '\n---\n'.join([render_text(text, current_lang, substitutions) for current_lang in language])
    return await inter.client.get_channel(channel_id).send(message_text)
