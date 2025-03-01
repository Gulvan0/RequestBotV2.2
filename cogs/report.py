from datetime import date
from functools import partial
from pathlib import Path

import typing as tp
import discord
from discord import app_commands, File, Member
from discord.ext import commands

from facades.texts import render_text
from services.disc import member_language, requires_permission, respond
from util.datatypes import CommandChoiceOption, ReportGranularity, ReportRange, SimpleReportRange
from util.identifiers import PermissionFlagID, TextPieceID
from dateutil.parser import parse as parse_datetime, ParserError

import facades.reports
from util.time import to_end_of_week, to_start_of_week


class ReportCog(commands.GroupCog, name="report", description="Commands for displaying various reports"):
    @staticmethod
    async def prepare_simple_range(inter: discord.Interaction, date_from: str | None, date_to: str | None) -> SimpleReportRange | None:
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

        return SimpleReportRange(
            date_from=parsed_date_from,
            date_to=parsed_date_to
        )

    @staticmethod
    async def prepare_range(inter: discord.Interaction, date_from: str | None, date_to: str | None, by_week: bool) -> ReportRange | None:
        simple_range = await ReportCog.prepare_simple_range(inter, date_from, date_to)
        parsed_date_from = simple_range.date_from
        parsed_date_to = simple_range.date_to

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
        report_generator: tp.Callable[[SimpleReportRange], tp.Coroutine[tp.Any, tp.Any, str | None]],
        inter: discord.Interaction,
        date_from: str | None = None,
        date_to: str | None = None
    ):
        await inter.response.defer(ephemeral=True, thinking=True)

        report_range = await self.prepare_simple_range(inter, date_from, date_to)
        if not report_range:
            return

        image_path = await report_generator(report_range)
        if not image_path:
            await inter.edit_original_response(content=render_text(TextPieceID.ERROR_REPORT_NO_DATA, member_language(inter.user, inter.locale).language))
            return

        await inter.edit_original_response(attachments=[File(image_path)])
        Path(image_path).unlink()

    async def granular_report_command(
        self,
        report_generator: tp.Callable[[ReportRange], tp.Coroutine[tp.Any, tp.Any, str | None]],
        inter: discord.Interaction,
        date_from: str | None = None,
        date_to: str | None = None,
        granularity: ReportGranularity = ReportGranularity.DAY
    ):
        await inter.response.defer(ephemeral=True, thinking=True)

        report_range = await self.prepare_range(inter, date_from, date_to, granularity == ReportGranularity.WEEK)
        if not report_range:
            return

        image_path = await report_generator(report_range)
        if not image_path:
            await inter.edit_original_response(content=render_text(TextPieceID.ERROR_REPORT_NO_DATA, member_language(inter.user, inter.locale).language))
            return

        await inter.edit_original_response(attachments=[File(image_path)])
        Path(image_path).unlink()

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_NEW_REQUESTS.as_locale_str())
    @app_commands.describe(
        date_from=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_DATE_FROM.as_locale_str(),
        date_to=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_DATE_TO.as_locale_str(),
        granularity=TextPieceID.COMMAND_OPTION_REPORT_NEW_REQUESTS_GRANULARITY.as_locale_str(),
    )
    @app_commands.choices(granularity=CommandChoiceOption.report_granularity())
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def new_requests(self, inter: discord.Interaction, date_from: str | None = None, date_to: str | None = None, granularity: ReportGranularity = ReportGranularity.DAY) -> None:
        await self.granular_report_command(facades.reports.new_requests, inter, date_from, date_to, granularity)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_PENDING_REQUESTS.as_locale_str())
    @app_commands.describe(
        date_from=TextPieceID.COMMAND_OPTION_REPORT_PENDING_REQUESTS_DATE_FROM.as_locale_str(),
        date_to=TextPieceID.COMMAND_OPTION_REPORT_PENDING_REQUESTS_DATE_TO.as_locale_str(),
        granularity=TextPieceID.COMMAND_OPTION_REPORT_PENDING_REQUESTS_GRANULARITY.as_locale_str(),
    )
    @app_commands.choices(granularity=CommandChoiceOption.report_granularity())
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def pending_requests(self, inter: discord.Interaction, date_from: str | None = None, date_to: str | None = None, granularity: ReportGranularity = ReportGranularity.DAY) -> None:
        await self.granular_report_command(facades.reports.pending_requests, inter, date_from, date_to, granularity)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_REVIEWER_OPINIONS.as_locale_str())
    @app_commands.describe(
        reviewer=TextPieceID.COMMAND_OPTION_REPORT_REVIEWER_OPINIONS_REVIEWER.as_locale_str(),
        date_from=TextPieceID.COMMAND_OPTION_REPORT_REVIEWER_OPINIONS_DATE_FROM.as_locale_str(),
        date_to=TextPieceID.COMMAND_OPTION_REPORT_REVIEWER_OPINIONS_DATE_TO.as_locale_str(),
    )
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def reviewer_opinions(self, inter: discord.Interaction, reviewer: Member, date_from: str | None = None, date_to: str | None = None) -> None:
        await self.simple_report_command(
            partial(facades.reports.reviewer_opinions, reviewer),
            inter,
            date_from,
            date_to
        )

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REPORT_REVIEW_ACTIVITY.as_locale_str())
    @app_commands.describe(
        date_from=TextPieceID.COMMAND_OPTION_REPORT_REVIEW_ACTIVITY_DATE_FROM.as_locale_str(),
        date_to=TextPieceID.COMMAND_OPTION_REPORT_REVIEW_ACTIVITY_DATE_TO.as_locale_str(),
        granularity=TextPieceID.COMMAND_OPTION_REPORT_REVIEW_ACTIVITY_GRANULARITY.as_locale_str(),
    )
    @app_commands.choices(granularity=CommandChoiceOption.report_granularity())
    @requires_permission(PermissionFlagID.REPORT_VIEWER)
    async def review_activity(self, inter: discord.Interaction, date_from: str | None = None, date_to: str | None = None, granularity: ReportGranularity = ReportGranularity.DAY) -> None:
        await self.granular_report_command(facades.reports.review_activity, inter, date_from, date_to, granularity)

async def setup(bot):
    await bot.add_cog(ReportCog(bot))