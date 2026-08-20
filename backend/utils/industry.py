from rapidfuzz import process, fuzz

# Dictionary of raw category/keywords to normalized Standard Industries
STANDARD_INDUSTRIES = {
    # Sports & Fitness
    "sports shop": "Sporting Goods Store",
    "sports store": "Sporting Goods Store",
    "sporting goods store": "Sporting Goods Store",
    "cricket shop": "Cricket Shop",
    "badminton shop": "Badminton Shop",
    "sportswear store": "Sportswear Store",
    "fitness equipment store": "Fitness Equipment Store",
    "gym": "Gym",
    "fitness center": "Fitness Center",
    "fitness centre": "Fitness Center",
    "health club": "Health Club",
    "yoga studio": "Yoga Studio",
    "sports academy": "Sports Academy",
    "sports club": "Sports Club",
    "stadium": "Stadium",
    "playground": "Playground",
    "indoor sports complex": "Indoor Sports Complex",
    
    # Education
    "school": "School",
    "higher secondary school": "Higher Secondary School",
    "cbse school": "CBSE School",
    "matriculation school": "Matriculation School",
    "college": "College",
    "engineering college": "Engineering College",
    "arts college": "Arts College",
    "medical college": "Medical College",
    "university": "University",
    
    # Hospitality / Travel
    "hotel": "Hotel",
    "resort": "Resort",
    "lodge": "Lodge",
    
    # Healthcare
    "clinic": "Clinic",
    "hospital": "Hospital",
    "medical center": "Medical Center",
    "medical centre": "Medical Center",
    
    # Food
    "restaurant": "Restaurant",
    "cafe": "Cafe",
    "diner": "Restaurant"
}

def determine_industry(gmaps_category: str, business_name: str, search_keyword: str) -> str:
    """
    Determines standard industry based on category, business name, and keyword.
    Always returns the search keyword directly per requirements.
    """
    return search_keyword
