import os
import sys
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"


def run_update(email: str, password: str) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        try:
            _login(page, email, password)
            _update_profile(page)
        finally:
            context.close()
            browser.close()


def _login(page, email: str, password: str) -> None:
    log.info("Navigating to login page...")
    page.goto(NAUKRI_LOGIN_URL, wait_until="domcontentloaded")
    page.wait_for_selector("input#usernameField", timeout=15000)
    log.info("Login form loaded.")

    page.fill("input#usernameField", email)
    page.wait_for_timeout(400)
    page.fill("input#passwordField", password)
    page.wait_for_timeout(400)
    page.click('button[type="submit"]')

    try:
        page.wait_for_url(lambda url: "nlogin" not in url, timeout=15000)
        log.info("Login successful.")
    except PlaywrightTimeout:
        raise RuntimeError("Login failed — check your email/password.")


def _update_profile(page) -> None:
    log.info("Navigating to profile page...")
    page.goto(NAUKRI_PROFILE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # Open Basic Details modal (pencil icon at top of profile)
    log.info("Opening Basic Details edit modal...")
    edit_icons = page.locator("span.edit.icon, em.icon.edit").all()
    if not edit_icons:
        raise RuntimeError("Could not find edit icon on profile page.")
    edit_icons[0].click()
    page.wait_for_timeout(2500)

    # Read current name, clear it, type it back — triggers a change
    name_field = page.locator('input[name="name"], input[placeholder*="name" i]').first
    name_field.wait_for(timeout=8000)
    current_name = name_field.input_value()
    log.info("Current name: %s", current_name)

    name_field.click(click_count=3)         # select all
    name_field.press("Backspace")           # clear
    page.wait_for_timeout(300)
    name_field.type(current_name)           # retype same name
    page.wait_for_timeout(300)

    # Click Save (step 1 of wizard)
    log.info("Clicking Save (step 1)...")
    page.locator('button:has-text("Save"):not(.save-photo)').last.click()
    page.wait_for_timeout(2500)

    # If still a Save button visible, click again (step 2 of wizard)
    try:
        save2 = page.locator('button:has-text("Save"):not(.save-photo)').last
        if save2.is_visible(timeout=3000):
            log.info("Clicking Save (step 2)...")
            save2.click()
            page.wait_for_timeout(2500)
    except PlaywrightTimeout:
        pass

    log.info("Profile update complete.")


if __name__ == "__main__":
    _email = os.environ.get("NAUKRI_EMAIL", "").strip()
    _password = os.environ.get("NAUKRI_PASSWORD", "").strip()

    if not _email or not _password:
        log.error("Set NAUKRI_EMAIL and NAUKRI_PASSWORD in .env or environment.")
        sys.exit(1)

    run_update(_email, _password)
