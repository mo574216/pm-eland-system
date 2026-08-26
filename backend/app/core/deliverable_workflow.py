"""Built-in installable metadata profile for the governed deliverable demo flow."""

DELIVERABLE_WORKFLOW_KEY = "system_deliverable_lifecycle"
DELIVERABLE_WORKFLOW_NAME = "چرخه عمومی تحویل‌دادنی"

DELIVERABLE_STATES = (
    ("preparation", "در حال آماده‌سازی", 1, True, False),
    ("internal_review", "در بازبینی داخلی", 2, False, False),
    ("ready", "آماده ارسال رسمی", 3, False, False),
    ("submitted", "ارسال رسمی شده", 4, False, False),
)

DELIVERABLE_TRANSITIONS: tuple[
    tuple[str, str, str, str, str, str, str, bool, dict[str, bool]], ...
] = (
    (
        "request_internal_review",
        "ارسال برای بازبینی داخلی",
        "preparation",
        "internal_review",
        "DELIVERABLE_CONTRIBUTE",
        "CONTRIBUTION",
        "CONTRIBUTOR",
        False,
        {"requires_package_readiness": True},
    ),
    (
        "request_correction",
        "بازگرداندن برای اصلاح",
        "internal_review",
        "preparation",
        "DELIVERABLE_INTERNAL_REVIEW",
        "INTERNAL_REVIEW",
        "INTERNAL_REVIEWER",
        True,
        {},
    ),
    (
        "mark_ready",
        "تأیید آمادگی برای ارسال",
        "internal_review",
        "ready",
        "DELIVERABLE_INTERNAL_REVIEW",
        "INTERNAL_REVIEW",
        "INTERNAL_REVIEWER",
        False,
        {"requires_package_readiness": True},
    ),
    (
        "formal_submit",
        "ارسال رسمی",
        "ready",
        "submitted",
        "SUBMISSION_CREATE",
        "FORMAL_SUBMISSION",
        "OWNER",
        False,
        {"requires_active_submission": True},
    ),
    (
        "withdraw_submission",
        "پس گرفتن ارسال رسمی",
        "submitted",
        "ready",
        "SUBMISSION_CREATE",
        "FORMAL_SUBMISSION",
        "OWNER",
        True,
        {"requires_submission_withdrawal": True},
    ),
    (
        "project_request_revision",
        "درخواست اصلاح توسط مدیر پروژه",
        "submitted",
        "preparation",
        "PROJECT_REVIEW",
        "PROJECT_REVIEW",
        "REVIEW_RECIPIENT",
        True,
        {"requires_review_outcome": True},
    ),
    (
        "technical_request_revision",
        "درخواست اصلاح فنی",
        "submitted",
        "preparation",
        "TECHNICAL_REVIEW",
        "TECHNICAL_REVIEW",
        "REVIEW_RECIPIENT",
        True,
        {"requires_review_outcome": True},
    ),
)
