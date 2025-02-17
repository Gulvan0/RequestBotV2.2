import asyncio
import traceback

import aiohttp
import click
import discord
import logging
import os
import typing as tp

import uvicorn
from discord import InteractionType
from discord.ext import commands
from discord.utils import _ColourFormatter
from fastapi import FastAPI
from pydantic import BaseModel, Field

from components.modals.approval import ApprovalModal
from components.modals.pre_approval import PreApprovalModal
from components.modals.pre_rejection import PreRejectionModal
from components.modals.pre_rejection_no_review import PreRejectionNoReviewModal
from components.modals.rejection import RejectionModal
from components.modals.request_submission import RequestSubmissionModal
from components.modals.trainee_review_feedback import TraineeReviewFeedbackModal
from components.views.pending_request_widget import PendingRequestWidgetApproveAndReviewBtn, PendingRequestWidgetJustApproveBtn, PendingRequestWidgetJustRejectBtn, PendingRequestWidgetRejectAndReviewBtn
from components.views.resolution_widget import ResolutionWidgetEpicBtn, ResolutionWidgetFeatureBtn, ResolutionWidgetLegendaryBtn, ResolutionWidgetMythicBtn, ResolutionWidgetRejectBtn, ResolutionWidgetStarrateBtn
from components.views.trainee_pick_widget import TraineePickWidgetAcceptBtn, TraineePickWidgetRejectBtn
from components.views.trainee_promotion_decision import TraineePromotionDecisionExpelBtn, TraineePromotionDecisionPromoteBtn, TraineePromotionDecisionWaitBtn
from components.views.trainee_review_widget import TraineeReviewWidgetAcceptBtn, TraineeReviewWidgetRejectBtn
from config.texts import validate as validate_texts
from config.routes import validate as validate_routes
from config.parameters import validate as validate_parameters
from config.stage_parameters import validate as validate_stage_parameters, get_value as get_stage_parameter_value
from config.permission_flags import validate as validate_permission_flags
from database.db import create_db_and_tables
from database.models import *  # noqa
from globalconf import CONFIG
from services.disc import post_raw_text
from util.datatypes import Stage
from util.identifiers import StageParameterID
from util.translator import Translator


class Message(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    target_route_id: RouteID


api_app = FastAPI()


@api_app.post("/send_message")
async def root(message: Message):
    await post_raw_text(message.target_route_id, message.text)


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
        self.guild_id = 0

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(*args, **kwargs, command_prefix=commands.when_mentioned, intents=intents)  # noqa

    async def on_ready(self) -> None:
        self.logger.info(f"Logged in as {self.user} ({self.user.id})")

        CONFIG.guild = self.get_guild(self.guild_id)
        assert CONFIG.guild

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

        self.guild_id = get_stage_parameter_value(StageParameterID.GUILD_ID)
        guild = discord.Object(id=self.guild_id)

        if not self.synced:
            self.tree.copy_global_to(guild=guild)
            await self.tree.set_translator(Translator())
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
        self.add_dynamic_items(TraineeReviewWidgetAcceptBtn)
        self.add_dynamic_items(TraineeReviewWidgetRejectBtn)
        self.add_dynamic_items(TraineePromotionDecisionPromoteBtn)
        self.add_dynamic_items(TraineePromotionDecisionExpelBtn)
        self.add_dynamic_items(TraineePromotionDecisionWaitBtn)
        self.add_dynamic_items(TraineePickWidgetAcceptBtn)
        self.add_dynamic_items(TraineePickWidgetRejectBtn)

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
            elif custom_id.startswith("trf:"):
                await TraineeReviewFeedbackModal.handle_interaction(inter)

    def start(self, *args: tp.Any, **kwargs: tp.Any) -> tp.Coroutine[tp.Any, tp.Any, None]:
        try:
            return super().start(os.getenv("BOT_TOKEN"), *args, **kwargs)
        except (discord.LoginFailure, KeyboardInterrupt):
            self.logger.info("Exiting...")
            exit()


async def start_api() -> None:
    config = uvicorn.Config(api_app, port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    CONFIG.bot = RequestBot()
    tasks = [
        loop.create_task(CONFIG.bot.start()),
        loop.create_task(start_api()),
    ]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    main()