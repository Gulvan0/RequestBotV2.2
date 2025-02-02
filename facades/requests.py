from dataclasses import dataclass
from datetime import datetime, UTC

from discord import Colour, Embed, Member, Message
from sqlmodel import col, select, Session

from apps_script import Language
from components.views.pending_request_widget import PendingRequestWidgetView
from components.views.resolution_widget import ResolutionWidgetView
from database.db import engine
from database.models import Request, RequestOpinion, RequestReview
from facades.eventlog import add_entry
from services.disc import find_message, post, post_raw_text
from services.gd import get_level
from services.yt import get_video_id_by_url
from util.datatypes import Opinion
from util.format import as_code, as_link, as_user
from util.identifiers import LoggedEventTypeID, RouteID, TextPieceID


@dataclass
class LevelAlreadyApprovedException(Exception):
    """
    Raised when a user tries to request a level which has already been approved
    """
    request_author_mention: str
    requested_at: datetime
    resolved_at: datetime


@dataclass
class PreviousLevelRequestPendingException(Exception):
    """
    Raised when a user tries to request a level which already has an unresolved (pending) request
    """
    request_author_mention: str
    requested_at: datetime


class InvalidYtLinkException(Exception):
    """
    Raised when a user tries to submit a request with an invalid showcase video URL
    """
    pass


def assert_level_requestable(level_id: int) -> None:
    with Session(engine) as session:
        approved_query = select(RequestOpinion).join(Request).where(
            Request.level_id == level_id,  # noqa
            RequestOpinion.is_resolution == True,  # noqa
            RequestOpinion.opinion == Opinion.APPROVED
        )
        approved_request_opinion: RequestOpinion = session.exec(approved_query).first()  # noqa
        if approved_request_opinion:
            raise LevelAlreadyApprovedException(approved_request_opinion.request.request_author_mention, approved_request_opinion.request.requested_at, approved_request_opinion.created_at)

        resolved_request_ids = select(RequestOpinion.request_id).where(RequestOpinion.is_resolution == True)
        pending_query = select(Request).where(Request.level_id == level_id, Request.requested_at != None, ~col(Request.id).in_(resolved_request_ids))  # noqa
        pending_request: Request = session.exec(pending_query).first()  # noqa
        if pending_request:
            raise PreviousLevelRequestPendingException(pending_request.request_author_mention, pending_request.requested_at)


async def get_request_by_id(request_id: int) -> Request | None:
    with Session(engine) as session:
        return session.get(Request, request_id)


async def create_limbo_request(level_id: int, request_language: Language, invoker: Member) -> int:
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
    yt_video_id = get_video_id_by_url(yt_link)
    if not yt_video_id:
        raise InvalidYtLinkException

    with Session(engine) as session:
        request = session.get(Request, request_id)

        level_id = request.level_id
        level = await get_level(level_id)
        assert level

        lang_str = ":flag_gb: English" if request.language == Language.EN else ":flag_ru: Русский"
        copied_id_str = f"{level.copied_level_id} :exclamation:" if level.copied_level_id else "Not a copy"

        embed = Embed(
            color=Colour.from_str("#979b1f"),
            title=f"Request {request_id}",
            description=f"**{level.name}** by _{level.author_name}_"
        )
        embed.set_thumbnail(url=f"https://i.ytimg.com/vi/{yt_video_id}/hqdefault.jpg")
        embed.add_field(name="ID", value=str(level_id), inline=False)
        embed.add_field(name="Review Language", value=lang_str, inline=False)
        embed.add_field(name="Showcase", value=yt_link, inline=False)
        embed.add_field(name="Copied Level ID", value=copied_id_str, inline=False)
        embed.add_field(name="Length", value=level.length.to_str(), inline=True)
        embed.add_field(name="Current Difficulty", value=level.difficulty.to_str(), inline=True)
        embed.add_field(name="Game Version", value=level.game_version, inline=True)
        if additional_comment:
            embed.add_field(name="Comment", value=additional_comment, inline=False)
        embed.add_field(name="Requested by", value=request.request_author_mention, inline=False)

        message = await post_raw_text(RouteID.PENDING_REQUEST, view=PendingRequestWidgetView(request_id), embed=embed)
        if not message:
            return

        request.level_name = level.name
        request.yt_link = yt_link
        request.additional_comment = additional_comment
        request.details_message_id = message.id
        request.details_message_channel_id = message.channel.id
        request.requested_at = datetime.now(UTC)

        session.add(request)
        session.commit()

    await add_entry(LoggedEventTypeID.REQUEST_REQUESTED, invoker, dict(
        request_id=request_id,
        level_id=str(level_id),
        level_name=level.name
    ))


