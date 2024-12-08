import discord

from discord import app_commands, Member
from discord.ext import commands
from cog_presets.cooldown import CooldownPreset
from services.disc import requires_permission
from util.datatypes import CooldownEntity, CooldownListingOption
from util.identifiers import PermissionFlagID


class UserCooldownCog(commands.GroupCog, name="usercd", description="Commands for managing user cooldowns and bans"):
    def __init__(self):
        self.preset: CooldownPreset = CooldownPreset(CooldownEntity.USER, PermissionFlagID.REMOVE_OTHER_USER_BANS)

    @app_commands.command(description="List users currently on cooldown")
    @app_commands.describe(cooldown_listing_type="Whether to display temporary or endless cooldowns")
    @requires_permission(PermissionFlagID.BAN_USERS)
    async def list(self, inter: discord.Interaction, cooldown_listing_type: CooldownListingOption) -> None:
        await self.preset.list(inter, cooldown_listing_type)

    @app_commands.command(description="Describe the given user's current cooldown")
    @app_commands.describe(user="User whose cooldown will be described")
    @requires_permission(PermissionFlagID.BAN_USERS)
    async def describe(self, inter: discord.Interaction, user: Member) -> None:
        await self.preset.describe(inter, user.id)

    @app_commands.command(description="Remove current cooldown for user")
    @app_commands.describe(
        user="User whose cooldown is to be removed",
        reason="Why the cooldown is being removed"
    )
    @requires_permission(PermissionFlagID.BAN_USERS)
    async def amend(self, inter: discord.Interaction, user: Member, reason: str | None = None) -> None:
        await self.preset.amend(inter, user.id, reason)

    @app_commands.command(description="Put a user on a cooldown or modify the cooldown this user currently has")
    @app_commands.describe(
        user="User whose cooldown is to be set",
        duration="Cooldown duration (absolute, relative to the current one or infinite). Format: /help duration",
        reason="Why the cooldown is being casted/updated"
    )
    @requires_permission(PermissionFlagID.BAN_USERS)
    async def update(self, inter: discord.Interaction, user: Member, duration: str, reason: str | None = None) -> None:
        await self.preset.update(inter, user.id, duration, reason)


async def setup(bot):
    await bot.add_cog(UserCooldownCog())