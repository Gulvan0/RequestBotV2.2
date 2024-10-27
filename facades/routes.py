from dataclasses import dataclass

from discord import Member
from sqlmodel import Session

from config.routes import get_default_channel_id, get_description
from database.db import engine
from database.models import Route
from facades.eventlog import add_entry
from util.exceptions import AlreadySatisfiesError
from util.identifiers import LoggedEventTypeID, RouteID


@dataclass
class RouteDetails:
    description: str
    default_channel_id: int
    current_channel_id: int
    is_enabled: bool


def get_channel_id(route_id: RouteID) -> int:
    with Session(engine) as session:
        result = session.get(Route, route_id)

    if result and result.channel_id:
        return result.channel_id

    return get_default_channel_id(route_id)


def is_enabled(route_id: RouteID) -> bool:
    with Session(engine) as session:
        result = session.get(Route, route_id)
    return result.enabled if result else True


async def update_channel_id(route_id: RouteID, channel_id: int, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        route = session.get(Route, route_id)
        if route:
            if route.channel_id == channel_id:
                raise AlreadySatisfiesError
            elif route.channel_id is None and get_default_channel_id(route_id) == channel_id:
                raise AlreadySatisfiesError
            route.channel_id = channel_id
        else:
            if get_default_channel_id(route_id) == channel_id:
                raise AlreadySatisfiesError
            route = Route(id=route_id, channel_id=channel_id, enabled=True)
        session.add(route)
        session.commit()

    await add_entry(LoggedEventTypeID.ROUTE_TARGET_UPDATED, invoker, dict(
        route_id=route_id.value,
        new_channel_id=str(channel_id)
    ))


async def reset_channel_id(route_id: RouteID, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        route = session.get(Route, route_id)
        if not route:
            raise AlreadySatisfiesError

        if route.enabled:
            session.delete(route)
        elif route.channel_id:
            route.channel_id = None
            session.add(route)
        else:
            raise AlreadySatisfiesError

        session.commit()

    await add_entry(LoggedEventTypeID.ROUTE_TARGET_UPDATED, invoker, dict(
        route_id=route_id.value,
        new_channel_id=str(get_default_channel_id(route_id))
    ))


async def enable(route_id: RouteID, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        route = session.get(Route, route_id)
        if not route or route.enabled:
            raise AlreadySatisfiesError

        if route.channel_id:
            route.enabled = True
            session.add(route)
        else:
            session.delete(route)

        session.commit()

    await add_entry(LoggedEventTypeID.ROUTE_TOGGLED, invoker, dict(
        route_id=route_id.value,
        enabled="True"
    ))


async def disable(route_id: RouteID, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        route = session.get(Route, route_id)

        if not route:
            route = Route(id=route_id, channel_id=None, enabled=False)
        elif route.enabled:
            route.enabled = False
        else:
            raise AlreadySatisfiesError

        session.add(route)
        session.commit()

    await add_entry(LoggedEventTypeID.ROUTE_TOGGLED, invoker, dict(
        route_id=route_id.value,
        enabled="False"
    ))


def explain(route_id: RouteID) -> RouteDetails:
    return RouteDetails(
        description=get_description(route_id),
        default_channel_id=get_default_channel_id(route_id),
        current_channel_id=get_channel_id(route_id),
        is_enabled=is_enabled(route_id)
    )
