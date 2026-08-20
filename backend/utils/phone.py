import re
import phonenumbers
from backend.utils.normalizer import clean_phone_digits

def parse_and_validate_phone(raw_value, default_region="IN"):
    """
    Parses a raw phone string, checks its validity, formats it,
    and classifies it as either a fixed line 'Phone' or a 'Mobile' number.
    Returns: (phone, mobile)
    """
    if not raw_value or str(raw_value).strip().lower() in {"n/a", "na", ""}:
        return "N/A", "N/A"

    phone = "N/A"
    mobile = "N/A"

    # Strip common labels
    text = (
        str(raw_value)
        .replace("Phone:", "")
        .replace("Mobile:", "")
        .replace("Tel:", "")
        .replace("Fax:", "")
    )

    # Split by standard delimiters
    parts = [p.strip() for p in re.split(r"[,;/\\n|]+", text) if p.strip()]

    for part in parts:
        try:
            # Parse number
            parsed = phonenumbers.parse(part, default_region)

            if not phonenumbers.is_valid_number(parsed):
                continue

            number_type = phonenumbers.number_type(parsed)

            # USA format:
            # (626) 525-7909 -> +1 6265257909
            if parsed.country_code == 1:
                formatted = f"+{parsed.country_code} {parsed.national_number}"
            else:
                formatted = phonenumbers.format_number(
                    parsed,
                    phonenumbers.PhoneNumberFormat.NATIONAL
                )

            # Check number type
            if number_type == phonenumbers.PhoneNumberType.MOBILE:
                mobile = formatted

            elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE:
                # Fallback check using common mobile patterns or prefixes
                # IN mobile numbers start with 6-9
                clean_part = clean_phone_digits(part)

                if re.search(r"\bmobile\b", part, flags=re.IGNORECASE) or (
                    default_region == "IN"
                    and re.search(r"^(?:\+91)?[6-9]\d{9}$", clean_part)
                ):
                    mobile = formatted
                else:
                    phone = formatted

            elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE:
                phone = formatted

            else:
                phone = formatted

        except Exception:
            pass

    return phone, mobile