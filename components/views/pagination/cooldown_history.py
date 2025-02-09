import json
import re

from win32ctypes.pywin32.pywintypes import datetime

from components.views.pagination.generic import GenericPaginationView
from facades.eventlog import get_entries, LoadedLogFilter
from facades.requests import get_request_by_id
from services.disc import find_message
from util.datatypes import CooldownEntity
from util.format import as_code, as_link, as_timestamp, as_user, TimestampStyle
from util.identifiers import LoggedEventTypeID


class CooldownHistoryPaginationView(GenericPaginationView):
    def __init__(self, entity: CooldownEntity, entity_id: int) -> None:
        super().__init__()
        self.limit = 6

        self.entity = entity
        self.entity_id = entity_id

    async def get_current_page_blocks(self) -> list[str]:
        event_type = LoggedEventTypeID.USER_COOLDOWN_UPDATED if self.entity == CooldownEntity.USER else LoggedEventTypeID.LEVEL_COOLDOWN_UPDATED
        entity_id_key = "target_user_id" if self.entity == CooldownEntity.USER else "target_level_id"

        entries = get_entries(self.limit, self.offset, LoadedLogFilter(
            event_type=event_type,
            custom_data_values={
                entity_id_key: self.entity_id
            }
        ))

        blocks = []

        for event in entries:
            custom_data_dict = json.loads(event.custom_data)
            cast_timestamp = as_timestamp(event.timestamp)
            reason = custom_data_dict.get("reason", "no reason")

            cooldowns = {}
            for cooldown_field in ("old", "new"):
                raw = custom_data_dict.get(cooldown_field)
                matched = re.search(r'until (.*)$', raw)
                cooldowns[cooldown_field] = as_timestamp(datetime.fromisoformat(matched.group(1)), TimestampStyle.LONG_DATETIME) if matched else as_code(raw)

            if event.user_id:
                caster_ref = as_user(event.user_id)
                if reason != "no reason":
                    caster_ref += f" ({reason})"
            else:
                request_id_matches = re.findall(r'\(request ID: (\d+)\)$', reason)
                if request_id_matches:
                    request_id = int(request_id_matches[0])
                    request = await get_request_by_id(request_id)
                    details_message = await find_message(request.details_message_channel_id, request.details_message_id)
                    caster_ref = as_link(details_message.jump_url, f"**Request {request_id}**")
                else:
                    caster_ref = "SYSTEM"

            blocks.append(f"{cast_timestamp} by {caster_ref}\n{cooldowns['old']} -> {cooldowns['new']}\n")

        return blocks