import os
import sys
import json
import time
import logging
import urllib.request
import urllib.parse
import re
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

# ── Candidate profile (from CV) ───────────────────────────────────────────────
CANDIDATE_SKILLS = [
    "embedded c", "c", "dsp", "audio processing", "arm intrinsics",
    "hifi fusion", "linux", "misra c", "jenkins", "git", "jira",
    "sa8155p", "adsp-21593", "adsp-21489", "sigma studio",
    "cross core embedded studio", "xtensa xplorer", "unit testing",
    "static code analysis", "frequency spectrum", "audio", "amplifier",
    "sdk", "api development", "neural", "automotive",
]
CANDIDATE_EXP_YEARS = 3.5
CANDIDATE_CURRENT_SALARY = 6.63  # in Lakhs

# ── Company knowledge base ────────────────────────────────────────────────────
COMPANY_DB = {
    "qualcomm": {
        "type": "Product",
        "domain": "Semiconductors / Automotive / Mobile",
        "about": "World's largest wireless chip maker. SA8155p (your current hardware) is Qualcomm's automotive SoC — direct match.",
        "hike": "High (20–40% on joining)",
        "salary_3_5yr": "₹20L–₹35L",
    },
    "harman": {
        "type": "Product",
        "domain": "Audio / Automotive / Consumer Electronics",
        "about": "Samsung subsidiary. Makes JBL, Harman Kardon. Strong in automotive audio DSP — perfect match for audio processing skills.",
        "hike": "High (15–30%)",
        "salary_3_5yr": "₹15L–₹28L",
    },
    "ittiam": {
        "type": "Product",
        "domain": "Audio/Video DSP / Codecs",
        "about": "Bengaluru-based DSP IP company. Specialises in audio/video codecs — extremely relevant for DSP and audio skills.",
        "hike": "Moderate–High (15–25%)",
        "salary_3_5yr": "₹14L–₹22L",
    },
    "bosch": {
        "type": "Product",
        "domain": "Automotive / IoT",
        "about": "German MNC, world's largest auto supplier. Strong embedded/AUTOSAR roles in Bengaluru. Excellent job security.",
        "hike": "Moderate (10–20%)",
        "salary_3_5yr": "₹14L–₹24L",
    },
    "continental": {
        "type": "Product",
        "domain": "Automotive Embedded",
        "about": "German auto tech company. Big embedded team in Bengaluru. Good for automotive embedded C experience.",
        "hike": "Moderate (10–20%)",
        "salary_3_5yr": "₹13L–₹22L",
    },
    "texas instruments": {
        "type": "Product",
        "domain": "Semiconductors / DSP",
        "about": "Pioneer of DSP chips. Your DSP skills are core to TI's business. One of the best companies for DSP engineers.",
        "hike": "High (20–35%)",
        "salary_3_5yr": "₹18L–₹30L",
    },
    "nxp": {
        "type": "Product",
        "domain": "Semiconductors / Automotive",
        "about": "Netherlands chip company, strong in automotive MCUs. Good match for automotive embedded background.",
        "hike": "High (20–30%)",
        "salary_3_5yr": "₹16L–₹26L",
    },
    "analog devices": {
        "type": "Product",
        "domain": "Semiconductors / Audio DSP",
        "about": "Makes the ADSP-21593 chip you currently work on! Direct hands-on match — strong advantage in interview.",
        "hike": "High (20–35%)",
        "salary_3_5yr": "₹18L–₹30L",
    },
    "sasken": {
        "type": "Service",
        "domain": "Embedded / Telecom / Automotive",
        "about": "Bengaluru-based embedded services firm. Strong in automotive and telecom. Good stepping stone.",
        "hike": "Moderate (10–18%)",
        "salary_3_5yr": "₹10L–₹16L",
    },
    "aptiv": {
        "type": "Product",
        "domain": "Automotive Electrical",
        "about": "Spun off from Delphi. Autonomous driving and connected vehicles. Growing fast in India.",
        "hike": "High (15–25%)",
        "salary_3_5yr": "₹14L–₹24L",
    },
    "intel": {
        "type": "Product",
        "domain": "Semiconductors / AI",
        "about": "World's largest chipmaker. Strong embedded/firmware roles. Premium pay and benefits.",
        "hike": "High (25–40%)",
        "salary_3_5yr": "₹22L–₹38L",
    },
    "nvidia": {
        "type": "Product",
        "domain": "GPU / AI / Automotive",
        "about": "Top GPU maker expanding in automotive AI. Premium salaries. Competitive but worth applying.",
        "hike": "Very High (30–50%)",
        "salary_3_5yr": "₹25L–₹45L",
    },
    "renesas": {
        "type": "Product",
        "domain": "Semiconductors / Automotive MCU",
        "about": "Japanese chip company, top automotive MCU maker. Good embedded roles in Bengaluru.",
        "hike": "High (18–28%)",
        "salary_3_5yr": "₹15L–₹25L",
    },
    "mistral": {
        "type": "Service",
        "domain": "Embedded / Defence / Telecom",
        "about": "Bengaluru-based embedded solutions company. Works on defence and telecom embedded systems.",
        "hike": "Moderate (10–18%)",
        "salary_3_5yr": "₹10L–₹16L",
    },
    "tata elxsi": {
        "type": "Service",
        "domain": "Automotive / Broadcast / Healthcare",
        "about": "Your current employer. Moving here would be lateral — consider only for significant hike or role change.",
        "hike": "Low (already here)",
        "salary_3_5yr": "₹8L–₹14L",
    },
    "moschip": {
        "type": "Product",
        "domain": "Semiconductors / Embedded",
        "about": "Indian semiconductor company. Works on BSP and multimedia — good match for embedded Linux skills.",
        "hike": "Moderate (12–20%)",
        "salary_3_5yr": "₹10L–₹16L",
    },
    "broadcom": {
        "type": "Product",
        "domain": "Networking / Semiconductors",
        "about": "Top semiconductor company. Networking and storage chips. Good pay, competitive process.",
        "hike": "Very High (25–40%)",
        "salary_3_5yr": "₹20L–₹35L",
    },
    "mediatek": {
        "type": "Product",
        "domain": "Semiconductors / Mobile / IoT",
        "about": "Taiwan chip company. Mobile and IoT SoCs. Growing India team with good pay.",
        "hike": "High (20–30%)",
        "salary_3_5yr": "₹16L–₹28L",
    },
}

