import traceback
import aiohttp
import click
import discord
import logging
import os
import typing as tp

from discord.ext import commands
from discord.utils import _ColourFormatter
from config.texts import validate as validate_texts
from config.routes import validate as validate_routes
from config.parameters import validate as validate_parameters
from config.stage_parameters import validate as validate_stage_parameters
from database.db import create_db_and_tables
from database.models import *  # noqa
from globalconf import CONFIG
from util.datatypes import Stage


class RequestBot(commands.Bot):
    client: aiohttp.ClientSession

    def __init__(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = _ColourFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.ext_dir = "cogs"
        self.synced = False

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(*args, **kwargs, command_prefix=commands.when_mentioned, intents=intents)

    async def on_ready(self) -> None:
        self.logger.info(f"Logged in as {self.user} ({self.user.id})")

    async def _load_extensions(self) -> None:
        if not os.path.isdir(self.ext_dir):
            self.logger.error(f"Extension directory {self.ext_dir} does not exist.")
            return

        for filename in os.listdir(self.ext_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    await self.load_extension(f"{self.ext_dir}.{filename[:-3]}")
                    self.logger.info(f"Loaded extension {filename[:-3]}")
                except commands.ExtensionError:
                    self.logger.error(f"Failed to load extension {filename[:-3]}\n{traceback.format_exc()}")

    async def on_error(self, event_method: str, *args: tp.Any, **kwargs: tp.Any) -> None:
        self.logger.error(f"An error occurred in {event_method}.\n{traceback.format_exc()}")

    async def close(self) -> None:
        await super().close()
        await self.client.close()

    async def setup_hook(self) -> None:
        self.client = aiohttp.ClientSession()
        await self._load_extensions()

        guild_id = 992102986052534292 if CONFIG.stage == Stage.PROD else 942429314434088990
        guild = discord.Object(id=guild_id)

        if not self.synced:
            self.tree.copy_global_to(guild=guild)
            result = await self.tree.sync(guild=guild)
            self.synced = not self.synced
            self.logger.info(f"Synced command tree: {len(result)} commands")
    def run(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        try:
            super().run(os.getenv("BOT_TOKEN"), *args, **kwargs)
        except (discord.LoginFailure, KeyboardInterrupt):
            self.logger.info("Exiting...")
            exit()


@click.command
@click.option(
    "--debug",
    is_flag=True,
    help="Use testing server"
)
@click.option(
    "--log_queries",
    is_flag=True,
    help="Log queries to the output"
)
def main(debug: bool, log_queries: bool) -> None:
    if log_queries:
        logger = logging.getLogger('sqlalchemy.engine')
        logger.setLevel(logging.DEBUG)

    CONFIG.stage = Stage.TEST if debug else Stage.PROD

    create_db_and_tables()

    validate_texts()
    validate_routes()
    validate_parameters()
    validate_stage_parameters()

    bot = RequestBot()
    bot.run()


if __name__ == "__main__":
    main()