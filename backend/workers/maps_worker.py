import asyncio
import re
from urllib.parse import quote
from playwright.async_api import async_playwright
from backend.utils.logger import logger
from backend.workers.queue_manager import queue_manager
from backend.utils.normalizer import clean_text, normalize_string, clean_phone_digits, extract_domain, validate_business_record, format_duplicate_log, normalize_phone, normalize_website
from backend.utils.phone import parse_and_validate_phone
from backend.utils.address import parse_address

class MapsWorker:
    def __init__(self):
        self.seen_keys = set() # Duplicate prevention per mining session

    async def run(self, browser, state: str, district: str, keyword: str, settings, stats_callback, log_callback, country: str, business_offset: int = 0, stage_callback=None):
        """
        Runs the scraper for a specific keyword in a district.
        Yields raw scraped listings.
        """
        search_query = f"{keyword} in {district}, {state}, {country}"
        log_callback(f"Starting Google Maps search: '{search_query}'")
        if stage_callback:
            stage_callback("Searching", None)
        
        # We reuse the passed browser instance
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Search Google Maps
            url = f"https://www.google.com/maps/search/{quote(search_query)}"
            await page.goto(url, timeout=settings.google_timeout, wait_until="domcontentloaded")
            
            # Check for feed load
            try:
                await page.wait_for_selector('div[role="feed"]', timeout=15000)
            except Exception:
                # Sometimes there is only a single result and no feed load is necessary
                logger.warning("Feed selector not found; possibly a single search result.")
            
            # 2. Scroll the feed side panel
            feed_selector = 'div[role="feed"]'
            has_feed = await page.locator(feed_selector).count() > 0
            
            if has_feed:
                scroll_panel = page.locator(feed_selector)
                prev_count = 0
                no_change_streak = 0
                
                while not queue_manager.is_stopped:
                    await queue_manager.wait_if_paused()
                    
                    # Scroll down
                    await scroll_panel.evaluate("el => el.scrollTop += 6000")
                    await asyncio.sleep(settings.scroll_delay / 1000.0)
                    
                    # Check for end indicators
                    end_indicators = [
                        "span.HlvSq", 
                        "p.fontBodyMedium span[jslog]", 
                        "div.PbZDve p",
                        "div.HlvSq"
                    ]
                    end_reached = False
                    for selector in end_indicators:
                        if await page.locator(selector).count() > 0:
                            end_reached = True
                            break
                            
                    curr_count = await page.locator("a.hfpxzc").count()
                    if curr_count == prev_count:
                        no_change_streak += 1
                        if no_change_streak >= 4 or end_reached:
                            break
                        await asyncio.sleep(2.0)
                    else:
                        no_change_streak = 0
                        prev_count = curr_count
                        
                    # Slight scroll up and down if stuck
                    if no_change_streak == 1:
                        await scroll_panel.evaluate("el => el.scrollTop -= 800")
                        await asyncio.sleep(0.5)
                        await scroll_panel.evaluate("el => el.scrollTop += 6000")
                        await asyncio.sleep(1.5)
                        
            # Get all links
            listings = await page.locator("a.hfpxzc").all()
            total_found = len(listings)
            if stage_callback:
                stage_callback("TotalFound", total_found)
            log_callback(f"Found {total_found} listings for '{search_query}'. Extracting details...")
            
            # Iterate and extract details
            for i in range(business_offset, total_found):
                if queue_manager.is_stopped:
                    break
                await queue_manager.wait_if_paused()
                
                try:
                    # Reset all extracted fields at loop start to prevent stale data carry-over
                    phone = ""
                    mobile = ""
                    email = ""
                    website = ""
                    address = ""
                    phone_raw = ""
                    
                    item = page.locator("a.hfpxzc").nth(i)
                    name_raw = await item.get_attribute("aria-label")
                    name = clean_text(name_raw)

                    
                    if stage_callback:
                        stage_callback("Opening Business", name)
                        
                    # Click to show panel details
                    panel_loaded = False
                    details_name = "N/A"

                    for attempt in range(2):
                        try:
                            # Re-acquire the locator because Google Maps can refresh the results DOM
                            item = page.locator("a.hfpxzc").nth(i)

                            await item.scroll_into_view_if_needed()
                            await item.click()

                            # Poll details pane header instead of relying on a fixed sleep.
                            # Render can be slower than local Windows execution.
                            import time
                            start_wait = time.time()

                            while time.time() - start_wait < 10.0:
                                try:
                                    title_loc = page.locator("h1.DUwDvf")

                                    if await title_loc.count() > 0:
                                        title_text = await title_loc.first.text_content() or ""
                                        details_name = clean_text(title_text)

                                        if normalize_string(details_name) == normalize_string(name):
                                            panel_loaded = True
                                            break

                                except Exception:
                                    pass

                                await asyncio.sleep(0.2)

                            if panel_loaded:
                                break

                            logger.warning(
                                f"Panel attempt {attempt + 1}/2 did not match "
                                f"'{name}'. Current panel title: '{details_name}'."
                            )

                            # Give Google Maps a short moment before retrying.
                            await asyncio.sleep(0.5)

                        except Exception as e:
                            logger.warning(
                                f"Panel click attempt {attempt + 1}/2 failed for "
                                f"'{name}': {e}"
                            )

                    if not panel_loaded:
                        logger.warning(
                            f"Timeout waiting for details panel to match '{name}'. "
                            f"Current panel title: '{details_name}'. "
                            f"Skipping extraction to avoid stale data."
                        )
                        continue
                    
                    await asyncio.sleep(0.2) # Short settle delay
                    
                    if stage_callback:
                        stage_callback("Extracting Details", name)
                        
                    # Extract Address
                    address = "N/A"
                    address_loc = page.locator('button[data-item-id="address"]')
                    if await address_loc.count() > 0:
                        address = clean_text(await address_loc.first.text_content())
                        
                    # Extract Phone
                    phone_raw = ""
                    phone_loc = page.locator('button[aria-label^="Phone:"]')
                    if await phone_loc.count() > 0:
                        phone_raw = await phone_loc.first.get_attribute("aria-label")
                        
                    region = "US" if country == "USA" else "IN"
                    phone, mobile = parse_and_validate_phone(phone_raw, default_region=region)
                    
                    # Extract Website
                    website = "N/A"
                    web_loc = page.locator('a[data-item-id="authority"]')
                    if await web_loc.count() > 0:
                        website = await web_loc.first.get_attribute("href") or "N/A"
                        
                    # Log the 5 business data items for verification
                    logger.info(
                        f"Business Extraction Details:\n"
                        f"1. Selected Name (List): {name}\n"
                        f"2. Panel Name (Loaded): {details_name}\n"
                        f"3. Extracted Phone: {phone or 'N/A'}\n"
                        f"4. Extracted Mobile: {mobile or 'N/A'}\n"
                        f"5. Extracted Website: {website}"
                    )
                    
                    # Record Validation: strict mandatory field validation (Name, Address, Phone/Mobile)
                    is_rec_valid, reason_msg = validate_business_record(name, address, phone, mobile)
                    if not is_rec_valid:
                        logger.info(reason_msg)
                        continue

                        
                    # Parse address components
                    street, city, state_val, zip_code, country = parse_address(address, default_city=district)
                    
                    # Check duplicate logic before crawling website or saving
                    place_id = ""
                    place_match = re.search(r"PlaceID:([a-zA-Z0-9_-]+)", await item.get_attribute("jsaction") or "")
                    if place_match:
                        place_id = place_match.group(1)
                    
                    incoming_data = {
                        "name": name,
                        "address": address,
                        "place_id": place_id,
                        "phone": phone,
                        "mobile": mobile,
                        "website": website,
                        "email": ""
                    }
                    
                    # Immediately before duplicate detection, print the debug log
                    logger.info(
                        f"================================================\n\n"
                        f"Business Selected:\n{name}\n\n"
                        f"Business Displayed:\n{details_name}\n\n"
                        f"Phone:\n{phone or 'N/A'}\n\n"
                        f"Mobile:\n{mobile or 'N/A'}\n\n"
                        f"Email:\n{incoming_data.get('email') or 'N/A'}\n\n"
                        f"Website:\n{website or 'N/A'}\n\n"
                        f"================================================"
                    )
                    
                    if hasattr(self, "duplicate_detector") and self.duplicate_detector is not None:
                        is_dup, reason, matched_existing = await self.duplicate_detector.add_and_check(incoming_data)

                        if is_dup:
                            stats_callback("duplicate")
                            dup_log = format_duplicate_log(incoming_data, matched_existing, reason)
                            logger.info(dup_log)
                            continue
                        else:
                            if matched_existing and "row_index" in matched_existing:
                                incoming_data["row_index"] = matched_existing["row_index"]

                    else:
                        # Fallback to local seen_keys if duplicate_detector is not assigned
                        norm_ph = normalize_phone(phone)
                        norm_mob = normalize_phone(mobile)
                        norm_web = normalize_website(website)
                        is_dup = False
                        
                        if norm_ph and norm_ph in self.seen_keys:
                            is_dup = True
                        elif norm_mob and norm_mob in self.seen_keys:
                            is_dup = True
                        elif norm_web and norm_web in self.seen_keys:
                            is_dup = True
                            
                        if is_dup:
                            stats_callback("duplicate")
                            continue
                            
                        if norm_ph: self.seen_keys.add(norm_ph)
                        if norm_mob: self.seen_keys.add(norm_mob)
                        if norm_web: self.seen_keys.add(norm_web)
                    
                    # Extract Category
                    category = "N/A"
                    cat_loc = page.locator('button[jsaction="pane.rating.category"]')
                    if await cat_loc.count() > 0:
                        category = clean_text(await cat_loc.first.text_content())
                        
                    # Extract Maps URL
                    maps_url = page.url
                    
                    # Extract rating / reviews
                    rating = "0.0"
                    rating_loc = page.locator('div.F7nice span[aria-hidden="true"]')
                    if await rating_loc.count() > 0:
                        rating = await rating_loc.first.text_content()
                        
                    reviews = "0"
                    reviews_loc = page.locator('div.F7nice span[aria-label*="reviews"]')
                    if await reviews_loc.count() > 0:
                        rev_text = await reviews_loc.first.text_content()
                        reviews = re.sub(r"\D", "", rev_text or "0")
                        
                    business_data = {
                        "name": name,
                        "raw_phone": phone_raw,
                        "phone": phone,
                        "mobile": mobile,
                        "website": website,
                        "address": address,
                        "street": street,
                        "city": city,
                        "state": state_val,
                        "zip_code": zip_code,
                        "country": country,
                        "category": category,
                        "maps_url": maps_url,
                        "place_id": place_id,
                        "rating": rating,
                        "reviews": reviews,
                        "search_keyword": keyword,
                        "search_district": district,
                        "row_index": incoming_data.get("row_index")
                    }

                    
                    stats_callback("found")
                    yield business_data
                    
                except Exception as ie:
                    logger.warning(f"Error extracting row {i} details: {ie}")
                    stats_callback("error")
                    
        except Exception as e:
            logger.error(f"Error processing Maps Search '{search_query}': {e}", exc_info=True)
            log_callback(f"Failed to scrape Maps search '{search_query}': {e}")
        finally:
            await context.close()
                
maps_worker = MapsWorker()
