from urllib.parse import urlparse

def format_website(url: str) -> str:
    """Normalize and format a website URL. Returns 'N/A' if invalid."""
    if not url or str(url).strip().lower() in ("n/a", "na", ""):
        return "N/A"
    
    url = url.strip()
    
    # Avoid javascript: void(0) or anchors
    if url.startswith(("javascript:", "#")):
        return "N/A"
        
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
            
        parsed = urlparse(url)
        if not parsed.netloc:
            return "N/A"
        return url
    except Exception:
        return "N/A"
