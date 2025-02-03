import traceback

import aiohttp
import click
import discord
import logging
import os
import typing as tp

from discord import InteractionType
from discord.ext import commands
from discord.utils import _ColourFormatter

from components.modals.approval import ApprovalModal
from components.modals.pre_approval import PreApprovalModal
from components.modals.pre_rejection import PreRejectionModal
from components.modals.pre_rejection_no_review import PreRejectionNoReviewModal
from components.modals.rejection import RejectionModal
from components.modals.request_submission import RequestSubmissionModal
from components.views.pending_request_widget import PendingRequestWidgetApproveAndReviewBtn, PendingRequestWidgetJustApproveBtn, PendingRequestWidgetJustRejectBtn, PendingRequestWidgetRejectAndReviewBtn
from components.views.resolution_widget import ResolutionWidgetEpicBtn, ResolutionWidgetFeatureBtn, ResolutionWidgetLegendaryBtn, ResolutionWidgetMythicBtn, ResolutionWidgetRejectBtn, ResolutionWidgetStarrateBtn
from config.texts import validate as validate_texts
from config.routes import validate as validate_routes
from config.parameters import validate as validate_parameters
from config.stage_parameters import validate as validate_stage_parameters
from config.permission_flags import validate as validate_permission_flags
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

        self.add_dynamic_items(PendingRequestWidgetApproveAndReviewBtn)
        self.add_dynamic_items(PendingRequestWidgetRejectAndReviewBtn)
        self.add_dynamic_items(PendingRequestWidgetJustApproveBtn)
        self.add_dynamic_items(PendingRequestWidgetJustRejectBtn)
        self.add_dynamic_items(ResolutionWidgetStarrateBtn)
        self.add_dynamic_items(ResolutionWidgetFeatureBtn)
        self.add_dynamic_items(ResolutionWidgetEpicBtn)
        self.add_dynamic_items(ResolutionWidgetMythicBtn)
        self.add_dynamic_items(ResolutionWidgetLegendaryBtn)
        self.add_dynamic_items(ResolutionWidgetRejectBtn)

    @staticmethod
    async def on_interaction(inter: discord.Interaction):
        custom_id = inter.data.get("custom_id")
        if custom_id and inter.type == InteractionType.modal_submit:
            if custom_id.startswith("rsm:"):
                await RequestSubmissionModal.handle_interaction(inter)
            elif custom_id.startswith("prnrm:"):
                await PreRejectionNoReviewModal.handle_interaction(inter)
            elif custom_id.startswith("prm:"):
                await PreRejectionModal.handle_interaction(inter)
            elif custom_id.startswith("pam:"):
                await PreApprovalModal.handle_interaction(inter)
            elif custom_id.startswith("am:"):
                await ApprovalModal.handle_interaction(inter)
            elif custom_id.startswith("rm:"):
                await RejectionModal.handle_interaction(inter)

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
    validate_permission_flags()

    CONFIG.bot = RequestBot()
    CONFIG.bot.run()


if __name__ == "__main__":
    main()