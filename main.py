import click
import logging

from config.texts import validate as validate_texts
from config.routes import enlist, validate as validate_routes
from database.db import create_db_and_tables
from database.models import *  # noqa
from globalconf import CONFIG
from routes import explain, get_channel_id, reset_channel_id, update_channel_id
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
def main(debug, log_queries):
    logging.basicConfig()
    if log_queries:
        logger = logging.getLogger('sqlalchemy.engine')
        logger.setLevel(logging.DEBUG)

    CONFIG.stage = Stage.TEST if debug else Stage.PROD

    create_db_and_tables()

    validate_texts()
    validate_routes()

    print(enlist())
    print(explain(RouteID.APPROVAL_NOTIFICATION))

    print(get_channel_id(RouteID.APPROVAL_NOTIFICATION))
    update_channel_id(RouteID.APPROVAL_NOTIFICATION, -1)
    reset_channel_id(RouteID.APPROVAL_NOTIFICATION)

if __name__ == "__main__":
    main()
