import discord

from discord import app_commands
from discord.ext import commands
from cog_presets.cooldown import CooldownPreset
from services.disc import requires_permission
from util.datatypes import CooldownEntity, CooldownListingOption
from util.identifiers import PermissionFlagID, TextPieceID


class LevelCooldownCog(commands.GroupCog, name="levelcd", description="Commands for managing level cooldowns and bans"):
    def __init__(self):
        self.preset: CooldownPreset = CooldownPreset(CooldownEntity.LEVEL, PermissionFlagID.REMOVE_OTHER_LEVEL_BANS)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LEVELCD_LIST.as_locale_str())
    @app_commands.describe(cooldown_listing_type=TextPieceID.COMMAND_OPTION_LEVELCD_LIST_COOLDOWN_LISTING_TYPE.as_locale_str())
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def list(self, inter: discord.Interaction, cooldown_listing_type: CooldownListingOption) -> None:
        await self.preset.list(inter, cooldown_listing_type)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LEVELCD_DESCRIBE.as_locale_str())
    @app_commands.describe(level_id=TextPieceID.COMMAND_OPTION_LEVELCD_DESCRIBE_LEVEL_ID.as_locale_str())
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def describe(self, inter: discord.Interaction, level_id: int) -> None:
        await self.preset.describe(inter, level_id)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LEVELCD_AMEND.as_locale_str())
    @app_commands.describe(
        level_id=TextPieceID.COMMAND_OPTION_LEVELCD_AMEND_LEVEL_ID.as_locale_str(),
        reason=TextPieceID.COMMAND_OPTION_LEVELCD_AMEND_REASON.as_locale_str()
    )
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def amend(self, inter: discord.Interaction, level_id: int, reason: str | None = None) -> None:
        await self.preset.amend(inter, level_id, reason)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LEVELCD_UPDATE.as_locale_str())
    @app_commands.describe(
        level_id=TextPieceID.COMMAND_OPTION_LEVELCD_UPDATE_LEVEL_ID.as_locale_str(),
        duration=TextPieceID.COMMAND_OPTION_LEVELCD_UPDATE_DURATION.as_locale_str(),
        reason=TextPieceID.COMMAND_OPTION_LEVELCD_UPDATE_REASON.as_locale_str()
    )
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def update(self, inter: discord.Interaction, level_id: int, duration: str, reason: str | None = None) -> None:
        await self.preset.update(inter, level_id, duration, reason)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LEVELCD_HISTORY.as_locale_str())
    @app_commands.describe(level_id=TextPieceID.COMMAND_OPTION_LEVELCD_HISTORY_LEVEL_ID.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def history(self, inter: discord.Interaction, level_id: int) -> None:
        await self.preset.history(inter, level_id)


async def setup(bot):
    await bot.add_cog(LevelCooldownCog())