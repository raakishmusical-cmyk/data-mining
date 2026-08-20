from backend.workers.website_worker import website_worker

class WebsiteService:
    async def scrape_site(self, url: str) -> dict:
        return await website_worker.scrape_website(url)

website_service = WebsiteService()
