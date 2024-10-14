from enum import Enum, unique


@unique
class TextPieceID(Enum):
    COMMON_SUCCESS = "common.success"
    COMMON_LANGUAGE_SELECTION_PROPOSAL_SUBTEXT = "common.language_selection_proposal_subtext"
    PERMISSION_NO_ASSIGNED_ROLES = "permission.no_assigned_roles"
    PERMISSION_MEMBER_HAS_NO_PERMISSIONS = "permission.member_has_no_permissions"
    WARNING_NO_EFFECT = "warning.no_effect"
    ERROR_FORBIDDEN = "error.forbidden"
    ERROR_CANT_REMOVE_ADMIN_PERMISSION = "error.cant_remove_admin_permission"
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


@unique
class PermissionFlagID(Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    TRAINEE = "trainee"
    GD_MOD = "gd_mod"
    BAN_LEVELS = "ban_levels"
    BAN_USERS = "ban_users"
    REMOVE_OTHER_LEVEL_BANS = "remove_other_level_bans"
    REMOVE_OTHER_USER_BANS = "remove_other_user_bans"


@unique
class StageParameterID(Enum):
    SPEAKS_RUSSIAN_ROLE_ID = "speaks_russian_role_id"
    ADMIN_USER_ID = "admin_user_id"


@unique
class UserPreferenceID(Enum):
    LANGUAGE = "language"