PRIORITY_COMPANIES = list(COMPANY_DB.keys())

SKILL_MATCH_KEYWORDS = {
    "dsp": "DSP algorithms",
    "audio": "Audio processing",
    "arm": "ARM intrinsics",
    "embedded": "Embedded C",
    "automotive": "Automotive (SA8155p)",
    "linux": "Linux",
    "misra": "MISRA C",
    "firmware": "Firmware dev",
    "rtos": "RTOS",
    "adsp": "ADSP hardware",
    "codec": "Audio codecs",
    "gstreamer": "GStreamer/multimedia",
    "bsp": "BSP development",
    "jenkins": "Jenkins CI/CD",
    "signal processing": "Signal processing",
    "amplifier": "Amplifier/audio hw",
    "c/c++": "C/C++",
    "sdk": "SDK development",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "appid": "109",
    "systemid": "Naukri",
    "Referer": "https://www.naukri.com/",
}

SEARCH_KEYWORDS = [
    "audio dsp c developer",
    "audio embedded c engineer",
    "dsp audio firmware engineer",
    "audio signal processing c",
]


# ── Telegram ──────────────────────────────────────────────────────────────────
def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_ids = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]
    if not token or not chat_ids:
        log.warning("Telegram not configured.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for chat_id in chat_ids:
        payload = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10):
                log.info("Telegram sent to %s", chat_id)
        except Exception as e:
            log.warning("Telegram failed: %s", e)


