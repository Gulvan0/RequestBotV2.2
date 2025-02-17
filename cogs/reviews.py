import discord
from discord import app_commands, Member
from discord.ext import commands

from components.views.pagination.list import ListPaginationView
from facades.reviews import get_level_reviews, get_user_reviews
from services.disc import find_message, respond
from util.format import as_link
from util.identifiers import TextPieceID


class ReviewsCog(commands.GroupCog, name="reviews", description="Commands for managing reviews"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REVIEWS_LEVEL.as_locale_str())
    @app_commands.describe(level_id=TextPieceID.COMMAND_OPTION_REVIEWS_LEVEL_LEVEL_ID.as_locale_str())
    async def level(self, inter: discord.Interaction, level_id: app_commands.Range[int, 200, 1000000000]) -> None:
        await inter.response.defer(ephemeral=True)

        reviews = await get_level_reviews(level_id)

        response_lines = []
        for review in reviews:
            review_message = await find_message(review.message_channel_id, review.message_id)
            if not review_message:
                continue
            response_lines.append(as_link(review_message.jump_url, str(review_message.id)))

        if not response_lines:
            await respond(inter, TextPieceID.REQUEST_NO_REVIEWS, ephemeral=True)
            return

        await respond(inter, response_lines, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_REVIEWS_USER.as_locale_str())
    @app_commands.describe(author=TextPieceID.COMMAND_OPTION_REVIEWS_USER_AUTHOR.as_locale_str())
    async def user(self, inter: discord.Interaction, author: Member) -> None:
        await inter.response.defer(ephemeral=True)

        reviews = await get_user_reviews(author)

        response_lines = []
        for review in reviews:
            review_message = await find_message(review.message_channel_id, review.message_id)
            if not review_message:
                continue
            response_lines.append(as_link(review_message.jump_url, str(review_message.id)))

        if not response_lines:
            await respond(inter, TextPieceID.REQUEST_NO_REVIEWS, ephemeral=True)
            return

        await ListPaginationView(response_lines).respond_with_view(inter, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReviewsCog(bot))