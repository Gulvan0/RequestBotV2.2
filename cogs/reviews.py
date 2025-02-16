import discord
from discord import app_commands, Member
from discord.ext import commands

from facades.reviews import get_level_reviews, get_user_reviews
from services.disc import find_message, respond
from util.format import as_link
from util.identifiers import TextPieceID


class ReviewsCog(commands.GroupCog, name="reviews", description="Commands for managing reviews"):
    @app_commands.command(description="Get all reviews written for a certain level. Won't include reviews written by trainees")
    @app_commands.describe(level_id="ID of a level you want to retrieve all reviews for")
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

    @app_commands.command(description="Get last 20 reviews written by a certain reviewer")
    @app_commands.describe(author="Author of the reviews to be retrieved")
    async def user(self, inter: discord.Interaction, author: Member) -> None:
        await inter.response.defer(ephemeral=True)

        reviews = await get_user_reviews(author)

        response_lines = []
        for review in reviews[:20]:
            review_message = await find_message(review.message_channel_id, review.message_id)
            if not review_message:
                continue
            response_lines.append(as_link(review_message.jump_url, str(review_message.id)))

        if not response_lines:
            await respond(inter, TextPieceID.REQUEST_NO_REVIEWS, ephemeral=True)
            return

        await respond(inter, response_lines, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReviewsCog(bot))