# ── Naukri public API ─────────────────────────────────────────────────────────
def fetch_naukri_jobs(keyword: str, results: int = 20) -> list:
    url = (
        f"https://www.naukri.com/jobapi/v2/search"
        f"?noOfResults={results}"
        f"&keyword={urllib.parse.quote(keyword)}"
        f"&city=bengaluru"
        f"&experience=3"
        f"&searchType=adv"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("list", [])
    except Exception as e:
        log.warning("Naukri failed for '%s': %s", keyword, e)
        return []


def parse_naukri_job(raw: dict) -> dict:
    add_date_str = raw.get("addDate", "")
    is_fresh = False
    posted_label = ""
    try:
        add_date = datetime.strptime(add_date_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
        add_date = add_date.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - add_date).total_seconds() / 3600
        is_fresh = age_hours <= 24
        posted_label = (
            "Just now" if age_hours < 1 else
            f"{int(age_hours)} hrs ago" if age_hours < 24 else
            "Yesterday" if age_hours < 48 else
            add_date.strftime("%d %b %Y")
        )
    except Exception:
        posted_label = add_date_str[:10] if add_date_str else ""

    min_sal = int(raw.get("minSal") or 0)
    max_sal = int(raw.get("maxSal") or 0)
    salary = (
        f"₹{min_sal/100000:.0f}L–₹{max_sal/100000:.0f}L"
        if raw.get("showSal", "n") != "n" and (min_sal or max_sal) else ""
    )

    return {
        "title": raw.get("post", ""),
        "company": raw.get("companyName", ""),
        "skills_raw": raw.get("keywords", ""),
        "salary_listed": salary,
        "min_exp": raw.get("minExp", ""),
        "max_exp": raw.get("maxExp", ""),
        "posted": posted_label,
        "is_fresh": is_fresh,
        "link": raw.get("urlStr", "") or f"https://www.naukri.com/job-listings-{raw.get('jobId','')}",
        "job_id": str(raw.get("jobId", "")),
        "ambition_rating": raw.get("ambitionBoxRating", ""),
        "ambition_reviews": raw.get("ambitionBoxReviewCount", ""),
    }


def is_relevant(job: dict) -> bool:
    combined = (job["title"] + " " + job["skills_raw"]).lower()

    # Must have Audio/DSP signal
    audio_dsp_keywords = ["audio", "dsp", "audio processing", "audio codec",
                          "acoustic", "amplifier", "sound", "speech", "voice",
                          "audio dsp", "hifi", "audio algorithm"]
    has_audio_dsp = any(k in combined for k in audio_dsp_keywords)

    # Must have C/Embedded C signal
    c_keywords = ["embedded c", "embedded-c", " c ", "c/c++", "c developer",
                  "c programming", "c language", "misra c", "firmware c",
                  "adsp", "arm intrinsics", "cortex"]
    has_c = any(k in combined for k in c_keywords)

    return has_audio_dsp and has_c


# ── CV match analysis ─────────────────────────────────────────────────────────
def get_match_reasons(job: dict) -> list:
    combined = (job["title"] + " " + job["skills_raw"]).lower()
    matched = []
    for kw, label in SKILL_MATCH_KEYWORDS.items():
        if kw in combined:
            matched.append(label)
    return matched[:5]  # top 5 matches


def get_company_info(company_name: str) -> dict:
    company_lower = company_name.lower()
    for key, info in COMPANY_DB.items():
        if key in company_lower:
            return info
    return None


def estimate_salary(job: dict, company_info: dict) -> str:
    if company_info:
        return company_info["salary_3_5yr"]
    # Generic estimate based on company type heuristics
    title_lower = job["title"].lower()
    if any(x in job["company"].lower() for x in ["tcs", "wipro", "infosys", "hcl", "cognizant"]):
        return "₹8L–₹12L"
    if "senior" in title_lower or "lead" in title_lower:
        return "₹14L–₹22L"
    return "₹10L–₹18L"


def get_hike_info(company_info: dict) -> str:
    if company_info:
        hike = company_info["hike"]
        current = CANDIDATE_CURRENT_SALARY
        # Parse hike range
        nums = re.findall(r'\d+', hike)
        if len(nums) >= 2:
            low = current * (1 + int(nums[0]) / 100)
            high = current * (1 + int(nums[1]) / 100)
            return f"{hike} → ~₹{low:.1f}L–₹{high:.1f}L expected CTC"
        return hike
    return "Varies"


# ── Format one job card ───────────────────────────────────────────────────────
def format_job_card(job: dict, index: int) -> str:
    company_info = get_company_info(job["company"])
    match_reasons = get_match_reasons(job)
    est_salary = estimate_salary(job, company_info)
    hike_info = get_hike_info(company_info)

    card = ""

    if job["is_fresh"]:
        card += "🔴 <b>POSTED IN LAST 24 HRS — APPLY NOW</b>\n"

    card += f"<b>{index}. {job['title']}</b>\n"
    card += f"🏢 {job['company']}"

    if job["ambition_rating"]:
        card += f" | ⭐ {job['ambition_rating']}/5"
    if job["ambition_reviews"]:
        card += f" ({job['ambition_reviews']} reviews)"
    card += "\n"

    if company_info:
        card += f"🏭 <b>{company_info['type']} Company</b> | {company_info['domain']}\n"
        card += f"ℹ️ {company_info['about']}\n"

    exp_label = f"{job['min_exp']}–{job['max_exp']} yrs" if job["min_exp"] else ""
    if exp_label:
        card += f"⏳ Required: {exp_label}\n"

    if job["salary_listed"]:
        card += f"💰 Listed: {job['salary_listed']}\n"
    card += f"📊 Market rate (3–5yr): {est_salary}\n"
    card += f"📈 Expected hike: {hike_info}\n"

    if match_reasons:
        card += f"✅ CV Match: {', '.join(match_reasons)}\n"

    card += f"🕐 Posted: {job['posted']}\n"
    card += f"🔗 <a href='{job['link']}'>Apply Here</a>\n"
    return card


# ── Build Telegram messages (split at 3800 chars) ─────────────────────────────
def build_messages(jobs: list, date_str: str) -> list:
    if not jobs:
        return [
            f"🔍 <b>Job Alert — {date_str}</b>\n\n"
            f"No matching Embedded/DSP jobs in Bengaluru today.\nWill check again tomorrow!"
        ]

    fresh = sum(j["is_fresh"] for j in jobs)
    header = (
        f"💼 <b>Job Alerts — Bengaluru</b>\n"
        f"📅 {date_str}\n"
        f"🎯 Embedded | DSP | Audio | Automotive\n"
        f"📊 {len(jobs)} relevant jobs"
        + (f" | 🔴 {fresh} new today" if fresh else "")
        + "\n━━━━━━━━━━━━━━━\n\n"
    )

    messages = []
    current = header

    for i, job in enumerate(jobs[:12], 1):
        card = format_job_card(job, i) + "\n"
        if len(current) + len(card) > 3800:
            messages.append(current)
            current = f"💼 <b>More Jobs (cont.)</b>\n\n" + card
        else:
            current += card

    messages.append(current)
    return messages


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    date_str = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    all_jobs = []
    seen_ids = set()

    for keyword in SEARCH_KEYWORDS:
        log.info("Searching: %s", keyword)
        raw_list = fetch_naukri_jobs(keyword, results=20)
        log.info("Got %d results", len(raw_list))
        for raw in raw_list:
            job_id = str(raw.get("jobId", ""))
            if job_id not in seen_ids:
                job = parse_naukri_job(raw)
                if is_relevant(job):
                    all_jobs.append(job)
                    seen_ids.add(job_id)
        time.sleep(1)

    # Sort: fresh first, then priority companies, then rest
    all_jobs.sort(key=lambda j: (
        not j["is_fresh"],
        not any(c in j["company"].lower() for c in PRIORITY_COMPANIES),
    ))

    log.info("Total relevant: %d | Fresh: %d", len(all_jobs), sum(j["is_fresh"] for j in all_jobs))

    for msg in build_messages(all_jobs, date_str):
        send_telegram(msg)
        time.sleep(0.5)

    log.info("Done.")


if __name__ == "__main__":
    main()
