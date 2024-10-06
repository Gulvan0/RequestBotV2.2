from sqlmodel import Session

from config.routes import get_default_channel_id, get_description
from database.db import engine
from database.models import Route
from util.format import as_channel
from util.identifiers import RouteID


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
            route.channel_id = channel_id
        else:
            route = Route(id=route_id, channel_id=channel_id, enabled=True)
        session.add(route)
        session.commit()


def reset_channel_id(route_id: RouteID) -> None:
    with Session(engine) as session:
        route = session.get(Route, route_id)
        if not route:
            return

        if route.enabled:
            session.delete(route)
        else:
            route.channel_id = None
            session.add(route)

        session.commit()


def enable(route_id: RouteID) -> None:
    with Session(engine) as session:
        route = session.get(Route, route_id)
        if not route or route.enabled:
            return

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
            return

        session.add(route)
        session.commit()


def explain(route_id: RouteID) -> str:
    desc = get_description(route_id)
    default_channel = get_default_channel_id(route_id)
    current_channel = get_channel_id(route_id)
    current_state = ':green_square: Включен' if is_enabled(route_id) else ':red_square: Выключен'

    return f"{desc}\n\n**Канал по умолчанию:** {as_channel(default_channel)}\n\n**Текущий канал:** {as_channel(current_channel)}\n\n**Текущее состояние:** {current_state}"
