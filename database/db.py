import asyncio
from pathlib import Path

from sqlmodel import SQLModel, create_engine


SQLITE_FILE_NAME = "data/database.db"


sqlite_url = f"sqlite:///{SQLITE_FILE_NAME}"
engine = create_engine(sqlite_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


async def replace_file(new_file_path: Path):
    global engine

    engine.dispose()
    engine = None

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
                engine = create_engine(sqlite_url)
                raise
        else:
            break

    new_file_path.rename(SQLITE_FILE_NAME)
    discarded_db_path.unlink()

    engine = create_engine(sqlite_url)
