import re

from discord import ButtonStyle, Interaction
from discord.ui import Button, DynamicItem, View

import typing as tp

from components.modals.pre_approval import PreApprovalModal
from components.modals.pre_rejection import PreRejectionModal
from services.disc import member_language, respond
from util.format import as_timestamp
from util.identifiers import TextPieceID


async def pass_common_checks(interaction: Interaction, request_id: int) -> bool:
    import facades.requests
    previous_review = await facades.requests.get_existing_review(interaction.user, request_id)
    if previous_review:
        await respond(
            interaction,
            TextPieceID.REQUEST_PENDING_WIDGET_REVIEW_ALREADY_EXISTS,
            substitutions=dict(
                prev_review_ts=as_timestamp(previous_review.created_at)
            ),
            ephemeral=True
        )
        return False

    return True


class TraineePickWidgetAcceptBtn(DynamicItem[Button[View]], template=r'tpw:a:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Write positive review",
                emoji="<:review_accept:1338212931237707818>",
                custom_id=f"tpw:a:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction, self.request_id):
            await interaction.response.send_modal(PreApprovalModal(self.request_id, member_language(interaction.user, interaction.locale).language))


class TraineePickWidgetRejectBtn(DynamicItem[Button[View]], template=r'tpw:r:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Write negative review",
                emoji="<:review_reject:1338212929841135626>",
                custom_id=f"tpw:r:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction, self.request_id):
            await interaction.response.send_modal(PreRejectionModal(self.request_id, member_language(interaction.user, interaction.locale).language))


class TraineePickWidgetView(View):
    def __init__(self, request_id: int) -> None:
        super().__init__(timeout=None)
        self.add_item(TraineePickWidgetAcceptBtn(request_id))
        self.add_item(TraineePickWidgetRejectBtn(request_id))