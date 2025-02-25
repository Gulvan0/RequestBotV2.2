from datetime import date
from pathlib import Path

import typing as tp
import discord
from discord import app_commands, File
from discord.ext import commands

from services.disc import requires_permission, respond
from util.datatypes import ReportRange
from util.identifiers import PermissionFlagID, TextPieceID
from dateutil.parser import parse as parse_datetime, ParserError

import facades.reports
from util.time import to_end_of_week, to_start_of_week


class ReportCog(commands.GroupCog, name="report", description="Commands for displaying various reports"):
    @staticmethod
    async def prepare_range(inter: discord.Interaction, date_from: str | None = None, date_to: str | None = None, by_week: bool = False) -> ReportRange | None:
        parsed_date_from = None
        if date_from:
            try:
                parsed_date_from = parse_datetime(date_from).date()
            except ParserError:
                await respond(inter, TextPieceID.ERROR_CANT_PARSE_TIMESTAMP, substitutions=dict(raw=date_from), ephemeral=True)
                return None
        parsed_date_to = date.today()
        if date_to:
            try:
                parsed_date_to = parse_datetime(date_to).date()
            except ParserError:
                await respond(inter, TextPieceID.ERROR_CANT_PARSE_TIMESTAMP, substitutions=dict(raw=date_to), ephemeral=True)
                return None

        if parsed_date_from and parsed_date_from > parsed_date_to:
            parsed_date_from, parsed_date_to = parsed_date_to, parsed_date_from

        if by_week:
            if parsed_date_from:
                parsed_date_from = to_start_of_week(parsed_date_from)
            parsed_date_to = to_end_of_week(parsed_date_to)

        return ReportRange(
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            weekly_granularity=by_week
        )

    async def simple_report_command(
        self,
        report_generator: tp.Callable[[ReportRange], str],
        inter: discord.Interaction,
        date_from: str | None = None,
        date_to: str | None = None,
        by_week: bool = False
    ):
        await inter.response.defer(ephemeral=True, thinking=True)

        report_range = await self.prepare_range(inter, date_from, date_to, by_week)
        if not report_range:
            return

        image_path = report_generator(report_range)
        await inter.edit_original_response(attachments=[File(image_path)])
        Path(image_path).unlink()

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_NEW_REQUESTS.as_locale_str())
    @app_commands.describe(
        date_from=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_FROM.as_locale_str(),
        date_to=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_TO.as_locale_str(),
        by_week=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_TO.as_locale_str(),  # TODO
    )
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def new_requests(self, inter: discord.Interaction, date_from: str | None = None, date_to: str | None = None, by_week: bool = False) -> None:
        await self.simple_report_command(facades.reports.new_requests, inter, date_from, date_to, by_week)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_NEW_REQUESTS.as_locale_str())  # TODO
    @app_commands.describe(
        date_from=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_FROM.as_locale_str(),  # TODO
        date_to=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_TO.as_locale_str(),  # TODO
        by_week=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_TS_TO.as_locale_str(),  # TODO
    )
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def pending_requests(self, inter: discord.Interaction, date_from: str | None = None, date_to: str | None = None, by_week: bool = False) -> None:
        await self.simple_report_command(facades.reports.pending_requests, inter, date_from, date_to, by_week)

async def setup(bot):
    await bot.add_cog(ReportCog(bot))