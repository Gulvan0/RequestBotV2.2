import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, View

from components.modals.request_submission import RequestSubmissionModal
from facades.parameters import get_value as get_parameter_value
from facades.cooldowns import get_current_cooldown_eagerly
from facades.permissions import has_permission
from facades.requests import (
    assert_level_requestable, count_pending_requests, create_limbo_request, get_last_complete_request, get_oldest_ignored_request, get_oldest_unresolved_request, LevelAlreadyApprovedException,
    PreviousLevelRequestPendingException,
)
from facades.texts import render_text
from services.disc import find_message, member_language, requires_permission, respond
from services.gd import get_level, LevelGrade
from util.datatypes import CooldownEntity
from util.format import as_code, as_link, as_timestamp, as_user
from util.identifiers import ParameterID, PermissionFlagID, StageParameterID, TextPieceID
from config.stage_parameters import get_value as get_stage_parameter_value


class RequestCog(commands.GroupCog, name="request", description="Commands for managing requests"):
    @staticmethod
    async def check_request_cooldown(inter: Interaction, entity: CooldownEntity, entity_id: int, level_name: str | None = None) -> bool:
        current_cd_info = get_current_cooldown_eagerly(entity, entity_id)
        if not current_cd_info:
            return False

        current_cd = current_cd_info.cooldown
        if current_cd_info.causing_request:
            if entity == CooldownEntity.USER:
                prev_level = await get_level(current_cd_info.causing_request.level_id)
                text_piece_id = TextPieceID.REQUEST_COMMAND_USER_ON_COOLDOWN
                substitutions = dict(
                    ends_at=as_timestamp(current_cd.exact_ends_at),
                    prev_level_name=prev_level.name,
                    prev_request_ts=as_timestamp(current_cd_info.causing_request.requested_at)
                )
            else:
                text_piece_id = TextPieceID.REQUEST_COMMAND_LEVEL_ON_COOLDOWN
                substitutions = dict(
                    ends_at=as_timestamp(current_cd.exact_ends_at),
                    prev_request_author=current_cd_info.causing_request.request_author_mention,
                    prev_request_ts=as_timestamp(current_cd_info.causing_request.requested_at)
                )
        elif current_cd.ends_at:
            text_piece_id = TextPieceID.REQUEST_COMMAND_USER_BANNED_TEMPORARILY if entity == CooldownEntity.USER else TextPieceID.REQUEST_COMMAND_LEVEL_BANNED_TEMPORARILY
            substitutions = dict(
                ends_at=as_timestamp(current_cd.exact_ends_at),
                responsible_mention=as_user(current_cd.caster_user_id),
                reason=as_code(current_cd.reason) if current_cd.reason else TextPieceID.COMMON_NOT_SPECIFIED,
                admin_mention=as_user(get_stage_parameter_value(StageParameterID.ADMIN_USER_ID))
            )
        else:
            text_piece_id = TextPieceID.REQUEST_COMMAND_USER_BANNED_FOREVER if entity == CooldownEntity.USER else TextPieceID.REQUEST_COMMAND_LEVEL_BANNED_FOREVER
            substitutions = dict(
                responsible_mention=as_user(current_cd.caster_user_id),
                reason=as_code(current_cd.reason) if current_cd.reason else TextPieceID.COMMON_NOT_SPECIFIED,
                admin_mention=as_user(get_stage_parameter_value(StageParameterID.ADMIN_USER_ID))
            )

        if level_name:
            substitutions.update(level_name=level_name)

        await respond(inter, text_piece_id, substitutions, ephemeral=True)

        return True

    @app_commands.command(description="Request a level")
    @app_commands.describe(level_id="ID of a level you want to request")
    async def create(self, inter: discord.Interaction, level_id: app_commands.Range[int, 200, 1000000000]) -> None:
        await inter.response.defer(ephemeral=True)

        if get_parameter_value(ParameterID.QUEUE_BLOCKED, bool) and not has_permission(inter.user, PermissionFlagID.REQUEST_WHILE_QUEUE_CLOSED):
            await respond(inter, TextPieceID.QUEUE_QUEUE_CLOSED_ERROR, ephemeral=True)
            return

        if not has_permission(inter.user, PermissionFlagID.NO_REQUEST_COOLDOWN) and await self.check_request_cooldown(inter, CooldownEntity.USER, inter.user.id):
            return

        try:
            assert_level_requestable(level_id)
        except LevelAlreadyApprovedException as e:
            await respond(
                inter,
                TextPieceID.REQUEST_COMMAND_ALREADY_APPROVED,
                dict(
                    approval_ts=as_timestamp(e.resolved_at),
                    request_ts=as_timestamp(e.requested_at),
                    orig_author=e.request_author_mention
                ),
                ephemeral=True
            )
            return
        except PreviousLevelRequestPendingException as e:
            await respond(
                inter,
                TextPieceID.REQUEST_COMMAND_PREVIOUS_PENDING,
                dict(
                    request_ts=as_timestamp(e.requested_at),
                    orig_author=e.request_author_mention
                ),
                ephemeral=True
            )
            return

        level = await get_level(level_id)

        if not level:
            await respond(inter, TextPieceID.REQUEST_COMMAND_NOT_FOUND, dict(level_id=str(level_id)), ephemeral=True)
            return

        if await self.check_request_cooldown(inter, CooldownEntity.LEVEL, level_id, level.name):
            return

        if level.grade != LevelGrade.UNRATED:
            await respond(
                inter,
                TextPieceID.REQUEST_COMMAND_ALREADY_RATED,
                dict(
                    level_name=as_code(level.name),
                    level_quality=level.grade.to_str()
                ),
                ephemeral=True
            )
            return

        request_language = member_language(inter.user, inter.locale).language

        request_id = await create_limbo_request(level_id, request_language, inter.user)

        # TODO: Remove defer call and replace these lines with just response.send_modal() upon release
        async def show_modal(inter) -> None:
            await inter.response.send_modal(RequestSubmissionModal(request_id, request_language))
        continue_view = View()
        btn = Button(label="Continue")
        btn.callback = show_modal
        continue_view.add_item(btn)
        await inter.edit_original_response(content="", view=continue_view)

    @app_commands.command(description="Get widget links for a requested level")
    @app_commands.describe(level_id="ID of a level you want to get the widgets of")
    @requires_permission(PermissionFlagID.GD_MOD)
    async def widgets(self, inter: discord.Interaction, level_id: app_commands.Range[int, 200, 1000000000]) -> None:
        await inter.response.defer(ephemeral=True)

        request = await get_last_complete_request(level_id)
        if not request or not request.details_message_channel_id or not request.details_message_id:
            await respond(inter, TextPieceID.REQUEST_INFO_REQUEST_NOT_FOUND, ephemeral=True)
            return

        user_lang = member_language(inter.user, inter.locale).language
        details_message = await find_message(request.details_message_channel_id, request.details_message_id)
        response_text = as_link(details_message.jump_url, render_text(TextPieceID.REQUEST_INFO_REVIEWERS_WIDGET_LINK_TEXT, user_lang))
        if request.resolution_message_channel_id and request.resolution_message_id:
            resolution_widget = await find_message(request.resolution_message_channel_id, request.resolution_message_id)
            response_text += "\n" + as_link(resolution_widget.jump_url, render_text(TextPieceID.REQUEST_INFO_MODERATORS_WIDGET_LINK_TEXT, user_lang))

        await respond(inter, response_text, ephemeral=True)

    @app_commands.command(description="Get widget links for a requested level")
    @requires_permission(PermissionFlagID.REVIEWER)
    async def ignored(self, inter: discord.Interaction) -> None:
        await inter.response.defer(ephemeral=True)

        request = await get_oldest_ignored_request()
        if not request or not request.details_message_channel_id or not request.details_message_id:
            await respond(inter, TextPieceID.REQUEST_NO_IGNORED, ephemeral=True)
            return

        user_lang = member_language(inter.user, inter.locale).language
        details_message = await find_message(request.details_message_channel_id, request.details_message_id)
        response_text = as_link(details_message.jump_url, render_text(TextPieceID.REQUEST_INFO_REVIEWERS_WIDGET_LINK_TEXT, user_lang))

        await respond(inter, response_text, ephemeral=True)

    @app_commands.command(description="Get widget links for a requested level")
    @requires_permission(PermissionFlagID.GD_MOD)
    async def unresolved(self, inter: discord.Interaction) -> None:
        await inter.response.defer(ephemeral=True)

        request = await get_oldest_unresolved_request()
        if not request or not request.resolution_message_id or not request.resolution_message_channel_id:
            await respond(inter, TextPieceID.REQUEST_NO_UNRESOLVED, ephemeral=True)
            return

        user_lang = member_language(inter.user, inter.locale).language
        resolution_widget = await find_message(request.resolution_message_channel_id, request.resolution_message_id)
        response_text = as_link(resolution_widget.jump_url, render_text(TextPieceID.REQUEST_INFO_MODERATORS_WIDGET_LINK_TEXT, user_lang))

        await respond(inter, response_text, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RequestCog(bot))