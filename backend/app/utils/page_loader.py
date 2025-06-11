from playwright.async_api import async_playwright, Browser, Playwright, TimeoutError as PlaywrightTimeoutError
from loguru import logger

class PageLoader:
    _playwright: Playwright = None
    _browser: Browser = None

    @classmethod
    async def initialize(cls):
        if cls._browser:
            logger.warning("Browser is already initialized.")
            return
        cls._playwright = await async_playwright().start()
        cls._browser = await cls._playwright.chromium.launch()
        logger.info("Playwright browser initialized.")

    @classmethod
    async def shutdown(cls):
        if cls._browser:
            await cls._browser.close()
            cls._browser = None
        if cls._playwright:
            await cls._playwright.stop()
            cls._playwright = None
        logger.info("Playwright browser shut down.")

    async def load_page(self, url: str):
        if not self._browser:
            raise Exception("Browser is not initialized. Call initialize() first.")
        
        page = await self._browser.new_page()
        try:
            logger.info(f"Loading page: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            return page
        except PlaywrightTimeoutError:
            await page.close()
            raise
        except Exception as e:
            await page.close()
            logger.error(f"An unexpected error occurred while loading page {url}: {e}")
            raise 