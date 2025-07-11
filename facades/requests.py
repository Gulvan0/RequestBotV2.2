from dataclasses import dataclass
from datetime import datetime, UTC

from discord import Colour, Embed, Member, Message
from sqlalchemy import func
from sqlmodel import col, select

from components.views.pending_request_widget import PendingRequestWidgetView
from components.views.resolution_widget import ResolutionWidgetView
from db import EngineProvider
from db.models import Request, RequestOpinion, RequestReview
from facades.eventlog import add_entry
from facades.parameters import get_value as get_parameter_value, update_value as update_parameter_value
from facades.texts import render_text
from services.disc import find_message, post, post_raw_text, safe_delete_message
from services.gd import get_level
from services.yt import get_video_id_by_url
from util.datatypes import Language, Opinion, SendType
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, as_code_block, as_link, as_user
from util.identifiers import LoggedEventTypeID, ParameterID, RouteID, TextPieceID


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


class NotFoundException(Exception):
    """
    Raised when a user passes an id of a non-existing request
    """
    pass


def assert_level_requestable(level_id: int) -> None:
    with EngineProvider.get_session() as session:
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
    with EngineProvider.get_session() as session:
        return session.get(Request, request_id)


async def get_last_complete_request(level_id: int) -> Request | None:
    with EngineProvider.get_session() as session:
        query = select(Request).where(Request.level_id == level_id, Request.requested_at != None).order_by(col(Request.requested_at).desc())  # noqa
        return session.exec(query).first()  # noqa


async def is_request_unresolved(request_id: int) -> bool:
    with EngineProvider.get_session() as session:
        query = select(RequestOpinion.request_id).where(RequestOpinion.request_id == request_id, RequestOpinion.is_resolution == True)
        return session.exec(query).first() is None


async def get_latest_pending_request(level_id: int) -> Request | None:
    with EngineProvider.get_session() as session:
        resolved_request_ids = select(RequestOpinion.request_id).where(RequestOpinion.is_resolution == True)
        query = select(
            Request
        ).where(
            Request.level_id == level_id,
            Request.requested_at != None,  # noqa
            ~col(Request.id).in_(resolved_request_ids)
        ).order_by(
            col(Request.requested_at).desc()
        )
        return session.exec(query).first()  # noqa


async def get_oldest_ignored_request() -> Request | None:
    with EngineProvider.get_session() as session:
        query = select(Request).where(Request.resolution_message_id == None, Request.requested_at != None).order_by(Request.requested_at)  # noqa
        return session.exec(query).first()  # noqa


async def get_oldest_unresolved_request() -> Request | None:
    with EngineProvider.get_session() as session:
        resolved_request_ids = select(RequestOpinion.request_id).where(RequestOpinion.is_resolution == True)
        query = select(Request).where(
            ~col(Request.id).in_(resolved_request_ids),
            Request.resolution_message_id != None,  # noqa
            Request.resolution_message_channel_id != None  # noqa
        ).order_by(Request.requested_at)
        return session.exec(query).first()  # noqa


async def get_pending_request(oldest: bool) -> Request | None:
    with EngineProvider.get_session() as session:
        resolved_request_ids = select(RequestOpinion.request_id).where(RequestOpinion.is_resolution == True)
        query = select(
            Request
        ).where(
            ~col(Request.id).in_(resolved_request_ids),
            Request.requested_at != None  # noqa
        ).order_by(
            Request.requested_at if oldest else func.random()
        )
        return session.exec(query).first()  # noqa


async def create_limbo_request(level_id: int, request_language: Language, invoker: Member, creator: Member | str | None = None) -> int:
    match creator:
        case Member():
            request_author = str(creator.id)
            is_author_user_id = True
        case str():
            request_author = creator
            is_author_user_id = False
        case _:
            request_author = str(invoker.id)
            is_author_user_id = True

    with EngineProvider.get_session() as session:
        new_entry = Request(
            level_id=level_id,
            language=request_language,
            request_author=request_author,
            is_author_user_id=is_author_user_id
        )
        session.add(new_entry)
        session.commit()

        request_id = new_entry.id

    await add_entry(LoggedEventTypeID.REQUEST_INITIALIZED, invoker, dict(
        request_id=str(request_id),
        level_id=str(level_id),
        lang=request_language.value
    ))

    return request_id


