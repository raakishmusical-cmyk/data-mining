import re
from urllib.parse import urlparse

def is_valid_val(val) -> bool:
    if not val:
        return False
    val_clean = str(val).strip().lower()
    return val_clean not in (
        "", "n/a", "na", "nan", "none", "null", "unknown", "publicly unavailable", "-", "--"
    )

def normalize_phone(phone_val) -> str:
    if not phone_val:
        return ""
    if not is_valid_val(phone_val):
        return ""
    val = str(phone_val).strip()
    
    # 1. Lowercase just in case of letters
    val = val.lower()
    
    # 2. Strip spaces, hyphens, parentheses, and other non-digits except '+'
    cleaned = re.sub(r"[^0-9+]", "", val)
    
    # 3. Strip Country Code +91 or 91
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) > 10:
        cleaned = cleaned[2:]
        
    # 4. Remove all non-digits (including any + signs that might be left)
    cleaned = re.sub(r"\D", "", cleaned)
    
    # 5. Strip Leading Zeros
    cleaned = cleaned.lstrip("0")
    
    return cleaned

def normalize_email(email_val) -> str:
    if not email_val:
        return ""
    if not is_valid_val(email_val):
        return ""
    return str(email_val).strip().lower()

def normalize_website(web_val) -> str:
    if not web_val:
        return ""
    if not is_valid_val(web_val):
        return ""
    val = str(web_val).strip().lower()
    # Strip protocol prefix
    if val.startswith("https://"):
        val = val[8:]
    elif val.startswith("http://"):
        val = val[7:]
    # Strip www prefix
    if val.startswith("www."):
        val = val[4:]
    # Strip trailing slash
    if val.endswith("/"):
        val = val[:-1]
    return val

def clean_text(x):
    if not x:
        return "N/A"
    x = str(x)
    # Remove private-use unicode characters and zero-width characters
    x = re.sub(r"[\uE000-\uF8FF]", " ", x)
    x = re.sub(r"[\u200B-\u200F\uFEFF]", "", x)
    # Normalize spaces
    x = re.sub(r"\s+", " ", x)
    # Replace characters that disrupt CSV layout
    x = x.replace('"', "").replace(",", " ")
    return x.strip()

def normalize_string(x):
    """Normalized lowercase alphanumerics only, for strict duplicate comparison."""
    if not x:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(x).lower())

def clean_phone_digits(x):
    """Strip all non-digit characters."""
    if not x:
        return ""
    return re.sub(r"\D", "", str(x))

def extract_domain(url):
    """Extract domain name without www. prefix."""
    if not url or url.lower() in ("n/a", "na", ""):
        return ""
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""

def validate_business_record(name: str, address: str, phone: str, mobile: str) -> tuple[bool, str]:
    """
    Validates business records according to strict requirements:
    Mandatory Fields: Business Name, Address, and at least one contact number (Phone OR Mobile).
    Returns (is_valid, reason_message)
    """
    def is_valid_val(val) -> bool:
        if val is None:
            return False
        val_clean = str(val).strip().upper()
        return val_clean not in (
            "", "N/A", "NA", "NONE", "NULL", "-", "--", "UNKNOWN", "NOT AVAILABLE", "PUBLICLY UNAVAILABLE"
        )

    def is_valid_phone_or_mobile(val) -> bool:
        if not is_valid_val(val):
            return False
        digits = re.sub(r"\D", "", str(val))
        return len(digits) > 0

    has_name = is_valid_val(name)
    has_address = is_valid_val(address)
    has_phone = is_valid_phone_or_mobile(phone)
    has_mobile = is_valid_phone_or_mobile(mobile)

    has_contact = has_phone or has_mobile
    is_valid = has_name and has_address and has_contact

    reason_msg = ""
    if not is_valid:
        name_ind = "✓" if has_name else "✗"
        addr_ind = "✓" if has_address else "✗"
        phone_ind = "✓" if has_phone else "✗"
        mobile_ind = "✓" if has_mobile else "✗"

        # Format business name cleanly for display in the log
        display_name = str(name).strip() if name else "Unknown Business"
        if display_name.upper() in ("", "N/A", "NA", "NONE", "NULL", "-", "--", "UNKNOWN", "NOT AVAILABLE", "PUBLICLY UNAVAILABLE"):
            display_name = "Unknown Business"

        reason_msg = (
            f"Skipping \"{display_name}\"\n"
            f"Reason:\n"
            f"Missing mandatory field(s)\n\n"
            f"Name: {name_ind}\n"
            f"Address: {addr_ind}\n"
            f"Phone: {phone_ind}\n"
            f"Mobile: {mobile_ind}"
        )

    return is_valid, reason_msg

