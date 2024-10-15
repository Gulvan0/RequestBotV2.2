import json

import discord

from database.models import LoggedEvent
from util.identifiers import LoggedEventTypeID
from sqlmodel import Session

from database.db import engine


def add_entry(event_type: LoggedEventTypeID, user: discord.Member | None = None, custom_data: dict[str, str] | None = None) -> None:
    user_str = user.name if user else 'SYSTEM'
    message = f'{event_type.name} by {user_str}'
    if custom_data:
        pairs = ', '.join([f'{key}={value}' for key, value in custom_data.items()])
        message += f' ({pairs})'
    print(message)

    custom_data_str = json.dumps(custom_data) if custom_data else "{}"
    with Session(engine) as session:
        new_entry = LoggedEvent(event_type=event_type, user_id=user.id if user else None, custom_data=custom_data_str)
        session.add(new_entry)
        session.commit()