async def complete_request(request_id: int, yt_link: str | None, additional_comment: str | None, invoker: Member, allow_queue_closing: bool = True) -> None:
    if yt_link:
        yt_video_id = get_video_id_by_url(yt_link)
        if not yt_video_id:
            raise InvalidYtLinkException
    else:
        yt_video_id = None

    with EngineProvider.get_session() as session:
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
        if yt_video_id:
            embed.set_thumbnail(url=f"https://i.ytimg.com/vi/{yt_video_id}/hqdefault.jpg")
        embed.add_field(name="ID", value=str(level_id), inline=False)
        embed.add_field(name="Review Language", value=lang_str, inline=False)
        if yt_link:
            embed.add_field(name="Showcase", value=yt_link, inline=False)
        embed.add_field(name="Copied Level ID", value=copied_id_str, inline=False)
        embed.add_field(name="Stars Requested", value=str(level.stars_requested) or "NA", inline=False)
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
        request.yt_link = yt_link or ""
        request.additional_comment = additional_comment
        request.details_message_id = message.id
        request.details_message_channel_id = message.channel.id
        request.requested_at = datetime.now(UTC)

        session.add(request)
        session.commit()

    if allow_queue_closing and get_parameter_value(ParameterID.QUEUE_BLOCK_ENABLED, bool) and get_parameter_value(ParameterID.QUEUE_BLOCK_AT, int) <= await count_pending_requests():
        try:
            await update_parameter_value(ParameterID.QUEUE_BLOCKED, "true")
        except AlreadySatisfiesError:
            pass
        else:
            await post_raw_text(
                RouteID.REQUESTS_CLOSED,
                "<@&1145682760074276984> Requests are temporarily closed / Реквесты временно закрыты"
            )

    await add_entry(LoggedEventTypeID.REQUEST_REQUESTED, invoker, dict(
        request_id=str(request_id),
        level_id=str(level_id),
        level_name=level.name
    ))


def _render_reasoning(associated_review_message: Message | None, reason: str | None) -> str | None:
    if associated_review_message:
        return as_link(associated_review_message.jump_url, "Review")
    elif reason:
        return as_code(reason)
    return None


def _render_opinion(reviewer: Member, reasoning: str | None = None) -> str:
    text = as_user(reviewer.id)
    if reasoning:
        text += f" ({reasoning})"
    return text


async def _append_opinion_to_resolution_widget(resolution_widget: Message, reviewer: Member, opinion: Opinion, reasoning: str | None = None) -> None:
    emoji = "<:yes:1154748625251999744>" if opinion == Opinion.APPROVED else "<:no:1154748651827110010>"
    row_prefix = f"{emoji}: "
    rendered_opinion = _render_opinion(reviewer, reasoning)

    resolution_embed = resolution_widget.embeds[0]
    for field_index, field in enumerate(resolution_embed.fields):
        if field.name == "Consensus":
            lines = field.value.split('\n')
            line_index = 0 if opinion == Opinion.APPROVED else 1
            remainder = lines[line_index].removeprefix(row_prefix).strip()
            if remainder == "No votes yet":
                remainder = rendered_opinion
            else:
                remainder += f", {rendered_opinion}"
            lines[line_index] = row_prefix + remainder

            # Setting field's value doesn't work, so we have to re-add it
            resolution_embed.remove_field(field_index)
            resolution_embed.add_field(name="Consensus", value='\n'.join(lines), inline=False)
            break

    await resolution_widget.edit(
        embed=resolution_embed
    )


async def _append_resolution_to_resolution_widget(resolution_widget: Message, reviewer: Member, opinion: Opinion, reasoning: str | None = None) -> bool:
    emoji = "<:yes:1154748625251999744>" if opinion == Opinion.APPROVED else "<:no:1154748651827110010>"
    rendered_resolution = f"{emoji}:{_render_opinion(reviewer, reasoning)}"

    resolution_embed = resolution_widget.embeds[0]
    resolutions_field_value = None
    is_first = True
    for field_index, field in enumerate(resolution_embed.fields):
        if field.name == "Resolutions":
            is_first = False
            resolutions_field_value = field.value
            resolution_embed.remove_field(field_index)
            break

    if resolutions_field_value:
        rendered_resolution = resolutions_field_value + f", {rendered_resolution}"

    resolution_embed.add_field(
        name="Resolutions",
        value=rendered_resolution,
        inline=False
    )

    resolution_embed.colour = Colour.from_str("#128611")

    await resolution_widget.edit(
        embed=resolution_embed
    )

    return is_first


async def _create_resolution_widget(
    request_id: int,
    details_embed: Embed,
    first_reviewer: Member,
    first_opinion: Opinion,
    reasoning: str | None = None
) -> Message:
    opinion_str = _render_opinion(first_reviewer, reasoning)
    yes_text = opinion_str if first_opinion == Opinion.APPROVED else "No votes yet"
    no_text = opinion_str if first_opinion == Opinion.REJECTED else "No votes yet"
    consensus = f"<:yes:1154748625251999744>: {yes_text}\n<:no:1154748651827110010>: {no_text}"

    details_embed.colour = Colour.from_str("#990000")
    details_embed.add_field(name="Consensus", value=consensus, inline=False)

    return await post_raw_text(
        RouteID.RESOLUTION,
        view=ResolutionWidgetView(request_id),
        embed=details_embed
    )


