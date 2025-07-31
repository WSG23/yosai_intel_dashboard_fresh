"""Common regex patterns for security checks."""

SQL_INJECTION_PATTERNS = [
    r"(\b(select|insert|update|delete|drop|create|alter|exec|execute)\b)",
    r"(\bunion\b.*\bselect\b)",
    r"(\bor\b.*=.*\bor\b)",
    r"(\band\b.*=.*\band\b)",
    r"(--|\#|\/\*|\*\/)",
    r"(\bxp_cmdshell\b|\bsp_executesql\b)",
    r"(;\s*(drop|delete|truncate|alter)\b)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
    r"vbscript:",
    r"expression\s*\(",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\.\/",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e%5c",
    r"\.\.%2f",
    r"\.\.%5c",
]

__all__ = [
    "SQL_INJECTION_PATTERNS",
    "XSS_PATTERNS",
    "PATH_TRAVERSAL_PATTERNS",
]
