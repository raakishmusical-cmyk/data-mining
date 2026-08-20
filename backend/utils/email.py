# import re

# EMAIL_REGEX = re.compile(
#     r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", re.IGNORECASE
# )

# # List of typical false positives/garbage file extensions mapped as emails
# GARBAGE_PATTERNS = [
#     r"\.png$", r"\.jpg$", r"\.jpeg$", r"\.gif$", r"\.css$", r"\.js$",
#     r"^email@", r"^info@", r"^support@" # Wait, info@ and support@ are valid emails, but let's exclude purely placeholder text
# ]

# def is_valid_email(email: str) -> bool:
#     """Validate format of an email address."""
#     if not email:
#         return False
#     email = email.strip()
#     if not EMAIL_REGEX.match(email):
#         return False
        
#     # Check against known garbage email suffixes (like image attachments scraped as text)
#     lower_email = email.lower()
#     for pattern in GARBAGE_PATTERNS[:6]: # Only check image/script extensions
#         if re.search(pattern, lower_email):
#             return False
            
#     return True

# def clean_emails(emails_list):
#     """Normalize and filter valid emails from a list, removing duplicates."""
#     if not emails_list:
#         return "N/A", []
    
#     valid_emails = []
#     seen = set()
#     for e in emails_list:
#         if not e:
#             continue
#         cleaned = e.strip().lower()
#         if is_valid_email(cleaned) and cleaned not in seen:
#             seen.add(cleaned)
#             valid_emails.append(cleaned)
            
#     if not valid_emails:
#         return "N/A", []
        
#     primary = valid_emails[0]
#     secondary = valid_emails[1] if len(valid_emails) > 1 else "N/A"
#     return primary, secondary


import re

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$",
    re.IGNORECASE
)

# Technical / infrastructure domains
BLOCKED_EMAIL_DOMAINS = {
    "sentry-next.wixpress.com",
    "sentry.wixpress.com",
    "wixpress.com",
    "wix.com",
}

# Obvious placeholder emails
BLOCKED_EMAILS = {
    "user@domain.com",
    "example@example.com",
    "test@test.com",
    "test@example.com",
    "admin@example.com",
    "email@example.com",
    "name@email.com",
    "you@example.com",
    "your@email.com",
    "yourname@email.com",
    "someone@example.com",
    "john@doe.com",
    "johndoe@example.com",
    "info@example.com",
    "support@example.com",
    "noreply@example.com",
}

# Obvious non-email garbage
GARBAGE_PATTERNS = [
    r"\.png$",
    r"\.jpg$",
    r"\.jpeg$",
    r"\.gif$",
    r"\.css$",
    r"\.js$",
]


def is_valid_email(email: str) -> bool:
    """Validate an email that was actually extracted from a website."""

    if not isinstance(email, str):
        return False

    email = email.strip()

    if not email:
        return False

    # Reject list/string placeholders
    if email in {"[]", "{}", "None", "null", "N/A", "NA"}:
        return False

    # Basic email format
    if not EMAIL_REGEX.fullmatch(email):
        return False

    lower_email = email.lower()

    # Reject if it contains placeholder keyword
    if "placeholder" in lower_email:
        return False

    # Reject known placeholders
    if lower_email in BLOCKED_EMAILS:
        return False

    # Get domain
    try:
        username, domain = lower_email.rsplit("@", 1)
    except ValueError:
        return False

    # Reject placeholder/demo domains
    placeholder_domains = {
        "example.com",
        "example.net",
        "example.org",
        "placeholder.com",
        "sample.com",
        "temp.com",
        "dummy.com",
        "yourdomain.com",
        "mycompany.com",
    }
    if domain in placeholder_domains:
        return False

    # Reject Sentry.io emails
    if domain == "sentry.io" or lower_email.endswith("@sentry.io") or "@sentry.io" in lower_email:
        return False

    # Reject asset / file extensions
    asset_extensions = (".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".css", ".js")
    if lower_email.endswith(asset_extensions):
        return False

    # Reject technical domains
    if domain in BLOCKED_EMAIL_DOMAINS:
        return False

    # Reject obvious garbage
    for pattern in GARBAGE_PATTERNS:
        if re.search(pattern, lower_email):
            return False

    return True


def clean_emails(emails_list):
    """Clean, validate and deduplicate extracted website emails."""

    if not emails_list:
        return "N/A", "N/A"

    # Handle accidental single string
    if isinstance(emails_list, str):
        emails_list = [emails_list]

    valid_emails = []
    seen = set()

    for email in emails_list:

        if not isinstance(email, str):
            continue

        email = email.strip()

        if not is_valid_email(email):
            continue

        key = email.lower()

        if key in seen:
            continue

        seen.add(key)
        valid_emails.append(email)

    if not valid_emails:
        return "N/A", "N/A"

    primary = valid_emails[0]

    secondary = (
        valid_emails[1]
        if len(valid_emails) > 1
        else "N/A"
    )

    return primary, secondary