async def _post_review(reviewer: Member, request: Request, opinion: Opinion, review_text: str, append_summary: bool) -> Message:
    if not append_summary:
        summary = ""
    elif opinion == Opinion.APPROVED:
        summary = TextPieceID.REQUEST_SUMMARY_GOOD
    else:
        summary = TextPieceID.REQUEST_SUMMARY_BAD

    return await post(
        RouteID.REVIEW_TEXT,
        TextPieceID.REQUEST_REVIEW,
        request.language,
        substitutions=dict(
            request_author=request.request_author_mention,
            reviewer_mention=reviewer.mention,
            level_id=request.level_id,
            level_name=as_code(request.level_name),
            review_text=as_code_block(review_text),
            summary=summary
        )
    )


async def get_existing_opinion(reviewer: Member, request_id: int, resolution_only: bool = False) -> RequestOpinion | None:
    with EngineProvider.get_session() as session:
        query = select(RequestOpinion).where(RequestOpinion.request_id == request_id, RequestOpinion.author_user_id == reviewer.id)
        if resolution_only:
            query = query.where(RequestOpinion.is_resolution == True)
        query = query.order_by(col(RequestOpinion.created_at).desc())
        return session.exec(query).first()  # noqa


async def get_existing_review(reviewer: Member, request_id: int) -> RequestReview | None:
    with EngineProvider.get_session() as session:
        query = select(RequestReview).where(RequestReview.request_id == request_id, RequestReview.author_user_id == reviewer.id)
        query = query.order_by(col(RequestReview.created_at).desc())
        return session.exec(query).first()  # noqa


async def count_pending_requests() -> int:
    resolved_request_ids = select(RequestOpinion.request_id).where(RequestOpinion.is_resolution == True)
    query = select(func.count(Request.id)).where(
        Request.requested_at != None,    # noqa
        ~col(Request.id).in_(resolved_request_ids)
    )
    with EngineProvider.get_session() as session:
        return session.exec(query).one() or 0  # noqa


async def add_opinion(reviewer: Member, request_id: int, opinion: Opinion, review_widget_message: Message | None = None, review_text: str | None = None, reason: str | None = None) -> None:
    with EngineProvider.get_session() as session:
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
            append_summary = get_parameter_value(ParameterID.REQUEST_APPEND_CONCLUSION_TO_REVIEW, bool)
            associated_review_message = await _post_review(reviewer, request, opinion, review_text, append_summary)
            associated_review = RequestReview(
                author_user_id=reviewer.id,
                text=review_text,
                message_id=associated_review_message.id,
                message_channel_id=associated_review_message.channel.id,
                opinion=opinion,
                request=request
            )
            session.add(associated_review)

        request.opinions.append(RequestOpinion(
            author_user_id=reviewer.id,
            opinion=opinion,
            request_id=request_id,
            associated_review=associated_review
        ))

        formatted_reasoning = _render_reasoning(associated_review_message, reason)

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
            if not review_widget_message:
                review_widget_message = await find_message(request.details_message_channel_id, request.details_message_id)
            assert review_widget_message, "Trying to add an opinion to a message with a deleted reviewers' widget (how on Earth did you trigger this hook then?)"
            resolution_message = await _create_resolution_widget(
                request_id,
                review_widget_message.embeds[0],
                reviewer,
                opinion,
                formatted_reasoning
            )
            request.resolution_message_id = resolution_message.id
            request.resolution_message_channel_id = resolution_message.channel.id

        session.add(request)
        session.commit()

    await add_entry(LoggedEventTypeID.REQUEST_OPINION_ADDED, reviewer, dict(
        request_id=str(request_id),
        level_id=str(level_id),
        level_name=level_name,
        opinion=opinion.value,
        is_first=str(is_first),
        review_msg_url=associated_review_message.jump_url if associated_review_message else "NO_REVIEW",
        reason=reason or "NO_REASON"
    ))


