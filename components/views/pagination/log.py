from __future__ import annotations

from datetime import datetime
from components.views.pagination.generic import GenericPaginationView
from database.models import StoredLogFilter
from facades.eventlog import get_current_filter, get_entries, get_offset_at_datetime, LoadedLogFilter
from util.format import as_code_block, logs_member_ref

import json
import yaml


class LogPaginationView(GenericPaginationView):
    def __init__(self, start_datetime: datetime | None = None, log_filter: StoredLogFilter | LoadedLogFilter | None = None) -> None:
        super().__init__()

        self.may_require_step_back: bool = start_datetime is not None
        self.log_filter: StoredLogFilter | LoadedLogFilter | None = log_filter

        self.limit = 4

        if start_datetime:
            self.offset = get_offset_at_datetime(start_datetime, self.log_filter)

    async def get_current_page_blocks(self) -> list[str]:
        if not self.log_filter:
            self.log_filter = get_current_filter(self.user)

        entries = get_entries(self.limit, self.offset, self.log_filter)

        # Processing the case when the datetime exceeds the timestamp of the last matching event
        if self.may_require_step_back and not entries and self.offset > 0:
            self.offset = max(self.offset - self.limit, 0)
            entries = get_entries(self.limit, self.offset, self.log_filter)

        self.may_require_step_back = False

        lines = []
        for event in entries:
            user = await self.interaction.client.fetch_user(event.user_id) if event.user_id else None
            event_info = dict(
                id=event.id,
                event=event.event_type.name,
                user=logs_member_ref(user),
                timestamp=event.timestamp.isoformat()
            )
            event_info.update(json.loads(event.custom_data))
            line = as_code_block(yaml.safe_dump(event_info, sort_keys=False), "yaml")
            lines.append(line)

        return lines