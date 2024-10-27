from enum import Enum, unique


@unique
class LoggedEventTypeID(Enum):
    TEXT_PIECE_EDITED = "TEXT_PIECE_EDITED"
    ROUTE_TARGET_UPDATED = "ROUTE_TARGET_UPDATED"
    ROUTE_TOGGLED = "ROUTE_TOGGLED"
    PARAMETER_EDITED = "PARAMETER_EDITED"
    PERMISSION_BOUND = "PERMISSION_BOUND"
    PERMISSION_UNBOUND = "PERMISSION_UNBOUND"
    ROLE_CLEARED_FROM_PERMISSIONS = "ROLE_CLEARED_FROM_PERMISSIONS"
    USER_PREFERENCE_UPDATED = "USER_PREFERENCE_UPDATED"


@unique
class TextPieceID(Enum):
    COMMON_SUCCESS = "common.success"
    COMMON_LANGUAGE_SELECTION_PROPOSAL_SUBTEXT = "common.language_selection_proposal_subtext"
    PERMISSION_NO_ASSIGNED_ROLES = "permission.no_assigned_roles"
    PERMISSION_MEMBER_HAS_NO_PERMISSIONS = "permission.member_has_no_permissions"
    LOG_NO_ENTRIES = "log.no_entries"
    LOG_NO_FILTERS = "log.no_filters"
    LOG_TOP_REACHED = "log.top_reached"
    LOG_BOTTOM_REACHED = "log.bottom_reached"
    LOG_EMPTY_FILTER = "log.empty_filter"
    LOG_EMPTY_FILTER_WONT_BE_SAVED = "log.empty_filter_wont_be_saved"
    REQUEST_COMMAND_CLOSED = "request_command.closed"
    REQUEST_COMMAND_UNFEATURED = "request_command.unfeatured"
    REQUEST_COMMAND_ALREADY_RATED = "request_command.already_rated"
    REQUEST_COMMAND_NOT_FOUND = "request_command.not_found"
    CONFIRMATION_OVERRIDE_FILTER = "confirmation.override_filter"
    CONFIRMATION_DELETE_FILTER = "confirmation.delete_filter"
    WARNING_NO_EFFECT = "warning.no_effect"
    ERROR_COMPONENT_ERROR = "error.component_error"
    ERROR_COMMAND_ERROR = "error.command_error"
    ERROR_FORBIDDEN = "error.forbidden"
    ERROR_FILTER_DOESNT_EXIST = "error.filter_doesnt_exist"
    ERROR_CANT_PARSE_TIMESTAMP = "error.cant_parse_timestamp"
    ERROR_CANT_REMOVE_ADMIN_PERMISSION = "error.cant_remove_admin_permission"
    ERROR_WRONG_PARAMETER_VALUE_TYPE = "error.wrong_parameter_value_type"
    ERROR_BAD_DURATION_FORMAT = "error.bad_duration_format"
    ERROR_EXPECTED_POSITIVE_DURATION = "error.expected_positive_duration"


@unique
class RouteID(Enum):
    LOG = "log"
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
    LOG_VIEWER = "log_viewer"
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
    DEVELOPER_USER_IDS = "developer_user_ids"


@unique
class UserPreferenceID(Enum):
    LANGUAGE = "language"