async def resolve(resolving_mod: Member, request_id: int, sent_for: SendType | None, review_text: str | None = None, reason: str | None = None) -> bool:
    opinion = Opinion.APPROVED if sent_for else Opinion.REJECTED

    with EngineProvider.get_session() as session:
        request: Request = session.get(Request, request_id)  # noqa
        if not request:
            return False

        # Eagerly reading all the properties so as not to trigger entity refresh later
        level_id = request.level_id
        level_name = request.level_name

        associated_review = None
        associated_review_message = None
        if review_text:
            append_summary = get_parameter_value(ParameterID.REQUEST_APPEND_CONCLUSION_TO_FINAL_REVIEW, bool)
            associated_review_message = await _post_review(resolving_mod, request, opinion, review_text, append_summary)
            associated_review = RequestReview(
                author_user_id=resolving_mod.id,
                text=review_text,
                message_id=associated_review_message.id,
                message_channel_id=associated_review_message.channel.id,
                opinion=opinion,
                request=request
            )
            session.add(associated_review)

        request.opinions.append(RequestOpinion(
            author_user_id=resolving_mod.id,
            opinion=opinion,
            is_resolution=True,
            request_id=request_id,
            associated_review=associated_review
        ))

        formatted_reasoning = _render_reasoning(associated_review_message, reason)
        resolution_widget = await find_message(request.resolution_message_channel_id, request.resolution_message_id)

        review_widget = await find_message(request.details_message_channel_id, request.details_message_id)
        assert review_widget
        review_widget_embed = review_widget.embeds[0]

        if not resolution_widget:
            resolution_widget = await _create_resolution_widget(
                request_id=request_id,
                details_embed=review_widget_embed,
                first_reviewer=resolving_mod,
                first_opinion=opinion,
                reasoning=formatted_reasoning
            )
        assert resolution_widget

        is_first = await _append_resolution_to_resolution_widget(resolution_widget, resolving_mod, opinion, formatted_reasoning)

        if is_first:
            embed = review_widget_embed.copy()
            embed.colour = Colour.from_str("#666666")
            embed.add_field(name="Opinions and Resolutions", value=f"See {as_link(resolution_widget.jump_url, 'widget')}")
            archive_message = await post_raw_text(RouteID.ARCHIVE, embed=embed)

            request.details_message_id = archive_message.id
            request.details_message_channel_id = archive_message.channel.id

            await review_widget.delete()

        session.add(request)
        session.commit()

        if opinion == Opinion.APPROVED:
            grade_text_pieces = {
                SendType.STARRATE: TextPieceID.REQUEST_GRADE_STARRATE,
                SendType.FEATURE: TextPieceID.REQUEST_GRADE_FEATURED,
                SendType.EPIC: TextPieceID.REQUEST_GRADE_EPIC,
                SendType.MYTHIC: TextPieceID.REQUEST_GRADE_MYTHIC,
                SendType.LEGENDARY: TextPieceID.REQUEST_GRADE_LEGENDARY,
            }

            review_message_text = render_text(
                TextPieceID.REQUEST_APPROVED,
                request.language,
                substitutions=dict(
                    request_author=request.request_author_mention,
                    responsible_mod_mention=resolving_mod.mention,
                    level_id=request.level_id,
                    level_name=as_code(request.level_name),
                    grade=grade_text_pieces[sent_for]
                )
            )
            if reason:
                review_message_text += "\n" + render_text(
                    TextPieceID.REQUEST_APPROVAL_COMMENT_ADDENDUM,
                    request.language,
                    substitutions=dict(
                        comment=as_code(reason)
                    )
                )

            await post_raw_text(RouteID.APPROVAL_NOTIFICATION, review_message_text)
        else:
            await post(
                RouteID.REJECTION_NOTIFICATION,
                TextPieceID.REQUEST_REJECTED,
                request.language,
                substitutions=dict(
                    request_author=request.request_author_mention,
                    responsible_mod_mention=resolving_mod.mention,
                    level_id=request.level_id,
                    level_name=as_code(request.level_name),
                    reason=as_code(reason) or TextPieceID.COMMON_NOT_SPECIFIED
                )
            )

    if is_first and get_parameter_value(ParameterID.QUEUE_UNBLOCK_ENABLED, bool) and get_parameter_value(ParameterID.QUEUE_UNBLOCK_AT, int) >= await count_pending_requests():
        try:
            await update_parameter_value(ParameterID.QUEUE_BLOCKED, "false")
        except AlreadySatisfiesError:
            pass
        else:
            await post_raw_text(
                RouteID.REQUESTS_REOPENED,
                "<@&1145682760074276984> Requests are open again / Реквесты снова открыты"
            )

    await add_entry(LoggedEventTypeID.REQUEST_RESOLUTION_ADDED, resolving_mod, dict(
        request_id=str(request_id),
        level_id=str(level_id),
        level_name=level_name,
        opinion=opinion.value,
        is_first=str(is_first),
        review_msg_url=associated_review_message.jump_url if associated_review_message else "NO_REVIEW",
        reason=reason or "NO_REASON"
    ))

    return True


async def delete_request(request_id: int, invoker: Member) -> None:
    with EngineProvider.get_session() as session:
        request: Request = session.get(Request, request_id)  # noqa
        if not request:
            raise NotFoundException

        await safe_delete_message(request.resolution_message_channel_id, request.resolution_message_id)
        await safe_delete_message(request.details_message_channel_id, request.details_message_id)

        session.delete(request)
        session.commit()

    await add_entry(LoggedEventTypeID.REQUEST_DELETED, invoker, dict(
        request_id=str(request_id)
    ))