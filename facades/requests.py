from dataclasses import dataclass
from datetime import datetime, UTC
from enum import auto, Enum

from discord import Interaction, Member
from sqlmodel import select, Session

from apps_script import Language
from components.views.pending_request_widget import PendingRequestWidgetView
from database.db import engine
from database.models import Request
from facades.eventlog import add_entry
from services.disc import member_language, post_raw_text
from services.gd import get_level
from util.datatypes import Resolution
from util.identifiers import LoggedEventTypeID, RouteID


@dataclass
class LevelAlreadyApprovedException(Exception):
    request_author_mention: str
    requested_at: datetime
    resolved_at: datetime


@dataclass
class PreviousLevelRequestPendingException(Exception):
    request_author_mention: str
    requested_at: datetime


def assert_level_requestable(level_id: int) -> None:
    with Session(engine) as session:
        approved_query = select(Request).where(Request.level_id == level_id, Request.resolution == Resolution.APPROVED)
        approved_request: Request = session.exec(approved_query).first()  # noqa
        if approved_request:
            raise LevelAlreadyApprovedException(approved_request.request_author_mention, approved_request.requested_at, approved_request.resolved_at)

        pending_query = select(Request).where(Request.level_id == level_id, Request.requested_at != None, Request.resolution == None)  # noqa
        pending_request: Request = session.exec(pending_query).first()  # noqa
        if pending_request:
            raise PreviousLevelRequestPendingException(pending_request.request_author_mention, pending_request.requested_at)


async def get_request_by_id(request_id: int) -> Request | None:
    with Session(engine) as session:
        return session.get(Request, request_id)


async def create_limbo_request(level_id: int, invoking_interaction: Interaction) -> int:
    invoker = invoking_interaction.user
    request_language = member_language(invoker, invoking_interaction.locale).language

    with Session(engine) as session:
        new_entry = Request(
            level_id=level_id,
            language=request_language,
            request_author=invoker.id
        )
        session.add(new_entry)
        session.commit()

        request_id = new_entry.id

    await add_entry(LoggedEventTypeID.REQUEST_INITIALIZED, invoker, dict(
        request_id=request_id,
        level_id=str(level_id),
        lang=request_language.value
    ))

    return request_id


async def complete_request(request_id: int, yt_link: str, additional_comment: str | None, invoker: Member) -> None:
    with Session(engine) as session:
        request = session.get(Request, request_id)

        level = await get_level(request.level_id)
        assert level

        lang_str = ":flag_gb: English" if request.language == Language.EN else ":flag_ru: Русский"
        copied_id_str = f"{level.copied_level_id} :exclamation:" or "Not a copy"
        message_lines = [
            f"**Request {request_id}**",
            "",
            f"`{level.name}` by `{level.author_name}`",
            f"ID: `{request.level_id}`",
            f"YT Link: {yt_link}",
            f"Review Language: {lang_str}",
            f"Length: {level.length.to_str()}",
            f"Current Difficulty: {level.difficulty.to_str()}",
            f"Copied Level ID: {copied_id_str}",
            f"Game Version: {level.game_version}",
            f"Requested by: {request.request_author_mention}",
        ]
        if request.additional_comment:
            message_lines += [
                "",
                request.additional_comment
            ]
        message_text = '\n'.join(message_lines)

        message = await post_raw_text(RouteID.PENDING_REQUEST, message_text, PendingRequestWidgetView())
        if not message:
            return

        request.yt_link = yt_link
        request.additional_comment = additional_comment
        request.details_message_id = message.id
        request.requested_at = datetime.now(UTC)

        session.add(request)
        session.commit()

    await add_entry(LoggedEventTypeID.REQUEST_REQUESTED, invoker, dict(
        request_id=request_id,
        level_id=str(request.level_id)
    ))
