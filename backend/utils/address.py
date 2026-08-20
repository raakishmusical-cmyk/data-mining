# import re
# from backend.utils.normalizer import clean_text

# def parse_address(address_str: str, default_city: str = "Hingoli", default_state: str = "Maharashtra", default_country: str = "India"):
#     """
#     Splits a raw address string into Street, City, State, Zip Code, and Country.
#     """
#     city = default_city
#     state = default_state
#     country = default_country
#     zipcode = "N/A"
    
#     if not address_str or str(address_str).strip().lower() in {"n/a", "na", ""}:
#         return "N/A", city, state, zipcode, country
        
#     # Standardize spaces and newlines
#     addr_clean = address_str.replace("\r\n", ", ").replace("\r", ", ").replace("\n", ", ")
#     addr_clean = re.sub(r"\t+", " ", addr_clean)
#     addr_clean = re.sub(r"[ ]+", " ", addr_clean).strip()
    
#     if addr_clean.lower().startswith("address:"):
#         addr_clean = addr_clean[8:].strip()
        
#     # Match standard 6-digit postal codes (India PIN codes) or generic 5/9 digit zip codes
#     zip_match = re.search(r"\b(\d{6})\b", addr_clean)
#     if not zip_match:
#         zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", addr_clean)
        
#     if zip_match:
#         zipcode = zip_match.group(1)
#         addr_clean = addr_clean[:zip_match.start()] + addr_clean[zip_match.end():]
        
#     # Extract country if explicitly present
#     if "india" in addr_clean.lower():
#         country = "India"
#         addr_clean = re.sub(r"\bIndia\b", "", addr_clean, flags=re.IGNORECASE)
#     elif "united states" in addr_clean.lower() or "usa" in addr_clean.lower():
#         country = "USA"
#         addr_clean = re.sub(r"\b(United States|USA)\b", "", addr_clean, flags=re.IGNORECASE)
        
#     # Try to parse state and city
#     # Strip state from the address
#     state_match = re.search(r"\b(Maharashtra|Goa|Gujarat|Karnataka|Tamil\s*Nadu|Delhi)\b", addr_clean, flags=re.IGNORECASE)
#     if state_match:
#         state = state_match.group(1).title()
#         addr_clean = addr_clean[:state_match.start()] + addr_clean[state_match.end():]
        
#     # Clean the remaining street text
#     street = clean_text(addr_clean)
    
#     # If street ends up empty, mark as N/A
#     if not street or street.strip() in ("", " "):
#         street = "N/A"
        
#     return street, city, state, zipcode, country



import re
from backend.utils.normalizer import clean_text


# All Indian States & Union Territories
INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi",
    "Chandigarh",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
    "Andaman and Nicobar Islands",
    "Dadra and Nagar Haveli and Daman and Diu",
]

USA_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", 
    "Wisconsin", "Wyoming", "District of Columbia"
]



ALL_STATES = INDIAN_STATES + USA_STATES 

STATE_PATTERN = "|".join(
    sorted(
        [re.escape(state).replace(r"\ ", r"\s*") for state in ALL_STATES],
        key=len,
        reverse=True,
    )
)


def parse_address(
    address_str: str,
    default_city: str = "N/A",
    default_state: str = "N/A",
    default_country: str = "N/A",
):
    """
    Splits a raw address into:
        Street, City, State, Zipcode, Country
    """

    city = default_city
    state = default_state
    country = default_country
    zipcode = "N/A"

    if not address_str or str(address_str).strip().lower() in {"", "na", "n/a", "none"}:
        return "N/A", city, state, zipcode, country

    # Normalize whitespace
    addr_clean = address_str.replace("\r\n", ", ").replace("\r", ", ").replace("\n", ", ")
    addr_clean = re.sub(r"\t+", " ", addr_clean)
    addr_clean = re.sub(r"\s+", " ", addr_clean).strip()

    if addr_clean.lower().startswith("address:"):
        addr_clean = addr_clean[8:].strip()

    # ---------------- ZIP CODE ---------------- #

    zip_match = re.search(r"\b\d{6}\b", addr_clean)

    if not zip_match:
        zip_match = re.search(r"\b\d{5}(?:-\d{4})?\b", addr_clean)

    if zip_match:
        zipcode = zip_match.group()
        addr_clean = addr_clean.replace(zipcode, "")

    # ---------------- COUNTRY ---------------- #

    if re.search(r"\bIndia\b", addr_clean, re.IGNORECASE):
        country = "India"
        addr_clean = re.sub(r"\bIndia\b", "", addr_clean, flags=re.IGNORECASE)

    elif re.search(r"\bUSA\b|\bUnited States\b|\bUnited States of America\b", addr_clean, re.IGNORECASE):
        country = "USA"
        addr_clean = re.sub(
            r"\bUSA\b|\bUnited States\b|\bUnited States of America\b",
            "",
            addr_clean,
            flags=re.IGNORECASE,
        )



    # ---------------- STATE ---------------- #

    state_match = re.search(
        rf"\b({STATE_PATTERN})\b",
        addr_clean,
        flags=re.IGNORECASE,
    )

    if state_match:
        state = state_match.group(1).title()
        addr_clean = addr_clean.replace(state_match.group(0), "")

    # ---------------- CITY ---------------- #

    parts = [p.strip() for p in addr_clean.split(",") if p.strip()]

    if len(parts) >= 2:
        city = clean_text(parts[-1])
        parts = parts[:-1]

    # ---------------- STREET ---------------- #

    street = clean_text(", ".join(parts))

    if not street:
        street = "N/A"

    return (
        street,
        city,
        state,
        zipcode,
        country,
    )