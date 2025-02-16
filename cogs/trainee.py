from discord import app_commands, Interaction, Member
from discord.ext import commands

from facades.trainee import expel_trainee, NotATraineeException, promote_trainee, RoleNotAssociatedException
from services.disc import requires_permission, respond
from util.format import as_code
from util.identifiers import PermissionFlagID, TextPieceID


class TraineeCog(commands.GroupCog, name="trainee", description="Commands for working with the trainee system"):
    @app_commands.command(description="Promote a trainee to a regular reviewer")
    @app_commands.describe(trainee="Trainee to be promoted")
    @requires_permission(PermissionFlagID.TRAINEE_SUPERVISOR)
    async def promote(self, inter: Interaction, trainee: Member) -> None:
        try:
            await promote_trainee(trainee, inter.user)
        except RoleNotAssociatedException as e:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_ROLE_NOT_ASSOCIATED, substitutions=dict(permission=as_code(e.permission.value)), ephemeral=True)
        except NotATraineeException:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_NOT_A_TRAINEE, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Expel a member from the trainees")
    @app_commands.describe(trainee="Trainee to be expelled")
    @requires_permission(PermissionFlagID.TRAINEE_SUPERVISOR)
    async def expel(self, inter: Interaction, trainee: Member) -> None:
        try:
            await expel_trainee(trainee, inter.user)
        except RoleNotAssociatedException as e:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_ROLE_NOT_ASSOCIATED, substitutions=dict(permission=as_code(e.permission.value)), ephemeral=True)
        except NotATraineeException:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_NOT_A_TRAINEE, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TraineeCog(bot))