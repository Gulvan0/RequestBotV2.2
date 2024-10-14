from collections import defaultdict

import discord
from sqlalchemy import Select
from sqlmodel import select, Session

from database.db import engine
from database.models import PermissionFlag
from util.exceptions import AlreadySatisfiesError
from util.identifiers import PermissionFlagID


def has_permission(member: discord.Member, permission: PermissionFlagID) -> bool:
    member_roles = set(map(lambda role: role.id, member.roles))

    with Session(engine) as session:
        query: Select = select(PermissionFlag.role_id).where(PermissionFlag.id == permission)
        required_roles = set(session.exec(query))

    return bool(member_roles & required_roles)


def bind(role: discord.Role, permission: PermissionFlagID) -> None:
    with Session(engine) as session:
        existing_entry = session.get(PermissionFlag, (permission, role.id))
        if existing_entry:
            raise AlreadySatisfiesError

        new_entry = PermissionFlag(id=permission, role_id=role.id)
        session.add(new_entry)
        session.commit()


def unbind(role: discord.Role, permission: PermissionFlagID) -> None:
    with Session(engine) as session:
        existing_entry = session.get(PermissionFlag, (permission, role.id))
        if not existing_entry:
            raise AlreadySatisfiesError

        session.delete(existing_entry)
        session.commit()


def clear(role: discord.Role) -> None:
    with Session(engine) as session:
        had_permissions = False
        query: Select = select(PermissionFlag).where(PermissionFlag.role_id == role.id)
        for entry in session.exec(query):
            had_permissions = True
            session.delete(entry)

        if not had_permissions:
            raise AlreadySatisfiesError

        session.commit()


def list_bound_roles(member: discord.Member | None = None) -> dict[int, list[PermissionFlagID]]:
    member_roles = set(map(lambda role: role.id, member.roles)) if member else set()

    d = defaultdict(list)
    with Session(engine) as session:
        for entry in session.exec(select(PermissionFlag)):
            if not member or entry.role_id in member_roles:
                d[entry.role_id].append(entry.id)
    return d


def is_permission_assigned(permission: PermissionFlagID) -> bool:
    with Session(engine) as session:
        query: Select = select(PermissionFlag).where(PermissionFlag.id == permission)
        return bool(session.exec(query).first())
