import asyncio
import os
import re
import time
import csv
import phonenumbers
from playwright.async_api import async_playwright
from urllib.parse import urlparse, quote

# ---------------- CONFIG ----------------
# FILE_NAME = r"C:\Users\trupt\OneDrive\Desktop\Pune_Leads.csv"
FILE_NAME = "Output/Mumbai City_Leads.csv"
# FILE_NAME = "Output/Erode_Leads.csv"

LOCATIONS = ["Mumbai City district,Maharashtra, India"]

KEYWORDS = [
    "Sports Shop",
    "Sports Store",
    "Sporting Goods Store",
    "Gym",
    "Fitness Center",
    "Yoga Studio",
    "School",
    "College",
    "University",
    "Sports Academy",
    "Sports Club",
    "Stadium",
    "Playground",
    "Indoor Sports Complex",
]

# ---------------- PERFORMANCE SETTINGS ----------------
HEADLESS = True
SCRAPE_WEBSITES = True
SEARCH_TIMEOUT = 20000
WEBSITE_TIMEOUT = 10000
INITIAL_WAIT = 1.5
SCROLL_WAIT = 1.5
CLICK_WAIT = 1.5
DEFAULT_REGION = "IN"

HEADERS = [
    "Organization Name",
    "Salutation",
    "First Name",
    "Last Name",
    "Title",
    "Email",
    "Secondary Email",
    "Phone",
    "Mobile",
    "Fax",
    "Skype ID",
    "Website",
    "Instagram",
    "Facebook",
    "LinkedIn",
    "Twitter",
    "YouTube",
    "Street",
    "City",
    "State",
    "Zip Code",
    "Country",
    "Industry",
    "Tags",
]

CSV_DELIMITER = ","
seen_keys = set()


# ---------------- CLEAN ----------------
def clean_text(x):
    if not x:
        return "N/A"
    x = str(x)
    x = re.sub(r"[\uE000-\uF8FF]", " ", x)  # private-use icons
    x = re.sub(r"[\u200B-\u200F\uFEFF]", "", x)  # zero-width chars
    # x = re.sub(r"\b[A-Za-z0-9]{2,4}\+[A-Za-z0-9]{2,4}\b", " ", x)
    x = re.sub(r"\s+", " ", x)
    x = x.replace('"', "").replace(",", " ")
    return x.strip()


def normalize(x):
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


def clean_phone(x):
    return re.sub(r"\D", "", x or "")


def split_phone_and_mobile(raw_number, default_region=DEFAULT_REGION):
    if not raw_number or str(raw_number).strip().lower() in {"n/a", "na"}:
        return "N/A", "N/A"

    cleaned = str(raw_number).strip()
    cleaned = (
        cleaned.replace("Phone:", "")
        .replace("Mobile:", "")
        .replace("Tel:", "")
        .replace("Call:", "")
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return "N/A", "N/A"

    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) == 10:
        if digits[0] in "6789":
            return "N/A", f"+91{digits}"
        return digits, "N/A"

    try:
        parsed = phonenumbers.parse(cleaned, default_region)
        if phonenumbers.is_valid_number(parsed):
            if phonenumbers.number_type(parsed) == phonenumbers.PhoneNumberType.MOBILE:
                formatted = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                return "N/A", formatted

            formatted = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            )
            return formatted, "N/A"
    except phonenumbers.NumberParseException:
        pass

    return "N/A", "N/A"


def clean_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        return domain
    except:
        return ""


def generate_unique_key(name, phone, website, city):
    phone_clean = clean_phone(phone)
    domain = clean_domain(website)
    if phone_clean:
        return f"PHONE_{phone_clean}"
    if domain:
        return f"WEB_{domain}"
    return f"NAMECITY_{normalize(name)}_{normalize(city)}"


