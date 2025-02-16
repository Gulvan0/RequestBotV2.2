import re

from discord import ButtonStyle, Interaction
from discord.ui import Button, DynamicItem, View

import typing as tp

from components.modals.trainee_review_feedback import TraineeReviewFeedbackModal
from facades.permissions import has_permission
from services.disc import member_language, respond_forbidden
from util.identifiers import PermissionFlagID


async def pass_common_checks(interaction: Interaction) -> bool:
    if not has_permission(interaction.user, PermissionFlagID.TRAINEE_SUPERVISOR):
        await respond_forbidden(interaction)
        return False
    return True


class TraineeReviewWidgetAcceptBtn(DynamicItem[Button[View]], template=r'trw:a:(?P<review_id>\d+)'):
    def __init__(self, review_id: int):
        self.review_id = review_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Approve",
                emoji="<:yes:1154748625251999744>",
                custom_id=f"trw:a:{review_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("review_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction):
            await interaction.response.send_modal(TraineeReviewFeedbackModal(
                review_id=self.review_id,
                accept=True,
                language=member_language(interaction.user, interaction.locale).language
            ))


class TraineeReviewWidgetRejectBtn(DynamicItem[Button[View]], template=r'trw:r:(?P<review_id>\d+)'):
    def __init__(self, review_id: int):
        self.review_id = review_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Reject",
                emoji="<:no:1154748651827110010>",
                custom_id=f"trw:r:{review_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("review_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction):
            await interaction.response.send_modal(TraineeReviewFeedbackModal(
                review_id=self.review_id,
                accept=False,
                language=member_language(interaction.user, interaction.locale).language
            ))


class TraineeReviewWidgetView(View):
    def __init__(self, request_id: int) -> None:
        super().__init__(timeout=None)
        self.add_item(TraineeReviewWidgetAcceptBtn(request_id))
        self.add_item(TraineeReviewWidgetRejectBtn(request_id))