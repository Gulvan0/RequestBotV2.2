from collections import defaultdict
from datetime import datetime, timedelta

from discord import Member
from plotly.graph_objs import Figure
from sqlalchemy import func
from sqlmodel import col, distinct, select, Session

from facades.parameters import get_value as get_parameter_value
from database.db import engine

import pandas as pd
import plotly.express as px
import typing as tp

from database.models import LoggedEvent, Request, RequestOpinion, RequestReview
from services.disc import find_member
from util.datatypes import Opinion, ReportRange, SimpleReportRange
from util.identifiers import LoggedEventTypeID, ParameterID
from util.time import to_start_of_day


def __save_figure(fig: Figure) -> str:
    filename = str(round(datetime.now().timestamp() * 1000000)) + ".png"
    fig.write_image(filename)
    return filename


async def new_requests(report_range: ReportRange) -> str:
    query = select(Request.requested_at).where(Request.requested_at != None)  # noqa
    report_range.restrict_query(query, Request.requested_at)

    data_with_gaps = defaultdict(int)
    range_start = report_range.get_first_bin_value()
    range_end = report_range.get_last_bin_value()
    with Session(engine) as session:
        for requested_at in session.exec(query):  # noqa
            current_bin = report_range.get_bin(requested_at).value
            if not range_start or current_bin < range_start:
                range_start = current_bin
            if not range_end or current_bin > range_end:
                range_end = current_bin
            data_with_gaps[current_bin] += 1

    result = {}
    full_range = pd.date_range(
        start=range_start,
        end=range_end,
        freq=timedelta(weeks=1) if report_range.weekly_granularity else timedelta(days=1)
    )
    for ts in full_range.to_list():
        current_bin = report_range.get_bin(ts)
        result[current_bin.name] = data_with_gaps[current_bin.value]

    column_names = [report_range.get_x_axis_name(), 'New Requests']
    df = pd.DataFrame(result.items(), columns=column_names)
    fig = px.line(
        df,
        x=column_names[0],
        y=column_names[1],
        title="Levels Requested",
        subtitle=report_range.get_plot_subtitle()
    )

    if not report_range.weekly_granularity:
        block_updates: tp.Iterable[LoggedEvent] = session.exec(
            report_range.restrict_query(
                select(  # noqa
                    LoggedEvent
                ).where(
                    LoggedEvent.event_type == LoggedEventTypeID.PARAMETER_EDITED,
                    col(LoggedEvent.custom_data).contains('"parameter_id": "queue.blocked"')
                ),
                LoggedEvent.timestamp
            ).order_by(
                LoggedEvent.timestamp
            )
        )

        blocked_at = None
        initialized = False
        for block_update in block_updates:
            update_ts = block_update.timestamp
            blocked = '"value": "true"' in block_update.custom_data
            if blocked:
                if not blocked_at:
                    blocked_at = update_ts
            else:
                if not initialized:
                    blocked_at = to_start_of_day(range_start)
                if blocked_at and blocked_at.date() + timedelta(days=1) < update_ts.date():  # i.e. there is at least one full day during which the queue was blocked
                    fig.add_vrect(
                        # The reason for those hour manipulations is due to how our diagram looks like. It's not exactly the timeseries. It bears some similarities with a histogram
                        x0=blocked_at.replace(hour=12, minute=0, second=0, microsecond=0),  # noqa
                        x1=to_start_of_day(update_ts) - timedelta(hours=12),  # noqa
                        fillcolor="red",
                        opacity=0.25,
                        line_width=0
                    )
                blocked_at = None
            initialized = True
        if blocked_at and blocked_at.date() < range_end:
            fig.add_vrect(
                x0=blocked_at.replace(hour=12, minute=0, second=0, microsecond=0),  # noqa
                x1=to_start_of_day(range_end),  # noqa
                fillcolor="red",
                opacity=0.25,
                line_width=0
            )

    return __save_figure(fig)


