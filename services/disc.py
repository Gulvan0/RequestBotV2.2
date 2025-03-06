from dataclasses import dataclass
from os import PathLike

import discord
from discord import Embed, File, Locale, Member, Message, NotFound, Role, User
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

import typing as tp


MESSAGE_LENGTH_LIMIT = 2000
MAX_SPLIT_MESSAGE_PORTIONS = 10


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


def split_message_to_fit_limit(message: str, extra_portion_symbols: int = 0) -> list[str]:
    actual_max_length = MESSAGE_LENGTH_LIMIT - extra_portion_symbols

    if len(message) <= actual_max_length:
        return [message]

    message_portions = []
    index_from = 0
    while len(message_portions) < MAX_SPLIT_MESSAGE_PORTIONS and index_from < len(message):
        index_to = index_from + actual_max_length
        for better_index_to_candidate in range(index_to, index_to - 20, -1):
            if message[better_index_to_candidate].isspace():
                index_to = better_index_to_candidate
                break
        message_portions.append(message[index_from:index_to])
        index_from = index_to
    return message_portions


async def respond(
    inter: discord.Interaction,
    template: str | list[str] | Template | TextPieceID,
    substitutions: dict[str, str | TextPieceID] | None = None,
    ephemeral: bool = False,
    view: tp.Callable[[Language], discord.ui.View] | None = None
) -> None:
    lang = Language.EN
    if isinstance(template, TextPieceID):
        member_language_info = member_language(inter.user, inter.locale)
        lang = member_language_info.language
        message_text = render_text(template, lang, substitutions or {})
        if member_language_info.is_assumed:
            subtext_language = Language.EN if lang == Language.RU else Language.RU
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

    if inter.response.is_done():
        await inter.edit_original_response(content=message_text, view=view(lang) if view else None)
    else:
        try:
            if view:
                await inter.response.send_message(message_text, ephemeral=ephemeral, view=view(lang))
            else:
                await inter.response.send_message(message_text, ephemeral=ephemeral)
        except discord.errors.NotFound:
            pass


async def respond_forbidden(inter: discord.Interaction) -> None:
    await respond(inter, TextPieceID.ERROR_FORBIDDEN, dict(admin_mention=as_user(get_stage_parameter_value(StageParameterID.ADMIN_USER_ID))), ephemeral=True)


async def send_developers(message: str, code_syntax: str | None = None, file_path: str | PathLike | None = None):
    extra_symbols = 8 + len(code_syntax) if code_syntax is not None else 0  # Triple backtick plus newline at both sides (3+1)*2 = 8
    developer_user_ids: list[int] = get_stage_parameter_value(StageParameterID.DEVELOPER_USER_IDS)

    is_first_portion = True
    for portion in split_message_to_fit_limit(message, extra_symbols):
        for developer_user_id in developer_user_ids:
            developer = await CONFIG.bot.fetch_user(developer_user_id)
            await developer.send(
                as_code_block(portion, code_syntax or None) if code_syntax is not None else portion,
                file=File(file_path) if file_path and is_first_portion else None
            )
        is_first_portion = False


def requires_permission(permission: PermissionFlagID | list[PermissionFlagID]):
    async def predicate(inter: discord.Interaction):
        return has_permission(inter.user, permission)
    return commands.check(predicate)


async def post_raw_text(
    route: RouteID,
    text: str | None = None,
    view: discord.ui.View | None = None,
    embed: Embed | None = None,
    file_path: str | None = None
) -> Message | None:
    if not is_enabled(route):
        return None
    channel_id = get_channel_id(route)
    channel = CONFIG.bot.get_channel(channel_id)
    returned_message = None
    is_first_portion = True
    for portion in split_message_to_fit_limit(text or ""):
        posted_portion = await channel.send(portion, view=view, embed=embed, file=File(file_path) if file_path and is_first_portion else None)
        if is_first_portion:
            returned_message = posted_portion
        is_first_portion = False
    return returned_message


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


async def find_member(user_id: int) -> Member | None:
    try:
        return await CONFIG.guild.fetch_member(user_id)
    except NotFound:
        return None


async def get_role(role_id: int) -> Role | None:
    return await CONFIG.guild.get_role(role_id)


def get_default_role() -> Role:
    return CONFIG.guild.default_role
