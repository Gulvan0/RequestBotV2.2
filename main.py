import sys

from config.texts import validate as validate_texts
from config.routes import enlist, validate as validate_routes
from database.db import create_db_and_tables
from database.models import *  # noqa
from globalconf import GlobalConfiguration
from routes import explain
from util.datatypes import Stage


def main():
    GlobalConfiguration.stage = Stage.TEST if "-debug" in sys.argv else Stage.PROD

    create_db_and_tables()

    validate_texts()
    validate_routes()

    print(enlist())
    print(explain(RouteID.APPROVAL_NOTIFICATION))


if __name__ == "__main__":
    main()
