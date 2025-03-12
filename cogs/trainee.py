from discord import app_commands, Interaction, Member
from discord.ext import commands

from components.views.trainee_pick_widget import TraineePickWidgetView
from facades.trainee import expel_trainee, NotATraineeException, pick_random_request, promote_trainee, RoleNotAssociatedException
from services.disc import CheckDeferringBehaviour, requires_permission, respond
from util.format import as_code
from util.identifiers import PermissionFlagID, TextPieceID


class TraineeCog(commands.GroupCog, name="trainee", description="Commands for working with the trainee system"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TRAINEE_PROMOTE.as_locale_str())
    @app_commands.describe(trainee=TextPieceID.COMMAND_OPTION_TRAINEE_PROMOTE_TRAINEE.as_locale_str())
    @requires_permission(PermissionFlagID.TRAINEE_SUPERVISOR, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def promote(self, inter: Interaction, trainee: Member) -> None:
        try:
            await promote_trainee(trainee, inter.user)
        except RoleNotAssociatedException as e:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_ROLE_NOT_ASSOCIATED, substitutions=dict(permission=as_code(e.permission.value)), ephemeral=True)
        except NotATraineeException:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_NOT_A_TRAINEE, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TRAINEE_EXPEL.as_locale_str())
    @app_commands.describe(trainee=TextPieceID.COMMAND_OPTION_TRAINEE_EXPEL_TRAINEE.as_locale_str())
    @requires_permission(PermissionFlagID.TRAINEE_SUPERVISOR, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def expel(self, inter: Interaction, trainee: Member) -> None:
        try:
            await expel_trainee(trainee, inter.user)
        except RoleNotAssociatedException as e:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_ROLE_NOT_ASSOCIATED, substitutions=dict(permission=as_code(e.permission.value)), ephemeral=True)
        except NotATraineeException:
            await respond(inter, TextPieceID.TRAINEE_PROMOTION_NOT_A_TRAINEE, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TRAINEE_PICK.as_locale_str())
    @requires_permission(PermissionFlagID.TRAINEE, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def pick(self, inter: Interaction) -> None:
        picked_data = await pick_random_request(inter.user)

        if picked_data:
            await inter.edit_original_response(content="", embed=picked_data.embed, view=TraineePickWidgetView(picked_data.request_id))
        else:
            await respond(inter, TextPieceID.TRAINEE_PICK_NO_REQUESTS, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TraineeCog(bot))