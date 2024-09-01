from enum import Enum, unique


@unique
class TextPieceID(Enum):
    COMMON_SUCCESS = "common.success"
    ERROR_FORBIDDEN = "error.forbidden"
    ERROR_BAD_DURATION_FORMAT = "error.bad_duration_format"
    ERROR_EXPECTED_POSITIVE_DURATION = "errors.expected_positive_duration"
    ERROR_DURATION_EXCEEDS_MAX_ALLOWED = "errors.duration_exceeds_max_allowed"
