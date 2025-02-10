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
    USER_COOLDOWN_UPDATED = "USER_COOLDOWN_UPDATED"
    LEVEL_COOLDOWN_UPDATED = "LEVEL_COOLDOWN_UPDATED"
    REQUEST_INITIALIZED = "REQUEST_INITIALIZED"
    REQUEST_REQUESTED = "REQUEST_REQUESTED"
    REQUEST_OPINION_ADDED = "REQUEST_OPINION_ADDED"
    REQUEST_RESOLUTION_ADDED = "REQUEST_RESOLUTION_ADDED"


@unique
class TextPieceID(Enum):
    COMMON_SUCCESS = "common.success"
    COMMON_LANGUAGE_SELECTION_PROPOSAL_SUBTEXT = "common.language_selection_proposal_subtext"
    COMMON_NOT_SPECIFIED = "common.not_specified"
    PERMISSION_NO_ASSIGNED_ROLES = "permission.no_assigned_roles"
    PERMISSION_MEMBER_HAS_NO_PERMISSIONS = "permission.member_has_no_permissions"
    PAGINATION_TOP_REACHED = "pagination.top_reached"
    PAGINATION_BOTTOM_REACHED = "pagination.bottom_reached"
    PAGINATION_NO_ENTRIES = "pagination.no_entries"
    COOLDOWN_OVERWRITE_CONFIRMATION = "cooldown.overwrite_confirmation"
    COOLDOWN_NOT_ON_COOLDOWN = "cooldown.not_on_cooldown"
    COOLDOWN_INFO = "cooldown.info"
    HELP_DURATION = "help.duration"
    HELP_TIMESTAMP = "help.timestamp"
    LOG_NO_FILTERS = "log.no_filters"
    LOG_EMPTY_FILTER = "log.empty_filter"
    LOG_EMPTY_FILTER_WONT_BE_SAVED = "log.empty_filter_wont_be_saved"
    REQUEST_MODAL_TITLE = "request_modal.title"
    REQUEST_MODAL_YT_LINK_LABEL = "request_modal.yt_link.label"
    REQUEST_MODAL_ADDITIONAL_COMMENT_LABEL = "request_modal.additional_comment.label"
    REQUEST_MODAL_ADDITIONAL_COMMENT_PLACEHOLDER = "request_modal.additional_comment.placeholder"
    REQUEST_MODAL_INVALID_YT_LINK = "request_modal.invalid_yt_link"
    REQUEST_PENDING_WIDGET_OPINION_ALREADY_EXISTS = "request_pending_widget.opinion_already_exists"
    REQUEST_RESOLUTION_WIDGET_RESOLUTION_ALREADY_EXISTS = "request_resolution_widget.resolution_already_exists"
    REQUEST_OPINION_MODAL_TITLE = "request_opinion_modal.title"
    REQUEST_OPINION_MODAL_REASON_LABEL = "request_opinion_modal.reason.label"
    REQUEST_OPINION_MODAL_REASON_PLACEHOLDER = "request_opinion_modal.reason.placeholder"
    REQUEST_OPINION_MODAL_REVIEW_LABEL = "request_opinion_modal.review.label"
    REQUEST_OPINION_MODAL_REVIEW_PLACEHOLDER = "request_opinion_modal.review.placeholder"
    REQUEST_COMMAND_SUBMITTED = "request_command.submitted"
    REQUEST_COMMAND_CLOSED = "request_command.closed"
    REQUEST_COMMAND_ALREADY_RATED = "request_command.already_rated"
    REQUEST_COMMAND_NOT_FOUND = "request_command.not_found"
    REQUEST_COMMAND_ALREADY_APPROVED = "request_command.already_approved"
    REQUEST_COMMAND_PREVIOUS_PENDING = "request_command.previous_pending"
    REQUEST_COMMAND_USER_ON_COOLDOWN = "request_command.user_on_cooldown"
    REQUEST_COMMAND_USER_BANNED_TEMPORARILY = "request_command.user_banned_temporarily"
    REQUEST_COMMAND_USER_BANNED_FOREVER = "request_command.user_banned_forever"
    REQUEST_COMMAND_LEVEL_ON_COOLDOWN = "request_command.level_on_cooldown"
    REQUEST_COMMAND_LEVEL_BANNED_TEMPORARILY = "request_command.level_banned_temporarily"
    REQUEST_COMMAND_LEVEL_BANNED_FOREVER = "request_command.level_banned_forever"
    REQUEST_REVIEW = "request.review"
    REQUEST_SUMMARY_GOOD = "request.review.summary.good"
    REQUEST_SUMMARY_BAD = "request.review.summary.bad"
    REQUEST_APPROVED = "request.approved"
    REQUEST_GRADE_STARRATE = "request.approved.grade.starrate"
    REQUEST_GRADE_FEATURED = "request.approved.grade.featured"
    REQUEST_GRADE_EPIC = "request.approved.grade.epic"
    REQUEST_GRADE_MYTHIC = "request.approved.grade.mythic"
    REQUEST_GRADE_LEGENDARY = "request.approved.grade.legendary"
    REQUEST_REJECTED = "request.rejected"
    QUEUE_QUEUE_CLOSED_ERROR = "queue.queue_closed_error"
    QUEUE_INFO = "queue.info"
    QUEUE_INFO_OPEN_HEADER = "queue.info.open_header"
    QUEUE_INFO_CLOSED_HEADER = "queue.info.closed_header"
    QUEUE_INFO_DISABLED = "queue.info.disabled"
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
    ERROR_ORIGIN_COOLDOWN_ENDLESS = "error.origin_cooldown_endless"
    ERROR_COOLDOWN_END_IN_PAST = "error.cooldown_end_in_past"


@unique
class RouteID(Enum):
    LOG = "log"
    PENDING_REQUEST = "pending_request"
    RESOLUTION = "resolution"
    APPROVAL_NOTIFICATION = "approval_notification"
    REJECTION_NOTIFICATION = "rejection_notification"
    REVIEW_TEXT = "review_text"
    REQUESTS_CLOSED = "requests_closed"
    REQUESTS_REOPENED = "requests_reopened"
    ARCHIVE = "archive"


@unique
class ParameterID(Enum):
    QUEUE_BLOCK_AT = "queue.block_at"
    QUEUE_UNBLOCK_AT = "queue.unblock_at"
    QUEUE_BLOCK_ENABLED = "queue.block_enabled"
    QUEUE_UNBLOCK_ENABLED = "queue.unblock_enabled"
    QUEUE_BLOCKED = "queue.blocked"
    COOLDOWN_POST_REQUEST_USER_CD = "cooldown.post_request_user_cd"
    COOLDOWN_POST_REJECT_LEVEL_CD = "cooldown.post_reject_level_cd"


@unique
class PermissionFlagID(Enum):
    ADMIN = "admin"
    LOG_VIEWER = "log_viewer"
    REVIEWER = "reviewer"
    TRAINEE = "trainee"
    GD_MOD = "gd_mod"
    BAN_LEVELS = "ban_levels"
    BAN_USERS = "ban_users"
    NO_REQUEST_COOLDOWN = "no_request_cooldown"
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