from collections import defaultdict
from datetime import datetime, timedelta

from plotly.graph_objs import Figure
from sqlalchemy import func
from sqlmodel import col, select, Session
from database.db import engine

import pandas as pd
import plotly.express as px

from database.models import Request


def __save_figure(fig: Figure) -> str:
    filename = str(round(datetime.now().timestamp() * 1000000)) + ".png"
    fig.write_image(filename)
    return filename


def new_requests(ts_from: datetime | None, ts_to: datetime | None, ts_to_passed_as_date: bool) -> str:
    query = select(Request.requested_at).where(Request.requested_at != None)  # noqa
    if ts_from:
        query = query.where(Request.requested_at >= ts_from)
    if ts_to:
        upper_value = ts_to + timedelta(days=1) if ts_to_passed_as_date else ts_to
        query = query.where(Request.requested_at <= upper_value)

    data_with_gaps = defaultdict(int)
    min_day = ts_from.date().isoformat() if ts_from else None
    max_day = ts_to.date().isoformat() if ts_to else None
    with Session(engine) as session:
        for requested_at in session.exec(query):
            day = requested_at.date().isoformat()
            if not min_day or day < min_day:
                min_day = day
            if not max_day or day > max_day:
                max_day = day
            data_with_gaps[day] += 1

    result = {}
    for ts in pd.date_range(min_day, max_day).to_list():
        day = ts.date().isoformat()
        result[day] = data_with_gaps[day] if day in data_with_gaps else 0

    df = pd.DataFrame(result.items(), columns=['Date', 'New Requests'])
    fig = px.line(df, x='Date', y="New Requests")
    return __save_figure(fig)