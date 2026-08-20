import urllib.request
import urllib.parse
import json
import concurrent.futures
from backend.utils.logger import logger

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def _perform_translation(text: str) -> str:
    if not text or not isinstance(text, str) or text.strip() == "" or text == "N/A" or text == ".":
        return text
        
    # Check if text is pure ASCII to bypass translation API calls
    try:
        text.encode('ascii')
        return text
    except UnicodeEncodeError:
        pass # contains non-ascii characters, needs translation
        
    try:
        encoded_q = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={encoded_q}"
        
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = response.read().decode("utf-8")
            res_json = json.loads(res_data)
            translated = res_json[0][0][0]
            if translated:
                logger.info(f"Translated to English: '{text}' -> '{translated}'")
                return translated
    except Exception as e:
        logger.warning(f"Translation failed for '{text}': {e}")
        
    return text

async def translate_to_english_async(text: str) -> str:
    """Translates non-English texts to English asynchronously using a thread pool."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return _perform_translation(text)
    return await loop.run_in_executor(_executor, _perform_translation, text)
