from dataclasses import dataclass

from discord import Guild, Member
from discord.ext.commands import Bot

from util.datatypes import Stage


@dataclass
class GlobalConfiguration:
    bot: Bot | None = None
    guild: Guild | None = None
    admin: Member | None = None
    stage: Stage = Stage.TEST


CONFIG = GlobalConfiguration()
