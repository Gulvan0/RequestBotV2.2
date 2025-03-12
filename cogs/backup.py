import datetime
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks

from database.db import replace_file, SQLITE_FILE_NAME
from services.disc import CheckDeferringBehaviour, requires_permission, respond, send_developers
from util.format import as_timestamp, TimestampStyle
from util.identifiers import PermissionFlagID, TextPieceID


class BackupCog(commands.GroupCog, name="backup", description="Commands for managing backups"):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.my_task.start()

    async def cog_unload(self) -> None:
        self.my_task.stop()

    @staticmethod
    async def backup() -> None:
        time_now = time.time()
        absolute_time = as_timestamp(time_now, TimestampStyle.LONG_DATETIME)
        relative_time = as_timestamp(time_now, TimestampStyle.RELATIVE)
        await send_developers(f'BACKUP {absolute_time} ({relative_time})', file_path=SQLITE_FILE_NAME)

    @tasks.loop(time=datetime.time(hour=1, tzinfo=datetime.UTC))
    async def my_task(self) -> None:
        await self.backup()

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_BACKUP_SAVE.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def save(self, inter: discord.Interaction) -> None:
        await self.backup()
        await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_BACKUP_LOAD.as_locale_str())
    @app_commands.describe(file=TextPieceID.COMMAND_OPTION_BACKUP_LOAD_FILE.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def load(self, inter: discord.Interaction, file: discord.Attachment) -> None:
        downloaded_file_path = Path('data/new.db')
        await file.save(downloaded_file_path)
        await replace_file(downloaded_file_path)
        await respond(inter, TextPieceID.COMMON_SUCCESS)


async def setup(bot):
    await bot.add_cog(BackupCog(bot))