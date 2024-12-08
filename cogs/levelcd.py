import discord

from discord import app_commands
from discord.ext import commands
from cog_presets.cooldown import CooldownPreset
from services.disc import requires_permission
from util.datatypes import CooldownEntity, CooldownListingOption
from util.identifiers import PermissionFlagID


class LevelCooldownCog(commands.GroupCog, name="levelcd", description="Commands for managing level cooldowns and bans"):
    def __init__(self):
        self.preset: CooldownPreset = CooldownPreset(CooldownEntity.LEVEL, PermissionFlagID.REMOVE_OTHER_LEVEL_BANS)

    @app_commands.command(description="List levels currently on cooldown")
    @app_commands.describe(cooldown_listing_type="Whether to display temporary or endless cooldowns")
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def list(self, inter: discord.Interaction, cooldown_listing_type: CooldownListingOption) -> None:
        await self.preset.list(inter, cooldown_listing_type)

    @app_commands.command(description="Describe the given level's current cooldown")
    @app_commands.describe(level_id="ID of a level whose cooldown will be described")
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def describe(self, inter: discord.Interaction, level_id: int) -> None:
        await self.preset.describe(inter, level_id)

    @app_commands.command(description="Remove current cooldown for level")
    @app_commands.describe(
        level_id="ID of a level whose cooldown is to be removed",
        reason="Why the cooldown is being removed"
    )
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def amend(self, inter: discord.Interaction, level_id: int, reason: str | None = None) -> None:
        await self.preset.amend(inter, level_id, reason)

    @app_commands.command(description="Put a level on a cooldown or modify the cooldown this level currently has")
    @app_commands.describe(
        level_id="ID of a level whose cooldown is to be set",
        duration="Cooldown duration (absolute, relative to the current one or infinite). Format: /help duration",
        reason="Why the cooldown is being casted/updated"
    )
    @requires_permission(PermissionFlagID.BAN_LEVELS)
    async def update(self, inter: discord.Interaction, level_id: int, duration: str, reason: str | None = None) -> None:
        await self.preset.update(inter, level_id, duration, reason)


async def setup(bot):
    await bot.add_cog(LevelCooldownCog())