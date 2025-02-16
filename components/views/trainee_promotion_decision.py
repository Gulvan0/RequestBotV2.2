import re

from discord import ButtonStyle, Interaction
from discord.ui import Button, DynamicItem, View

import typing as tp

from facades.permissions import has_permission
from facades.texts import render_text
from services.disc import respond, respond_forbidden
from util.datatypes import Language
from util.format import as_code
from util.identifiers import PermissionFlagID, TextPieceID


async def pass_common_checks(interaction: Interaction) -> bool:
    if not has_permission(interaction.user, PermissionFlagID.TRAINEE_SUPERVISOR):
        await respond_forbidden(interaction)
        return False
    return True


class TraineePromotionDecisionPromoteBtn(DynamicItem[Button[View]], template=r'tpd:p:(?P<trainee_user_id>\d+)'):
    def __init__(self, trainee_user_id: int, language: Language = Language.EN):
        self.trainee_user_id = trainee_user_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label=render_text(TextPieceID.TRAINEE_REVIEW_RESOLUTION_RESPONSE_PROMOTE_BTN_LABEL, language),
                custom_id=f"tpd:p:{trainee_user_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("trainee_user_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction):
            import facades.trainee
            try:
                await facades.trainee.promote_trainee(self.trainee_user_id, interaction.user)
            except facades.trainee.RoleNotAssociatedException as e:
                await respond(interaction, TextPieceID.TRAINEE_PROMOTION_ROLE_NOT_ASSOCIATED, substitutions=dict(permission=as_code(e.permission.value)), ephemeral=True)
            except facades.trainee.NotATraineeException:
                await respond(interaction, TextPieceID.TRAINEE_PROMOTION_NOT_A_TRAINEE, ephemeral=True)
            else:
                await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)


class TraineePromotionDecisionExpelBtn(DynamicItem[Button[View]], template=r'tpd:e:(?P<trainee_user_id>\d+)'):
    def __init__(self, trainee_user_id: int, language: Language = Language.EN):
        self.trainee_user_id = trainee_user_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label=render_text(TextPieceID.TRAINEE_REVIEW_RESOLUTION_RESPONSE_EXPEL_BTN_LABEL, language),
                custom_id=f"tpd:e:{trainee_user_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("trainee_user_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction):
            import facades.trainee
            try:
                await facades.trainee.expel_trainee(self.trainee_user_id, interaction.user)
            except facades.trainee.RoleNotAssociatedException as e:
                await respond(interaction, TextPieceID.TRAINEE_PROMOTION_ROLE_NOT_ASSOCIATED, substitutions=dict(permission=as_code(e.permission.value)), ephemeral=True)
            except facades.trainee.NotATraineeException:
                await respond(interaction, TextPieceID.TRAINEE_PROMOTION_NOT_A_TRAINEE, ephemeral=True)
            else:
                await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)


class TraineePromotionDecisionWaitBtn(DynamicItem[Button[View]], template='tpd:w'):
    def __init__(self, language: Language = Language.EN):
        super().__init__(
            Button(
                style=ButtonStyle.gray,
                label=render_text(TextPieceID.TRAINEE_REVIEW_RESOLUTION_RESPONSE_WAIT_BTN_LABEL, language),
                custom_id=f"tpd:w"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, ___) -> tp.Self:
        return cls()

    async def callback(self, interaction: Interaction) -> None:
        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)


class TraineePromotionDecisionView(View):
    def __init__(self, trainee_user_id: int, language: Language) -> None:
        super().__init__(timeout=None)
        self.add_item(TraineePromotionDecisionPromoteBtn(trainee_user_id, language))
        self.add_item(TraineePromotionDecisionExpelBtn(trainee_user_id, language))
        self.add_item(TraineePromotionDecisionWaitBtn(language))