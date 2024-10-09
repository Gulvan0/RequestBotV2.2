import click
import logging

from config.texts import validate as validate_texts
from config.routes import validate as validate_routes
from config.parameters import validate as validate_parameters
from database.db import create_db_and_tables
from database.models import *  # noqa
from globalconf import CONFIG
from util.datatypes import Stage


@click.command
@click.option(
    "--debug",
    is_flag=True,
    help="Use testing server"
)
@click.option(
    "--log_queries",
    is_flag=True,
    help="Log queries to the output"
)
def main(debug: bool, log_queries: bool) -> None:
    logging.basicConfig()
    if log_queries:
        logger = logging.getLogger('sqlalchemy.engine')
        logger.setLevel(logging.DEBUG)

    CONFIG.stage = Stage.TEST if debug else Stage.PROD

    create_db_and_tables()

    validate_texts()
    validate_routes()
    validate_parameters()

    # FILL

if __name__ == "__main__":
    main()