async def pending_requests(report_range: ReportRange) -> str:
    if report_range.date_from:
        with Session(engine) as session:
            created_before_range_start: int = session.exec(
                select(  # noqa
                    func.count(Request.id)
                ).where(
                    Request.requested_at != None,  # noqa
                    Request.requested_at < report_range.get_inclusive_min_datetime()
                )
            ).one()
            resolved_before_range_start: int = session.exec(
                select(  # noqa
                    func.count(distinct(RequestOpinion.request_id))
                ).where(
                    RequestOpinion.is_resolution == True,  # noqa
                    RequestOpinion.created_at < report_range.get_inclusive_min_datetime()
                )
            ).one()
        a_priori_pending_requests = created_before_range_start - resolved_before_range_start
    else:
        a_priori_pending_requests = 0

    creates_query = report_range.restrict_query(
        select(  # noqa
            Request.requested_at
        ).where(
            Request.requested_at != None,  # noqa
        ),
        Request.requested_at
    )
    resolutions_query = report_range.restrict_query(
        select(  # noqa
            LoggedEvent.timestamp
        ).where(
            LoggedEvent.event_type == LoggedEventTypeID.REQUEST_RESOLUTION_ADDED,
            col(LoggedEvent.custom_data).contains('"is_first": "True"')
        ),
        LoggedEvent.timestamp
    )

    with Session(engine) as session:
        addends: list[tuple[datetime, int]] = [
            (created_at, 1)
            for created_at in session.exec(creates_query)
        ] + [
            (resolved_at, -1)
            for resolved_at in session.exec(resolutions_query)
        ]

    range_start = report_range.get_first_bin_value()
    range_end = report_range.get_last_bin_value()
    total_changes = defaultdict(int)
    for change_ts, addend in addends:
        current_bin = report_range.get_bin(change_ts).value
        if not range_start or current_bin < range_start:
            range_start = current_bin
        if not range_end or current_bin > range_end:
            range_end = current_bin
        total_changes[current_bin] += addend

    result = {}
    full_range = pd.date_range(
        start=range_start,
        end=range_end,
        freq=timedelta(weeks=1) if report_range.weekly_granularity else timedelta(days=1)
    )
    pending_requests_at_bin_start = a_priori_pending_requests
    for ts in full_range.to_list():
        current_bin = report_range.get_bin(ts)
        current_value = pending_requests_at_bin_start + total_changes[current_bin.value]
        result[current_bin.name] = current_value
        pending_requests_at_bin_start = current_value

    column_names = [report_range.get_x_axis_name(), 'Pending Requests']
    df = pd.DataFrame(result.items(), columns=column_names)
    fig = px.line(
        df,
        x=column_names[0],
        y=column_names[1],
        title=f'Pending requests at the end of the {"week" if report_range.weekly_granularity else "day"}',
        subtitle=report_range.get_plot_subtitle()
    )
    if get_parameter_value(ParameterID.QUEUE_BLOCK_ENABLED, bool):
        fig.add_hline(
            y=get_parameter_value(ParameterID.QUEUE_BLOCK_AT, int),
            line_dash="dash",
            line_color="red",
            annotation_text="Queue block threshold (current)",
            annotation_position="bottom right"
        )
    if get_parameter_value(ParameterID.QUEUE_UNBLOCK_ENABLED, bool):
        fig.add_hline(
            y=get_parameter_value(ParameterID.QUEUE_UNBLOCK_AT, int),
            line_dash="dash",
            line_color="green",
            annotation_text="Queue unblock threshold (current)",
            annotation_position="bottom right"
        )
    return __save_figure(fig)


async def reviewer_opinions(reviewer: Member, report_range: SimpleReportRange) -> str:
    with Session(engine) as session:
        opinions = session.exec(
            report_range.restrict_query(
                select(  # noqa
                    RequestOpinion.opinion,
                    func.count(distinct(RequestOpinion.request_id))
                ).where(
                    RequestOpinion.author_user_id == reviewer.id
                ),
                RequestOpinion.created_at
            ).group_by(
                RequestOpinion.opinion
            )
        )
    column_names = ['Resolution', 'Count']
    df = pd.DataFrame(opinions, columns=column_names)
    fig = px.pie(
        df,
        names=column_names[0],
        values=column_names[1],
        color=column_names[0],
        color_discrete_map={
            Opinion.APPROVED: 'green',
            Opinion.REJECTED: 'red'
        },
        hole=0.5,
        title=f"Opinions left by {reviewer.name}",
        subtitle=report_range.get_plot_subtitle()
    )
    fig.update_traces(textinfo="value+percent")
    return __save_figure(fig)


async def review_activity(report_range: ReportRange) -> str:
    with Session(engine) as session:
        result = session.exec(
            report_range.restrict_query(
                select(
                    RequestReview.author_user_id,
                    RequestReview.created_at
                ),
                RequestReview.created_at
            )
        )

    data_with_gaps = defaultdict(int)
    range_start = report_range.get_first_bin_value()
    range_end = report_range.get_last_bin_value()
    reviewers_by_id = dict()
    for author_user_id, created_at in result:  # noqa
        current_bin = report_range.get_bin(created_at).value
        if not range_start or current_bin < range_start:
            range_start = current_bin
        if not range_end or current_bin > range_end:
            range_end = current_bin

        if author_user_id not in reviewers_by_id:
            reviewer = await find_member(author_user_id)
            reviewers_by_id[author_user_id] = reviewer
        else:
            reviewer = reviewers_by_id[author_user_id]

        if reviewer:
            data_with_gaps[(author_user_id, current_bin)] += 1

    reviewers = [reviewer for reviewer in reviewers_by_id.values() if reviewer]

    result = []
    full_range = pd.date_range(
        start=range_start,
        end=range_end,
        freq=timedelta(weeks=1) if report_range.weekly_granularity else timedelta(days=1)
    )
    for ts in full_range.to_list():
        current_bin = report_range.get_bin(ts)
        for reviewer in reviewers:
            value = data_with_gaps[(reviewer.id, current_bin.value)]
            result.append((reviewer.name, current_bin.name, value))

    column_names = ['Reviewer', report_range.get_x_axis_name(), 'Reviews Written']
    df = pd.DataFrame(result, columns=column_names)
    fig = px.line(df, x=column_names[1], y=column_names[2], color=column_names[0], title='Reviews Written by Staff Members', subtitle=report_range.get_plot_subtitle())
    return __save_figure(fig)