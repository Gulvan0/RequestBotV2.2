import re
import typing as tp

from discord import ButtonStyle, Interaction
from discord.ui import DynamicItem, View, Button

from components.modals.approval import ApprovalModal
from components.modals.rejection import RejectionModal
from services.disc import member_language
from util.datatypes import SendType


class ResolutionWidgetStarrateBtn(DynamicItem[Button[View]], template=r'rw:sr:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Star Rate",
                row=0,
                custom_id=f"rw:sr:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(ApprovalModal(self.request_id, SendType.STARRATE, member_language(interaction.user, interaction.locale).language))


class ResolutionWidgetFeatureBtn(DynamicItem[Button[View]], template=r'rw:f:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Feature",
                row=0,
                custom_id=f"rw:f:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(ApprovalModal(self.request_id, SendType.FEATURE, member_language(interaction.user, interaction.locale).language))


class ResolutionWidgetEpicBtn(DynamicItem[Button[View]], template=r'rw:e:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Epic",
                row=0,
                custom_id=f"rw:e:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(ApprovalModal(self.request_id, SendType.EPIC, member_language(interaction.user, interaction.locale).language))


class ResolutionWidgetMythicBtn(DynamicItem[Button[View]], template=r'rw:m:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Mythic",
                row=0,
                custom_id=f"rw:m:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(ApprovalModal(self.request_id, SendType.MYTHIC, member_language(interaction.user, interaction.locale).language))


class ResolutionWidgetLegendaryBtn(DynamicItem[Button[View]], template=r'rw:l:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.green,
                label="Legendary",
                row=0,
                custom_id=f"rw:l:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(ApprovalModal(self.request_id, SendType.LEGENDARY, member_language(interaction.user, interaction.locale).language))


class ResolutionWidgetRejectBtn(DynamicItem[Button[View]], template=r'rw:r:(?P<req_id>\d+)'):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(
            Button(
                style=ButtonStyle.red,
                label="Reject",
                row=1,
                custom_id=f"rw:r:{request_id}"
            )
        )

    @classmethod
    async def from_custom_id(cls, _, __, match: re.Match[str]) -> tp.Self:
        return cls(int(match.group("req_id")))

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(RejectionModal(self.request_id, member_language(interaction.user, interaction.locale).language))


class ResolutionWidgetView(View):
    def __init__(self, request_id: int) -> None:
        super().__init__(timeout=None)
        self.add_item(ResolutionWidgetStarrateBtn(request_id))
        self.add_item(ResolutionWidgetFeatureBtn(request_id))
        self.add_item(ResolutionWidgetEpicBtn(request_id))
        self.add_item(ResolutionWidgetMythicBtn(request_id))
        self.add_item(ResolutionWidgetLegendaryBtn(request_id))
        self.add_item(ResolutionWidgetRejectBtn(request_id))