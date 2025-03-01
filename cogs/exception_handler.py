import traceback

import discord
from discord.app_commands import CheckFailure
from discord.ext import commands

from main import RequestBot
from services.disc import respond, respond_forbidden, send_developers
from util.format import as_code_block, as_user
from util.identifiers import StageParameterID, TextPieceID
from config.stage_parameters import get_value as get_stage_parameter_value


class ExceptionHandler(commands.Cog):
    def __init__(self, bot: RequestBot):
        self.bot = bot

        bot.tree.error(coro = self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, inter: discord.Interaction, error: discord.app_commands.AppCommandError):
        self.bot.dispatch("app_command_error", inter, error)

    @commands.Cog.listener("on_app_command_error")
    async def get_app_command_error(self, inter: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, CheckFailure):
            await respond_forbidden(inter)
        else:
            raw_error_message = str(error) + '\n' + ''.join(traceback.format_exception(error))

            self.bot.logger.error(raw_error_message)

            try:
                await respond(inter, TextPieceID.ERROR_COMMAND_ERROR, substitutions=dict(
                    admin_mention=as_user(get_stage_parameter_value(StageParameterID.ADMIN_USER_ID)),
                    error_traceback=as_code_block(raw_error_message[:1000])
                ), ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.NotFound, discord.errors.HTTPException):
                pass

            await send_developers(raw_error_message, "py")

async def setup(bot: RequestBot):
    await bot.add_cog(ExceptionHandler(bot))