from config.texts import enlist, validate
from database.db import create_db_and_tables
from database.models import *  # noqa
from texts.texts import explain, get_template, render_text, reset_template, update_template
from util.identifiers import TextPieceID


def main():
    create_db_and_tables()

    validate()

    # print(explain(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION))
    #
    # print(get_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN))
    # print(get_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU))
    # print(render_text(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN, dict(duration_secs=20)))
    # print(render_text(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU, dict(duration_secs=20)))
    #
    # update_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU, "да пошел ты нахуй")
    #
    # print(get_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN))
    # print(get_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU))
    # print(render_text(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN, dict(duration_secs=20)))
    # print(render_text(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU, dict(duration_secs=20)))
    #
    # reset_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN)
    # reset_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU)
    #
    # print(get_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN))
    # print(get_template(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU))
    # print(render_text(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.EN, dict(duration_secs=20)))
    # print(render_text(TextPieceID.ERROR_EXPECTED_POSITIVE_DURATION, Language.RU, dict(duration_secs=20)))
    #
    # print(enlist())



if __name__ == "__main__":
    main()
