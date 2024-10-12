from dataclasses import dataclass
from sqlmodel import Session

from config.routes import get_default_channel_id, get_description
from database.db import engine
from database.models import Route
from util.exceptions import AlreadySatisfiesError
from util.identifiers import RouteID


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


def update_channel_id(route_id: RouteID, channel_id: int) -> None:
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


def reset_channel_id(route_id: RouteID) -> None:
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


def enable(route_id: RouteID) -> None:
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


def disable(route_id: RouteID) -> None:
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


def explain(route_id: RouteID) -> RouteDetails:
    return RouteDetails(
        description=get_description(route_id),
        default_channel_id=get_default_channel_id(route_id),
        current_channel_id=get_channel_id(route_id),
        is_enabled=is_enabled(route_id)
    )
