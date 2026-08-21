# ruff: noqa: RUF001
"""Centralized safe public messages for the Persian-first API."""

PUBLIC_ERROR_MESSAGES_FA_IR: dict[str, str] = {
    "AUTH_INVALID_CREDENTIALS": "نام کاربری یا گذرواژه صحیح نیست.",
    "AUTH_TOKEN_EXPIRED": "نشست شما منقضی شده است. لطفاً دوباره وارد شوید.",
    "AUTH_REQUIRED": "برای انجام این عملیات باید وارد سامانه شوید.",
    "PERMISSION_DENIED": "شما اجازه انجام این عملیات را ندارید.",
    "WORKSPACE_ACCESS_DENIED": "شما به این فضای کاری دسترسی ندارید.",
    "RESOURCE_NOT_FOUND": "مورد درخواستی یافت نشد.",
    "RESOURCE_CONFLICT": "این عملیات با وضعیت فعلی مورد درخواستی سازگار نیست.",
    "STALE_VERSION": "این مورد پس از بارگذاری تغییر کرده است. صفحه را تازه‌سازی کنید.",
    "RESOURCE_LOCKED": "این مورد در مرحله قفل‌شده قرار دارد و قابل ویرایش نیست.",
    "VALIDATION_ERROR": "یک یا چند فیلد نامعتبر است.",
    "INVALID_METADATA": "پیکربندی فراداده نامعتبر است.",
    "INVALID_RELATIONSHIP": "رابطه درخواستی نامعتبر است.",
    "HIERARCHY_CYCLE": "این تغییر در ساختار سلسله‌مراتبی یک چرخه ایجاد می‌کند.",
    "FILE_TOO_LARGE": "حجم فایل بارگذاری‌شده از حد مجاز بیشتر است.",
    "FILE_TYPE_NOT_ALLOWED": "نوع فایل بارگذاری‌شده مجاز نیست.",
    "FILE_SCAN_FAILED": "بررسی امنیتی فایل کامل نشد. لطفاً دوباره تلاش کنید.",
    "IMPORT_VALIDATION_FAILED": "داده‌های ورودی دارای خطاهای اعتبارسنجی است.",
    "IMPORT_CONFLICTS_UNRESOLVED": "داده‌های ورودی دارای تعارض‌های حل‌نشده است.",
    "IMPORT_ALREADY_COMMITTED": "این عملیات ورود داده قبلاً ثبت نهایی شده است.",
    "FORM_NOT_PUBLISHED": "فرم درخواستی منتشر نشده است.",
    "FORM_VERSION_CONFLICT": "نسخه این فرم دیگر نسخه جاری نیست.",
    "RATE_LIMITED": "تعداد درخواست‌ها بیش از حد مجاز است. لطفاً کمی بعد تلاش کنید.",
    "INTERNAL_ERROR": "خطای پیش‌بینی‌نشده‌ای رخ داد.",
    "DEPENDENCY_UNAVAILABLE": "یکی از سرویس‌های موردنیاز موقتاً در دسترس نیست.",
}


def public_error_message(code: str) -> str:
    """Return safe Persian copy for a registered stable error code."""
    try:
        return PUBLIC_ERROR_MESSAGES_FA_IR[code]
    except KeyError as exc:
        raise ValueError(f"No fa-IR public message is registered for error code {code!r}") from exc
