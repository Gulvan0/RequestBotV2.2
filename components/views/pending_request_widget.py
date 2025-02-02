from discord import ButtonStyle, Interaction
from discord.ui import Button, DynamicItem, View

from services.disc import respond
from util.datatypes import Opinion
from util.identifiers import TextPieceID

import re
import typing as tp


class PendingRequestWidgetApproveAndReviewBtn(DynamicItem[Button[View]], template=r'prw:aar:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Approve and Review",
                row=0,
                custom_id=f"prw:aar:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        ...  # TODO: Show modal to provide a review, then call add_opinion


class PendingRequestWidgetRejectAndReviewBtn(DynamicItem[Button[View]], template=r'prw:rar:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Reject and Review",
                row=0,
                custom_id=f"prw:rar:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        ...  # TODO: Show a modal to provide a review and an optional reason, then call add_opinion


class PendingRequestWidgetJustApproveBtn(DynamicItem[Button[View]], template=r'prw:ja:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Just Approve",
                row=1,
                custom_id=f"prw:ja:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        import facades.requests
        await facades.requests.add_opinion(interaction.user, self.request_id, interaction.message, Opinion.APPROVED)
        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)


class PendingRequestWidgetJustRejectBtn(DynamicItem[Button[View]], template=r'prw:jr:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Just Reject",
                row=1,
                custom_id=f"prw:jr:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        ...  # TODO: Show a modal to provide an optional reason, then call add_opinion


class PendingRequestWidgetView(View):
    def __init__(self, request_id: int) -> None:
        super().__init__(timeout=None)
        self.add_item(PendingRequestWidgetApproveAndReviewBtn(request_id))
        self.add_item(PendingRequestWidgetRejectAndReviewBtn(request_id))
        self.add_item(PendingRequestWidgetJustApproveBtn(request_id))
        self.add_item(PendingRequestWidgetJustRejectBtn(request_id))