# ---------------- FIXED ADDRESS SPLITTER ----------------
def split_address(addr, default_city):
    parts = [p.strip() for p in (default_city or "").split(",")]
    city = parts[0] if parts else "Pune"
    state = parts[1] if len(parts) > 1 else "Maharashtra"
    country = parts[2] if len(parts) > 2 else "India"
    zipcode = "N/A"

    if not addr or addr == "N/A" or len(addr.strip()) < 5:
        return "N/A", city, state, zipcode, country

    # Initially convert newlines to commas for temporary token isolation
    addr_clean = addr.replace("\r\n", ", ").replace("\r", ", ").replace("\n", ", ")
    addr_clean = re.sub(r"\t+", " ", addr_clean)
    addr_clean = re.sub(r"[ ]+", " ", addr_clean).strip()

    if addr_clean.lower().startswith("address:"):
        addr_clean = addr_clean[8:].strip()

    # Match 6-digit PIN code anywhere in address
    zip_match = re.search(r"\b(\d{6})\b", addr_clean)
    if zip_match:
        zipcode = zip_match.group(1)
        addr_clean = addr_clean[: zip_match.start()] + addr_clean[zip_match.end() :]

    # Drop structural tags to clean the Street field
    for token in ["Maharashtra", "India", "Pune"]:
        pattern = r"(?<![A-Za-z])" + re.escape(token) + r"(?![A-Za-z])"
        addr_clean = re.sub(pattern, "", addr_clean, flags=re.IGNORECASE)

    # Convert all commas to spaces so Excel can NEVER shift columns
    addr_clean = addr_clean.replace('"', "").replace(",", " ")
    addr_clean = re.sub(r"\s+", " ", addr_clean).strip()

    street = addr_clean if addr_clean else "N/A"
    return street, city, state, zipcode, country


# ---------------- CSV HANDLING ----------------
def init_csv():
    # Make sure target folder exists
    os.makedirs(os.path.dirname(FILE_NAME), exist_ok=True)

    # If file exists but has no headers or is empty, overwrite it fresh
    should_write_header = True
    if os.path.exists(FILE_NAME) and os.path.getsize(FILE_NAME) > 0:
        try:
            with open(FILE_NAME, "r", encoding="utf-8-sig") as f:
                first_line = f.readline()
                if "Organization Name" in first_line:
                    should_write_header = False
        except:
            pass

    if should_write_header:
        with open(FILE_NAME, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f, delimiter=CSV_DELIMITER, quoting=csv.QUOTE_MINIMAL).writerow(
                HEADERS
            )


def save_row(row):
    while True:
        try:
            with open(FILE_NAME, "a", newline="", encoding="utf-8-sig") as f:
                csv.writer(
                    f, delimiter=CSV_DELIMITER, quoting=csv.QUOTE_MINIMAL
                ).writerow(row)
            print("Saved:", row[0])
            break
        except PermissionError:
            print("CSV file open in Excel? Waiting 2 seconds to retry...")
            time.sleep(2)


# ---------------- SOCIAL SCRAPER ----------------
async def scrape_site(page, url):
    result = {
        "Email": "N/A",
        "Instagram": "N/A",
        "Facebook": "N/A",
        "LinkedIn": "N/A",
        "Twitter": "N/A",
        "YouTube": "N/A",
    }
    try:
        await page.goto(url, timeout=WEBSITE_TIMEOUT, wait_until="domcontentloaded")
        await asyncio.sleep(1)
        html = await page.content()
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)
        if emails:
            result["Email"] = emails[0]

        links = await page.eval_on_selector_all("a", "els => els.map(e => e.href)")
        for link in links:
            if not link:
                continue
            l = link.lower()
            if "facebook.com" in l:
                result["Facebook"] = link
            elif "instagram.com" in l:
                result["Instagram"] = link
            elif "linkedin.com" in l:
                result["LinkedIn"] = link
            elif "twitter.com" in l or "x.com" in l:
                result["Twitter"] = link
            elif "youtube.com" in l:
                result["YouTube"] = link
    except:
        pass
    return result


# ---------------- TRANSLATE ----------------
async def translate_to_english(page, text):
    url = (
        "https://translate.google.com/?sl=auto&tl=en&text="
        + quote(text)
        + "&op=translate"
    )
    await page.goto(url, timeout=15000, wait_until="domcontentloaded")
    await page.wait_for_selector("span[jsname='W297wb']", timeout=15000)
    return await page.locator("span[jsname='W297wb']").text_content()


