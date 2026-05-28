import os
import sys
import logging
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

LOG_FILE = "run_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

IST = timezone(timedelta(hours=5, minutes=30))


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_IDS", "").strip()

    if not token or not chat_ids_raw:
        log.warning("Telegram not configured — skipping notification.")
        return

    chat_ids = [c.strip() for c in chat_ids_raw.split(",") if c.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chat_id in chat_ids:
        payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    log.info("Telegram notification sent to %s", chat_id)
                else:
                    log.warning("Telegram returned status %s for %s", resp.status, chat_id)
        except Exception as exc:
            log.warning("Telegram notification failed for %s: %s", chat_id, exc)


def run_update(email: str, password: str) -> None:
    now = datetime.now(IST).strftime("%I:%M %p IST, %d %b %Y")
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
            name = _update_profile(page)
            msg = (
                f"✅ <b>Naukri Profile Updated</b>\n"
                f"👤 Profile: {name}\n"
                f"🕐 Time: {now}\n"
                f"📌 Status: Success"
            )
            log.info("Update successful for profile: %s", name)
            send_telegram(msg)
        except Exception as exc:
            msg = (
                f"❌ <b>Naukri Update FAILED</b>\n"
                f"🕐 Time: {now}\n"
                f"⚠️ Error: {exc}"
            )
            log.error("Update failed: %s", exc)
            send_telegram(msg)
            sys.exit(1)
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
        page.screenshot(path="login_failed.png", full_page=True)
        log.error("Page URL after submit: %s", page.url)
        log.error("Page title: %s", page.title())
        # Log any visible error text
        for sel in ['.errmsg', '.error-msg', '[class*=error]', '[class*=alert]', 'p']:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=500):
                    log.error("Visible text (%s): %s", sel, el.inner_text()[:200])
            except Exception:
                pass
        raise RuntimeError("Login failed — see logs above for Naukri's response.")


def _update_profile(page) -> str:
    log.info("Navigating to profile page...")
    page.goto(NAUKRI_PROFILE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    log.info("Opening Basic Details edit modal...")
    edit_icons = page.locator("span.edit.icon, em.icon.edit").all()
    if not edit_icons:
        raise RuntimeError("Could not find edit icon on profile page.")
    edit_icons[0].click()
    page.wait_for_timeout(2500)

    name_field = page.locator('input[name="name"], input[placeholder*="name" i]').first
    name_field.wait_for(timeout=8000)
    current_name = name_field.input_value()
    log.info("Current name: %s", current_name)

    name_field.click(click_count=3)
    name_field.press("Backspace")
    page.wait_for_timeout(300)
    name_field.type(current_name)
    page.wait_for_timeout(300)

    log.info("Clicking Save (step 1)...")
    page.locator('button:has-text("Save"):not(.save-photo)').last.click()
    page.wait_for_timeout(2500)

    try:
        save2 = page.locator('button:has-text("Save"):not(.save-photo)').last
        if save2.is_visible(timeout=3000):
            log.info("Clicking Save (step 2)...")
            save2.click()
            page.wait_for_timeout(2500)
    except PlaywrightTimeout:
        pass

    log.info("Profile update complete.")
    return current_name


if __name__ == "__main__":
    _email = os.environ.get("NAUKRI_EMAIL", "").strip()
    _password = os.environ.get("NAUKRI_PASSWORD", "").strip()

    if not _email or not _password:
        log.error("Set NAUKRI_EMAIL and NAUKRI_PASSWORD in .env or environment.")
        sys.exit(1)

    run_update(_email, _password)
