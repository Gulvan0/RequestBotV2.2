from enum import Enum, unique


@unique
class TextPieceID(Enum):
    COMMON_SUCCESS = "common.success"
    WARNING_NO_EFFECT = "warning.no_effect"
    ERROR_FORBIDDEN = "error.forbidden"
    ERROR_WRONG_PARAMETER_VALUE_TYPE = "error.wrong_parameter_value_type"
    ERROR_BAD_DURATION_FORMAT = "error.bad_duration_format"
    ERROR_EXPECTED_POSITIVE_DURATION = "errors.expected_positive_duration"
    ERROR_DURATION_EXCEEDS_MAX_ALLOWED = "errors.duration_exceeds_max_allowed"


@unique
class RouteID(Enum):
    PENDING_REQUEST = "pending_request"
    PRE_APPROVAL_NOTIFICATION = "pre_approval_notification"
    PRE_REJECTION_NOTIFICATION = "pre_rejection_notification"
    DISCARD_NOTIFICATION = "discard_notification"
    APPROVAL_NOTIFICATION = "approval_notification"
    REJECTION_NOTIFICATION = "rejection_notification"
    PRE_APPROVED_VERIFICATION = "pre_approved_verification"
    PRE_REJECTED_VERIFICATION = "pre_rejected_verification"
    REVIEW_TEXT = "review_text"
    REQUESTS_CLOSED = "requests_closed"
    REQUESTS_REOPENED = "requests_reopened"


@unique
class ParameterID(Enum):
    QUEUE_BLOCK_AT = "queue.block_at"
    QUEUE_UNBLOCK_AT = "queue.unblock_at"
    QUEUE_BLOCK_ENABLED = "queue.block_enabled"
    QUEUE_UNBLOCK_ENABLED = "queue.unblock_enabled"
    QUEUE_BLOCKED_MANUALLY = "queue.blocked_manually"
