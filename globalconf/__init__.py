from dataclasses import dataclass

from discord import Guild
from discord.ext.commands import Bot

from util.datatypes import Stage


@dataclass
class GlobalConfiguration:
    bot: Bot | None = None
    guild: Guild | None = None
    stage: Stage = Stage.TEST


CONFIG = GlobalConfiguration()
