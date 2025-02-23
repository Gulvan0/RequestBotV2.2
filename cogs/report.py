from pathlib import Path

import discord
from discord import app_commands, File
from discord.ext import commands

from services.disc import requires_permission, respond
from util.identifiers import PermissionFlagID, TextPieceID
from dateutil.parser import parse as parse_datetime, ParserError

import facades.reports


class ReportCog(commands.GroupCog, name="report", description="Commands for displaying various reports"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_NEW_REQUESTS.as_locale_str())
    @app_commands.describe(
        ts_from=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_FROM.as_locale_str(),
        ts_to=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_TO.as_locale_str(),
    )
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def new_requests(self, inter: discord.Interaction, ts_from: str | None = None, ts_to: str | None = None) -> None:
        await inter.response.defer(ephemeral=True, thinking=True)

        parsed_ts_from = None
        if ts_from:
            try:
                parsed_ts_from = parse_datetime(ts_from)
            except ParserError:
                await respond(inter, TextPieceID.ERROR_CANT_PARSE_TIMESTAMP, substitutions=dict(raw=ts_from), ephemeral=True)
                return
        parsed_ts_to = None
        if ts_to:
            try:
                parsed_ts_to = parse_datetime(ts_to)
            except ParserError:
                await respond(inter, TextPieceID.ERROR_CANT_PARSE_TIMESTAMP, substitutions=dict(raw=ts_to), ephemeral=True)
                return

        if parsed_ts_from and parsed_ts_to and parsed_ts_from > parsed_ts_to:
            parsed_ts_from, parsed_ts_to = parsed_ts_to, parsed_ts_from

        image_path = facades.reports.new_requests(parsed_ts_from, parsed_ts_to, ":" not in ts_to if ts_to else False)
        await inter.edit_original_response(attachments=[File(image_path)])
        Path(image_path).unlink()

async def setup(bot):
    await bot.add_cog(ReportCog(bot))