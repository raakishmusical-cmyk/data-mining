# Mapping dictionary from Industry to Lead Tag
INDUSTRY_TO_TAG = {
    # Sports & Fitness leads
    "Sporting Goods Store": "Sports Lead",
    "Sports Shop": "Sports Lead",
    "Cricket Shop": "Sports Lead",
    "Badminton Shop": "Sports Lead",
    "Sportswear Store": "Sports Lead",
    "Fitness Equipment Store": "Sports Lead",
    "Sports Academy": "Sports Lead",
    "Sports Club": "Sports Lead",
    "Stadium": "Sports Lead",
    "Playground": "Sports Lead",
    "Indoor Sports Complex": "Sports Lead",
    
    "Gym": "Fitness Lead",
    "Fitness Center": "Fitness Lead",
    "Fitness Centre": "Fitness Lead",
    "Health Club": "Fitness Lead",
    "Yoga Studio": "Fitness Lead",
    
    # Education leads
    "School": "Education Lead",
    "Higher Secondary School": "Education Lead",
    "CBSE School": "Education Lead",
    "Matriculation School": "Education Lead",
    "College": "Education Lead",
    "Engineering College": "Education Lead",
    "Arts College": "Education Lead",
    "Medical College": "Education Lead",
    "University": "Education Lead",
    
    # Hospitality / Holiday leads
    "Hotel": "Hotel Lead",
    "Resort": "Hotel Lead",
    "Lodge": "Hotel Lead",
    
    # Healthcare leads
    "Clinic": "Healthcare Lead",
    "Hospital": "Hospital Lead",
    "Medical Center": "Healthcare Lead",
    "Medical Centre": "Healthcare Lead",
    
    # Food leads
    "Restaurant": "Restaurant Lead",
    "Cafe": "Restaurant Lead",
    
    # Medical Shop / Pharmacy leads
    "Medical Shop": "Medical Lead",
    "Pharmacy": "Medical Lead",
    
    # Automobile leads
    "Car Dealer": "Automobile Lead",
    "Automobile": "Automobile Lead"
}

def determine_tag(industry: str) -> str:
    """
    Maps standard industry to a specific lead tag.
    Always returns 'Sports Lead' per requirements.
    """
    return "Sports Lead"
