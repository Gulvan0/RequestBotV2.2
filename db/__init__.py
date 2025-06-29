import asyncio
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import ClassVar
from db.models import *
from sqlmodel import SQLModel, create_engine, Session, text
from sqlalchemy import Engine
from config.stage_parameters import get_value as get_stage_parameter_value
from globalconf import CONFIG
from util.format import as_timestamp
from util.identifiers import StageParameterID

SQLITE_FILE_NAME = "data/database.db"
SQLITE_URL = f"sqlite:///{SQLITE_FILE_NAME}"


class TooEarlyException(Exception):
    pass


class InitializingDatabaseSnapshotNotFoundError(Exception):
    pass


@dataclass
class EngineProvider:
    engine: ClassVar[Engine | None] = None

    @classmethod
    def get_session(cls) -> Session:
        if cls.engine:
            return Session(cls.engine)
        raise TooEarlyException

    @classmethod
    async def create(cls) -> None:
        cls.engine = create_engine(SQLITE_URL)
        SQLModel.metadata.create_all(cls.engine)
        await CONFIG.bot.sync_tree()

    @classmethod
    async def load(cls) -> None:
        channel = CONFIG.bot.get_channel(get_stage_parameter_value(StageParameterID.SNAPSHOT_CHANNEL_ID))
        assert channel
        async for message in channel.history():
            for attachment in message.attachments:
                if ".db" in attachment.filename:
                    await attachment.save(SQLITE_FILE_NAME)
                    await cls.create()
                    if datetime.now(UTC) - message.created_at > timedelta(minutes=10):
                        await channel.send(f"Warning: the snapshot loaded at startup was originally uploaded at {as_timestamp(message.created_at)}. If there were some updates after that, they have been lost")
                    return
        raise InitializingDatabaseSnapshotNotFoundError

    @classmethod
    async def replace_file(cls, new_file_path: Path):
        cls.engine.dispose()
        cls.engine = None

        discarded_db_path = Path('data/old.db')
        retries = 15
        for i in range(retries):
            try:
                Path(SQLITE_FILE_NAME).rename(discarded_db_path)
            except PermissionError:
                if i < retries - 1:
                    await asyncio.sleep(1 + 0.5 * retries)
                else:
                    new_file_path.unlink()
                    cls.engine = create_engine(SQLITE_URL)
                    raise
            else:
                break

        new_file_path.rename(SQLITE_FILE_NAME)
        discarded_db_path.unlink()

        await cls.create()