def _render_opinion(reviewer: Member, reasoning: str | None = None) -> str:
    text = as_user(reviewer.id)
    if reasoning:
        text += f" ({reasoning})"
    return text


async def _append_opinion_to_resolution_widget(resolution_widget: Message, reviewer: Member, opinion: Opinion, reasoning: str | None = None) -> None:
    emoji_short_name = "yes" if opinion == Opinion.APPROVED else "no"
    row_prefix = f":{emoji_short_name}~1:: "
    rendered_opinion = _render_opinion(reviewer, reasoning)

    lines = resolution_widget.content.split('\n')
    for i, line in enumerate(lines):
        if not line.startswith(row_prefix):
            continue
        remainder = line.removeprefix(row_prefix).strip()
        if remainder == "No votes yet":
            remainder = rendered_opinion
        else:
            remainder += f", {rendered_opinion}"
        lines[i] = row_prefix + remainder

    await resolution_widget.edit(
        content="\n".join(lines)
    )


async def _create_resolution_widget(
    details_embed: Embed,
    first_reviewer: Member,
    first_opinion: Opinion,
    reasoning: str | None = None
) -> None:
    opinion_str = _render_opinion(first_reviewer, reasoning)
    yes_text = opinion_str if first_opinion == Opinion.APPROVED else "No votes yet"
    no_text = opinion_str if first_opinion == Opinion.REJECTED else "No votes yet"
    consensus = f":yes~1:: {yes_text}\n:no~1:: {no_text}"

    details_embed.colour = Colour.from_str("#128611")
    details_embed.add_field(name="Consensus", value=consensus, inline=False)

    await post_raw_text(
        RouteID.RESOLUTION,
        view=ResolutionWidgetView(),
        embed=details_embed
    )


async def _post_review(reviewer: Member, request: Request, opinion: Opinion, review_text: str) -> Message:
    return await post(
        RouteID.REVIEW_TEXT,
        TextPieceID.REQUEST_REVIEW,
        request.language,
        substitutions=dict(
            request_author=request.request_author_mention,
            reviewer_mention=reviewer.mention,
            level_id=request.level_id,
            level_name=request.level_name,
            review_text=review_text,
            summary=TextPieceID.REQUEST_SUMMARY_GOOD if opinion == Opinion.APPROVED else TextPieceID.REQUEST_SUMMARY_BAD
        )
    )


async def add_opinion(reviewer: Member, request_id: int, review_widget_message: Message, opinion: Opinion, review_text: str | None = None, reason: str | None = None) -> None:
    with Session(engine) as session:
        request: Request = session.get(Request, request_id)  # noqa
        assert request

        # Eagerly reading all the properties so as not to trigger entity refresh later
        resolution_message_id = request.resolution_message_id
        resolution_message_channel_id = request.resolution_message_channel_id
        level_id = request.level_id
        level_name = request.level_name

        associated_review = None
        associated_review_message = None
        if review_text:
            associated_review_message = await _post_review(reviewer, request, opinion, review_text)
            associated_review = RequestReview(
                author_user_id=reviewer.id,
                text=review_text,
                message_id=associated_review_message.id,
                opinion=opinion,
                request=request
            )

        request.opinions.append(RequestOpinion(
            author_user_id=reviewer.id,
            opinion=opinion,
            request_id=request_id,
            associated_review=associated_review
        ))

        session.add(request)
        session.commit()

    formatted_reasoning = None
    if associated_review_message:
        formatted_reasoning = as_link(associated_review_message.jump_url, "Review")
    elif reason:
        formatted_reasoning = as_code(reason)

    if resolution_message_id and resolution_message_channel_id:
        is_first = False
        resolution_widget = await find_message(resolution_message_channel_id, resolution_message_id)
        if resolution_widget:
            await _append_opinion_to_resolution_widget(
                resolution_widget,
                reviewer,
                opinion,
                formatted_reasoning
            )
    else:
        is_first = True
        await _create_resolution_widget(
            review_widget_message.embeds[0],
            reviewer,
            opinion,
            formatted_reasoning
        )

    await add_entry(LoggedEventTypeID.REQUEST_OPINION_ADDED, reviewer, dict(
        request_id=request_id,
        level_id=str(level_id),
        level_name=level_name,
        opinion=opinion.value,
        is_first=str(is_first),
        review_msg_url=associated_review_message.jump_url if associated_review_message else "NO_REVIEW",
        reason=reason or "NO_REASON"
    ))