import asyncio

class DuplicateDetector:
    def __init__(self):
        self.lock = asyncio.Lock()
        self._seen_businesses = []
        
        # Audit statistics
        self.total_duplicates = 0
        self.duplicates_by_place_id = 0
        self.duplicates_by_name_address = 0
        self.rejected_by_phone = 0
        self.rejected_by_website = 0
        self.rejected_by_email = 0
        self.rejected_by_mobile = 0

    @property
    def seen_businesses(self):
        return self._seen_businesses

    @seen_businesses.setter
    def seen_businesses(self, value):
        self._seen_businesses = value
        for idx, item in enumerate(self._seen_businesses):
            if "row_index" not in item:
                item["row_index"] = idx + 1


    def check_duplicate(self, incoming: dict) -> tuple[bool, str, dict]:
        """
        Non-locking duplicate check. Returns (is_duplicate, reason_message, existing_record).
        Checks in priority order using if/elif to only compare the highest priority
        identifier that exists.
        """
        inc_phone = normalize_phone(incoming.get("phone"))
        inc_mobile = normalize_phone(incoming.get("mobile"))
        inc_email = normalize_email(incoming.get("email"))
        inc_website = normalize_website(incoming.get("website"))
        
        # If there is no contact identifier, we must save it (it cannot be a duplicate)
        if not (inc_phone or inc_mobile or inc_email or inc_website):
            return False, "", None
            
        if inc_phone:
            # Compare Phone only
            # Defensive validation: if phone is N/A or empty, it can never trigger a Phone Duplicate
            if not is_valid_val(incoming.get("phone")) or inc_phone == "":
                return False, "", None
            for existing in self.seen_businesses:
                ext_phone = normalize_phone(existing.get("phone"))
                if ext_phone and ext_phone == inc_phone:
                    self.rejected_by_phone += 1
                    return True, "Phone Duplicate", existing
                    
        elif inc_mobile:
            # Compare Mobile only
            # Defensive validation: if mobile is N/A or empty, it can never trigger a Mobile Duplicate
            if not is_valid_val(incoming.get("mobile")) or inc_mobile == "":
                return False, "", None
            for existing in self.seen_businesses:
                ext_mobile = normalize_phone(existing.get("mobile"))
                if ext_mobile and ext_mobile == inc_mobile:
                    self.rejected_by_mobile += 1
                    return True, "Mobile Duplicate", existing
                    
        elif inc_email:
            # Compare Email only
            # Defensive validation: if email is N/A or empty, it can never trigger an Email Duplicate
            if not is_valid_val(incoming.get("email")) or inc_email == "":
                return False, "", None
            for existing in self.seen_businesses:
                ext_email = normalize_email(existing.get("email"))
                if ext_email and ext_email == inc_email:
                    self.rejected_by_email += 1
                    return True, "Email Duplicate", existing
                    
        elif inc_website:
            # Compare Website only
            # Defensive validation: if website is N/A or empty, it can never trigger a Website Duplicate
            if not is_valid_val(incoming.get("website")) or inc_website == "":
                return False, "", None
            for existing in self.seen_businesses:
                ext_website = normalize_website(existing.get("website"))
                if ext_website and ext_website == inc_website:
                    self.rejected_by_website += 1
                    return True, "Website Duplicate", existing
                    
        return False, "", None

    async def add_and_check(self, incoming: dict) -> tuple[bool, str, dict]:
        """
        Thread/async-safe duplicate check and save.
        If it's not a duplicate, it saves the record details to self.seen_businesses.
        Returns (is_duplicate, reason_message, existing_record).
        """
        async with self.lock:
            is_dup, reason, matched_existing = self.check_duplicate(incoming)
            if is_dup:
                self.total_duplicates += 1
                # If total duplicates >= 10, check if 95% of duplicates are Mobile Duplicates
                if self.total_duplicates >= 10:
                    pct_mobile = (self.rejected_by_mobile / self.total_duplicates) * 100
                    if pct_mobile >= 95.0:
                        from backend.utils.logger import logger
                        logger.warning(
                            f"\n"
                            f"================================================\n"
                            f"WARNING: Potential Extraction or State-Reset Bug!\n"
                            f"Mobile duplicates make up {pct_mobile:.1f}% of all duplicates "
                            f"({self.rejected_by_mobile}/{self.total_duplicates}).\n"
                            f"Verify that Mobile values are not being leaked or reused.\n"
                            f"================================================\n"
                        )
            else:
                new_record = {
                    "row_index": len(self._seen_businesses) + 1,
                    "name": incoming.get("name") or "",
                    "address": incoming.get("address") or "",
                    "place_id": incoming.get("place_id") or "",
                    "phone": incoming.get("phone") or "",
                    "mobile": incoming.get("mobile") or "",
                    "website": incoming.get("website") or "",
                    "email": incoming.get("email") or ""
                }
                self._seen_businesses.append(new_record)
                matched_existing = new_record
            return is_dup, reason, matched_existing


    async def update_email(self, name: str, address: str, place_id: str, email: str, row_index: int = None, phone: str = None, mobile: str = None, website: str = None):
        async with self.lock:
            # 1. Look up by stable internal record reference
            if row_index is not None:
                for existing in self._seen_businesses:
                    if existing.get("row_index") == row_index:
                        existing["email"] = email
                        return

            # 2. Look up by Place ID
            if place_id and place_id.upper() not in ("", "N/A", "NA", "NONE", "NULL", "UNKNOWN"):
                for existing in self._seen_businesses:
                    if existing.get("place_id") == place_id:
                        existing["email"] = email
                        return

            # 3. Look up by unique contact identifiers (Phone / Mobile / Website)
            norm_ph = normalize_phone(phone) if phone else ""
            norm_mob = normalize_phone(mobile) if mobile else ""
            norm_web = normalize_website(website) if website else ""
            
            if norm_ph or norm_mob or norm_web:
                for existing in self._seen_businesses:
                    if norm_ph and normalize_phone(existing.get("phone")) == norm_ph:
                        existing["email"] = email
                        return
                    if norm_mob and normalize_phone(existing.get("mobile")) == norm_mob:
                        existing["email"] = email
                        return
                    if norm_web and normalize_website(existing.get("website")) == norm_web:
                        existing["email"] = email
                        return


    def generate_duplicate_report(self) -> str:
        return f"""========================================
DUPLICATE AUDIT REPORT
========================================
Total duplicates: {self.total_duplicates}

----------------------------------------
REJECTED CONTACT-ONLY MATCHES (AUDIT)
----------------------------------------
Duplicates rejected because of Phone: {self.rejected_by_phone}
Duplicates rejected because of Mobile: {self.rejected_by_mobile}
Duplicates rejected because of Email: {self.rejected_by_email}
Duplicates rejected because of Website: {self.rejected_by_website}
========================================
"""


