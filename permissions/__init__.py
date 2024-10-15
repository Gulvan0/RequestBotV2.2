from collections import defaultdict

import discord
from discord import Member
from sqlalchemy import Select
from sqlmodel import select, Session

from database.db import engine
from database.models import PermissionFlag
from eventlog import add_entry
from util.exceptions import AlreadySatisfiesError
from util.identifiers import LoggedEventTypeID, PermissionFlagID


def has_permission(member: discord.Member, permission: PermissionFlagID) -> bool:
    member_roles = set(map(lambda role: role.id, member.roles))

    with Session(engine) as session:
        query: Select = select(PermissionFlag.role_id).where(PermissionFlag.id == permission)
        required_roles = set(session.exec(query))

    return bool(member_roles & required_roles)


def bind(role: discord.Role, permission: PermissionFlagID, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        existing_entry = session.get(PermissionFlag, (permission, role.id))
        if existing_entry:
            raise AlreadySatisfiesError

        new_entry = PermissionFlag(id=permission, role_id=role.id)
        session.add(new_entry)
        session.commit()

    add_entry(LoggedEventTypeID.PERMISSION_BOUND, invoker, dict(
        permission_id=permission.value,
        role_id=str(role.id)
    ))


def unbind(role: discord.Role, permission: PermissionFlagID, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        existing_entry = session.get(PermissionFlag, (permission, role.id))
        if not existing_entry:
            raise AlreadySatisfiesError

        session.delete(existing_entry)
        session.commit()

    add_entry(LoggedEventTypeID.PERMISSION_UNBOUND, invoker, dict(
        permission_id=permission.value,
        role_id=str(role.id)
    ))


def clear(role: discord.Role, invoker: Member | None = None) -> None:
    with Session(engine) as session:
        had_permissions = False
        query: Select = select(PermissionFlag).where(PermissionFlag.role_id == role.id)
        for entry in session.exec(query):
            had_permissions = True
            session.delete(entry)

        if not had_permissions:
            raise AlreadySatisfiesError

        session.commit()

    add_entry(LoggedEventTypeID.ROLE_CLEARED_FROM_PERMISSIONS, invoker, dict(
        role_id=str(role.id)
    ))


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
