from dataclasses import dataclass
from os import PathLike

import discord
from discord import File, Locale, Message
from discord.app_commands import commands

from config.stage_parameters import get_value as get_stage_parameter_value
from globalconf import CONFIG
from facades.permissions import has_permission
from facades.routes import get_channel_id, is_enabled
from facades.texts import render_text
from facades.user_preferences import get_value as get_preference_value
from util.datatypes import Language
from util.format import as_code_block, as_user
from util.identifiers import PermissionFlagID, RouteID, StageParameterID, TextPieceID, UserPreferenceID
from string import Template


MESSAGE_LENGTH_LIMIT = 2000


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


async def respond(
    inter: discord.Interaction,
    template: str | list[str] | Template | TextPieceID,
    substitutions: dict[str, str | TextPieceID] | None = None,
    ephemeral: bool = False,
    followup: bool = False
) -> None:
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

    if followup:
        await inter.edit_original_response(content=message_text)
    else:
        try:
            await inter.response.send_message(message_text, ephemeral=ephemeral)
        except discord.errors.NotFound:
            pass


async def respond_forbidden(inter: discord.Interaction) -> None:
    await respond(inter, TextPieceID.ERROR_FORBIDDEN, dict(admin_mention=as_user(get_stage_parameter_value(StageParameterID.ADMIN_USER_ID))), ephemeral=True)


async def send_developers(message: str, code_syntax: str | None = None, file_path: str | PathLike | None = None):
    extra_symbols = 8 + len(code_syntax) if code_syntax is not None else 0
    actual_max_length = MESSAGE_LENGTH_LIMIT - extra_symbols

    message_length = len(message)

    if message_length > actual_max_length:
        parts_cnt = (message_length - 1) // actual_max_length + 1
        for part_index in range(min(parts_cnt, 10)):
            index_from = actual_max_length * part_index
            index_to = index_from + actual_max_length
            await send_developers(message[index_from:index_to], code_syntax, file_path if part_index == 0 else None)
        return

    developer_user_ids: list[int] = get_stage_parameter_value(StageParameterID.DEVELOPER_USER_IDS)
    for developer_user_id in developer_user_ids:
        developer = await CONFIG.bot.fetch_user(developer_user_id)
        await developer.send(
            as_code_block(message, code_syntax or None) if code_syntax is not None else message,
            file=File(file_path) if file_path else None
        )


def requires_permission(permission: PermissionFlagID):
    async def predicate(inter: discord.Interaction):
        return has_permission(inter.user, permission)
    return commands.check(predicate)


async def post_raw_text(
    route: RouteID,
    text: str,
    view: discord.ui.View | None = None
) -> Message | None:
    if not is_enabled(route):
        return None
    channel_id = get_channel_id(route)
    return await CONFIG.bot.get_channel(channel_id).send(text, view=view)


async def post(
    route: RouteID,
    text: TextPieceID,
    language: Language | list[Language] | tuple[Language, ...] = (Language.RU, Language.EN),
    substitutions: dict[str, str | TextPieceID] | None = None
) -> Message | None:
    if isinstance(language, Language):
        message_text = render_text(text, language, substitutions or {})
    else:
        message_text = '\n---\n'.join([render_text(text, current_lang, substitutions or {}) for current_lang in language])
    return await post_raw_text(route, message_text)


async def find_message(channel_id: int, message_id: int) -> Message | None:
    channel = CONFIG.bot.get_channel(channel_id)
    if channel:
        return await channel.fetch_message(message_id)
    return None