# ---------------- MAIN ----------------
async def run():
    init_csv()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()
        website_page = await browser.new_page() if SCRAPE_WEBSITES else None
        translator_page = await browser.new_page()

        for loc in LOCATIONS:
            for kw in KEYWORDS:
                print(f"\nSearching: {kw} in {loc}")
                try:
                    await page.goto(
                        f"https://www.google.com/maps/search/{kw}+in+{loc}",
                        timeout=SEARCH_TIMEOUT,
                        wait_until="domcontentloaded",
                    )
                    await page.wait_for_selector(
                        'div[role="feed"]', timeout=SEARCH_TIMEOUT
                    )
                    await asyncio.sleep(INITIAL_WAIT)
                except:
                    continue

                scroll = page.locator('div[role="feed"]')
                if not await scroll.count():
                    continue

                prev = 0
                no_change_streak = 0
                while True:
                    await scroll.evaluate("el => el.scrollTop += 5000")
                    await asyncio.sleep(SCROLL_WAIT)

                    end_reached = await page.locator(
                        "span.HlvSq, p.fontBodyMedium span[jslog], div.PbZDve p"
                    ).count()

                    curr = await page.locator("a.hfpxzc").count()

                    if curr == prev:
                        no_change_streak += 1
                        if no_change_streak >= 3 or end_reached:
                            break
                        await asyncio.sleep(3)
                    else:
                        no_change_streak = 0
                        prev = curr

                    if no_change_streak == 1:
                        await scroll.evaluate("el => el.scrollTop -= 500")
                        await asyncio.sleep(1)
                        await scroll.evaluate("el => el.scrollTop += 5500")
                        await asyncio.sleep(3)

                total = await page.locator("a.hfpxzc").count()
                print(f"Total Found (capped): {total}")

                for i in range(total):
                    try:
                        item = page.locator("a.hfpxzc").nth(i)
                        raw_name = await item.get_attribute("aria-label")
                        name = clean_text(raw_name or "")

                        if name:
                            try:
                                name = clean_text(
                                    await translate_to_english(translator_page, name)
                                )
                            except Exception:
                                pass

                        await item.click()

                        try:
                            await page.wait_for_selector(
                                f'h1:has-text("{name}")', timeout=3000
                            )
                        except:
                            pass
                        await asyncio.sleep(4.0)

                        phone = "N/A"
                        mobile = "N/A"
                        raw_phone = ""

                        if await page.locator('button[aria-label^="Phone"]').count():
                            raw_phone = await page.locator(
                                'button[aria-label^="Phone"]'
                            ).first.get_attribute("aria-label")
                            phone, mobile = split_phone_and_mobile(raw_phone)

                        print("Phone:", phone)
                        print("Mobile:", mobile)

                        website = "N/A"
                        if await page.locator('a[data-item-id="authority"]').count():
                            website = await page.locator(
                                'a[data-item-id="authority"]'
                            ).first.get_attribute("href")

                        if await page.locator('button[data-item-id="address"]').count():
                            raw_address = await page.locator(
                                'button[data-item-id="address"]'
                            ).first.text_content()
                            raw_address = clean_text(raw_address)
                            print("ADDRESS:", repr(raw_address))
                            if raw_address:
                                try:
                                    address = await translate_to_english(
                                        translator_page, raw_address
                                    )
                                    address = address or raw_address
                                except Exception:
                                    address = raw_address
                            else:
                                address = "N/A"

                        street, city, state, zip_code, country = split_address(
                            address, loc
                        )

                        key = generate_unique_key(name, phone, website, city)
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)

                        extra = {
                            "Email": "N/A",
                            "Instagram": "N/A",
                            "Facebook": "N/A",
                            "LinkedIn": "N/A",
                            "Twitter": "N/A",
                            "YouTube": "N/A",
                        }

                        if (
                            website
                            and website.startswith("http")
                            and SCRAPE_WEBSITES
                            and website_page
                        ):
                            extra = await scrape_site(website_page, website)

                        row = [
                            name,  # Organization Name
                            "N/A",  # Salutation
                            "N/A",  # First Name
                            "N/A",  # Last Name
                            "N/A",  # Title
                            extra["Email"],  # Email
                            "N/A",  # Secondary Email
                            phone,  # Phone
                            mobile,  # Mobile
                            "N/A",  # Fax
                            "N/A",  # Skype ID
                            website,  # Website
                            extra["Instagram"],  # Instagram
                            extra["Facebook"],  # Facebook
                            extra["LinkedIn"],  # LinkedIn
                            extra["Twitter"],  # Twitter
                            extra["YouTube"],  # YouTube
                            street,  # Street
                            city,  # City
                            state,  # State
                            zip_code,  # Zip Code
                            country,  # Country
                            kw,  # Industry
                            "Sports Lead",  # Tags
                        ]

                        # Completely clean data across all columns right before writing
                        cleaned_row = []
                        for idx, val in enumerate(row):
                            cleaned_row.append(clean_text(str(val)))

                        save_row(cleaned_row)

                    except Exception as e:
                        print("Skip Element Error:", e)

        await browser.close()
    print("\nProcess completed successfully.")


if __name__ == "__main__":
    asyncio.run(run())
