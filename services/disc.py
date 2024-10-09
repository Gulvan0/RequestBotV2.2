import discord
from discord import Message

from globalconf import CONFIG
from routes import get_channel_id, is_enabled
from texts import render_text
from util.datatypes import Language, Stage
from util.identifiers import RouteID, TextPieceID
from string import Template


SPEAKS_RUSSIAN_ROLE = {
    Stage.TEST: 1293687410651041907,
    Stage.PROD: 1065981580012691497
}


def member_language(member: discord.Member) -> Language:
    return Language.RU if member.get_role(SPEAKS_RUSSIAN_ROLE[CONFIG.stage]) is not None else Language.EN


async def respond(inter: discord.Interaction, template: str | Template | TextPieceID, substitutions: dict[str, str] | None = None, ephemeral: bool = False) -> None:
    if not substitutions:
        substitutions = {}

    if isinstance(template, TextPieceID):
        message_text = render_text(template, member_language(inter.user), substitutions)
    elif isinstance(template, Template):
        message_text = template.safe_substitute(substitutions)
    else:
        message_text = Template(template).safe_substitute(substitutions)

    await inter.response.send_message(message_text, ephemeral=ephemeral)


async def post(
    inter: discord.Interaction,
    language: Language | list[Language] | tuple[Language, ...],
    route: RouteID, text: TextPieceID,
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
