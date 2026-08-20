import asyncio
import re
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from backend.utils.logger import logger
from backend.utils.email import clean_emails
from backend.utils.normalizer import extract_domain

class WebsiteWorker:
    def __init__(self, timeout_ms: int = 10000):
        self.timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000.0)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        
    async def scrape_website(self, url: str) -> dict:
        """
        Crawls a website (Home, Contact, About) and extracts emails and socials.
        Returns extra fields: Email, Secondary Email, Instagram, Facebook, LinkedIn, Twitter, YouTube.
        """
        result = {
            "Email": "N/A",
            "Secondary Email": "N/A",
            "Instagram": "N/A",
            "Facebook": "N/A",
            "LinkedIn": "N/A",
            "Twitter": "N/A",
            "YouTube": "N/A"
        }
        
        if not url or url.lower() in ("n/a", "na", ""):
            return result
            
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
            
        crawled_urls = set()
        emails_found = []
        
        async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
            # 1. Scrape Homepage
            home_html = await self._fetch_page(session, url, crawled_urls)
            if not home_html:
                return result
                
            self._parse_page_content(home_html, url, emails_found, result)
            
            # Find Contact & About links to crawl
            links_to_crawl = self._find_subpage_links(home_html, url)
            
            # Limit to 2 additional pages (Contact, About)
            for sub_url in list(links_to_crawl)[:2]:
                if sub_url not in crawled_urls:
                    sub_html = await self._fetch_page(session, sub_url, crawled_urls)
                    if sub_html:
                        self._parse_page_content(sub_html, sub_url, emails_found, result)
                        
        # Final Email Cleanup and splitting
        primary_email, secondary_email = clean_emails(emails_found)
        result["Email"] = primary_email
        result["Secondary Email"] = secondary_email
        
        return result

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str, crawled_set: set) -> str:
        try:
            crawled_set.add(url)
            async with session.get(url, allow_redirects=True, ssl=False) as response:
                if response.status == 200:
                    return await response.text(errors="ignore")
        except Exception:
            # Ignore network or SSL failures silently
            pass
        return ""

    def _parse_page_content(self, html: str, page_url: str, emails: list, socials: dict):
        # Parse HTML safely
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception:
                soup = None

        if soup is None:
            # Fallback to simple regex if BS4 completely fails
            mailtos = re.findall(r'href=["\']mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', html, re.IGNORECASE)
            emails.extend(mailtos)
            general_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', html)
            emails.extend(general_emails)
            return

        # 1. Extract Emails
        # A. Mailto links (from a tags only)
        try:
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                if href.lower().startswith("mailto:"):
                    match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', href, re.IGNORECASE)
                    if match:
                        emails.append(match.group(1))
        except Exception:
            pass

        # B. General Regex patterns from visible text only
        try:
            # Remove elements we do not want to scrape emails from
            for tag in soup.find_all(["script", "style", "input", "textarea", "noscript", "svg", "head", "link", "meta"]):
                tag.decompose()
            
            visible_text = soup.get_text(separator=" ")
            general_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', visible_text)
            emails.extend(general_emails)
        except Exception:
            pass

        # 2. Extract Social Links
        try:
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                full_url = urljoin(page_url, href)
                lower_href = full_url.lower()
                
                # Check platforms and filter tracking/share/redirect links
                if "facebook.com" in lower_href and not any(x in lower_href for x in ["sharer", "share.php", "like.php"]):
                    socials["Facebook"] = full_url
                elif "instagram.com" in lower_href and not "share" in lower_href:
                    socials["Instagram"] = full_url
                elif "linkedin.com" in lower_href and not "share" in lower_href:
                    socials["LinkedIn"] = full_url
                elif ("twitter.com" in lower_href or "x.com" in lower_href) and not "intent" in lower_href:
                    socials["Twitter"] = full_url
                elif "youtube.com" in lower_href and not "share" in lower_href:
                    socials["YouTube"] = full_url
        except Exception:
            pass

    def _find_subpage_links(self, html: str, base_url: str) -> set:
        links = set()
        try:
            soup = BeautifulSoup(html, "lxml")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                full_url = urljoin(base_url, href)
                
                # Verify we stay on the same domain
                if extract_domain(full_url) == extract_domain(base_url):
                    lower_text = a_tag.text.lower()
                    lower_href = href.lower()
                    # Filter for about or contact indicators
                    if any(indicator in lower_text or indicator in lower_href for indicator in ["contact", "about", "reach", "info"]):
                        links.add(full_url)
        except Exception:
            pass
        return links

website_worker = WebsiteWorker()