def format_duplicate_log(incoming: dict, existing: dict, reason: str) -> str:
    # Determine type and value
    dup_type = "Unknown"
    dup_value = "N/A"
    if "Phone" in reason:
        dup_type = "Phone"
        dup_value = normalize_phone(incoming.get("phone"))
    elif "Mobile" in reason:
        dup_type = "Mobile"
        dup_value = normalize_phone(incoming.get("mobile"))
    elif "Email" in reason:
        dup_type = "Email"
        dup_value = normalize_email(incoming.get("email"))
    elif "Website" in reason:
        dup_type = "Website"
        dup_value = normalize_website(incoming.get("website"))

    return f"""==============================
DUPLICATE DETECTED
==============================

Incoming

Name:
{incoming.get('name') or 'N/A'}

Address:
{incoming.get('address') or 'N/A'}

Phone:
{incoming.get('phone') or 'N/A'}

Mobile:
{incoming.get('mobile') or 'N/A'}

Email:
{incoming.get('email') or 'N/A'}

Website:
{incoming.get('website') or 'N/A'}

-------------------------

Existing

Name:
{existing.get('name') or 'N/A'}

Address:
{existing.get('address') or 'N/A'}

Phone:
{existing.get('phone') or 'N/A'}

Mobile:
{existing.get('mobile') or 'N/A'}

Email:
{existing.get('email') or 'N/A'}

Website:
{existing.get('website') or 'N/A'}

-------------------------

Reason:
{reason}

Duplicate Type:
{dup_type}

Duplicate Value:
{dup_value}

Matched Existing Row:
{existing.get('row_index') or 'N/A'}

Matched Existing Business:
{existing.get('name') or 'N/A'}

=============================="""
