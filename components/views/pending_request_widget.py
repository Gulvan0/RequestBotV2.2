from discord import ButtonStyle, Interaction
from discord.ui import Button, DynamicItem, View

from components.modals.pre_approval import PreApprovalModal
from components.modals.pre_rejection import PreRejectionModal
from components.modals.pre_rejection_no_review import PreRejectionNoReviewModal
from facades.permissions import has_permission
from services.disc import member_language, respond, respond_forbidden
from util.datatypes import Opinion
from util.format import as_timestamp
from util.identifiers import PermissionFlagID, TextPieceID

import re
import typing as tp


async def pass_common_checks(interaction: Interaction, request_id: int) -> bool:
    if not has_permission(interaction.user, PermissionFlagID.REVIEWER):
        await respond_forbidden(interaction)
        return False
    
    import facades.requests
    previous_opinion = await facades.requests.get_existing_opinion(interaction.user, request_id)
    if previous_opinion:
        await respond(
            interaction,
            TextPieceID.REQUEST_PENDING_WIDGET_OPINION_ALREADY_EXISTS,
            substitutions=dict(
                prev_opinion_ts=as_timestamp(previous_opinion.created_at)
            ),
            ephemeral=True
        )
        return False

    return True


class PendingRequestWidgetApproveAndReviewBtn(DynamicItem[Button[View]], template=r'prw:aar:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Approve and Review",
                emoji="<:review_accept:1338212931237707818>",
                row=0,
                custom_id=f"prw:aar:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction, self.request_id):
            await interaction.response.send_modal(PreApprovalModal(self.request_id, member_language(interaction.user, interaction.locale).language))


class PendingRequestWidgetJustApproveBtn(DynamicItem[Button[View]], template=r'prw:ja:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Just Approve",
                emoji="<:yes:1154748625251999744>",
                row=0,
                custom_id=f"prw:ja:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        if await pass_common_checks(interaction, self.request_id):
            import facades.requests
            await facades.requests.add_opinion(interaction.user, self.request_id, Opinion.APPROVED, interaction.message)
            await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)


class PendingRequestWidgetRejectAndReviewBtn(DynamicItem[Button[View]], template=r'prw:rar:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Reject and Review",
                emoji="<:review_reject:1338212929841135626>",
                row=1,
                custom_id=f"prw:rar:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction, self.request_id):
            await interaction.response.send_modal(PreRejectionModal(self.request_id, member_language(interaction.user, interaction.locale).language))


class PendingRequestWidgetJustRejectBtn(DynamicItem[Button[View]], template=r'prw:jr:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Just Reject",
                emoji="<:no:1154748651827110010>",
                row=1,
                custom_id=f"prw:jr:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        if await pass_common_checks(interaction, self.request_id):
            await interaction.response.send_modal(PreRejectionNoReviewModal(self.request_id, member_language(interaction.user, interaction.locale).language))


class PendingRequestWidgetView(View):
    def __init__(self, request_id: int) -> None:
        super().__init__(timeout=None)
        self.add_item(PendingRequestWidgetApproveAndReviewBtn(request_id))
        self.add_item(PendingRequestWidgetJustApproveBtn(request_id))
        self.add_item(PendingRequestWidgetRejectAndReviewBtn(request_id))
        self.add_item(PendingRequestWidgetJustRejectBtn(request_id))