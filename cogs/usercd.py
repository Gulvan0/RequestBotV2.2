import discord

from discord import app_commands, Member
from discord.ext import commands
from cog_presets.cooldown import CooldownPreset
from services.disc import CheckDeferringBehaviour, requires_permission
from util.datatypes import CommandChoiceOption, CooldownEntity, CooldownListingOption
from util.identifiers import PermissionFlagID, TextPieceID


class UserCooldownCog(commands.GroupCog, name="usercd", description="Commands for managing user cooldowns and bans"):
    def __init__(self):
        self.preset: CooldownPreset = CooldownPreset(CooldownEntity.USER, PermissionFlagID.REMOVE_OTHER_USER_BANS)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_USERCD_LIST.as_locale_str())
    @app_commands.describe(cooldown_listing_type=TextPieceID.COMMAND_OPTION_USERCD_LIST_COOLDOWN_LISTING_TYPE.as_locale_str())
    @app_commands.choices(cooldown_listing_type=CommandChoiceOption.cooldown_listing_type())
    @requires_permission(PermissionFlagID.BAN_USERS, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def list(self, inter: discord.Interaction, cooldown_listing_type: CooldownListingOption) -> None:
        await self.preset.list(inter, cooldown_listing_type)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_USERCD_DESCRIBE.as_locale_str())
    @app_commands.describe(user=TextPieceID.COMMAND_OPTION_USERCD_DESCRIBE_USER.as_locale_str())
    @requires_permission(PermissionFlagID.BAN_USERS, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def describe(self, inter: discord.Interaction, user: Member) -> None:
        await self.preset.describe(inter, user.id)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_USERCD_AMEND.as_locale_str())
    @app_commands.describe(
        user=TextPieceID.COMMAND_OPTION_USERCD_AMEND_USER.as_locale_str(),
        reason=TextPieceID.COMMAND_OPTION_USERCD_AMEND_REASON.as_locale_str()
    )
    @requires_permission(PermissionFlagID.BAN_USERS, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def amend(self, inter: discord.Interaction, user: Member, reason: str | None = None) -> None:
        await self.preset.amend(inter, user.id, reason)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_USERCD_UPDATE.as_locale_str())
    @app_commands.describe(
        user=TextPieceID.COMMAND_OPTION_USERCD_UPDATE_USER.as_locale_str(),
        duration=TextPieceID.COMMAND_OPTION_USERCD_UPDATE_DURATION.as_locale_str(),
        reason=TextPieceID.COMMAND_OPTION_USERCD_UPDATE_REASON.as_locale_str()
    )
    @requires_permission(PermissionFlagID.BAN_USERS, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def update(self, inter: discord.Interaction, user: Member, duration: str, reason: str | None = None) -> None:
        await self.preset.update(inter, user.id, duration, reason)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_USERCD_HISTORY.as_locale_str())
    @app_commands.describe(user=TextPieceID.COMMAND_OPTION_USERCD_HISTORY_USER.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def history(self, inter: discord.Interaction, user: Member) -> None:
        await self.preset.history(inter, user.id)


async def setup(bot):
    await bot.add_cog(UserCooldownCog())