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

    # Audio/DSP alone is enough
    audio_dsp_keywords = [
        "audio dsp", "audio processing", "audio codec", "audio firmware",
        "audio embedded", "audio engineer", "audio developer", "audio software",
        "dsp engineer", "dsp developer", "dsp firmware", "dsp audio",
        "acoustic", "amplifier", "hifi", "audio algorithm", "speech processing",
        "voice processing", "sound processing",
    ]
    has_audio_dsp = any(k in combined for k in audio_dsp_keywords)

    # OR embedded C/DSP without explicit "audio" (covers roles like DSP Engineer, Embedded C)
    embedded_keywords = ["embedded c", "c/c++", "firmware engineer", "adsp", "arm intrinsics"]
    has_embedded = any(k in combined for k in embedded_keywords)

    return has_audio_dsp or has_embedded


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
    source = job.get("source", "")
    source_icon = {"Naukri": "🟠", "LinkedIn": "🔵", "TimesJobs": "🟣"}.get(source, "⚪")
    card += f"{source_icon} Source: {source}\n"
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


# ── LinkedIn guest API ────────────────────────────────────────────────────────
def fetch_linkedin_jobs(keyword: str) -> list:
    jobs = []
    encoded = urllib.parse.quote(keyword)
    url = (
        f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        f"?keywords={encoded}&location=Bengaluru%2C+Karnataka%2C+India"
        f"&f_TPR=r86400&start=0"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        titles   = re.findall(r'class="base-search-card__title"[^>]*>\s*([^<]+?)\s*<', html)
        companies = re.findall(r'class="base-search-card__subtitle"[^>]*>\s*([^<]+?)\s*<', html)
        links    = re.findall(r'href="(https://www\.linkedin\.com/jobs/view/[^"?]+)', html)
        for i in range(min(len(titles), len(companies), len(links))):
            jobs.append({
                "title": titles[i].strip(),
                "company": companies[i].strip(),
                "skills_raw": titles[i].lower(),
                "salary_listed": "",
                "min_exp": "", "max_exp": "",
                "posted": "Last 24 hrs",
                "is_fresh": True,
                "link": links[i],
                "job_id": f"li_{abs(hash(links[i]))}",
                "ambition_rating": "", "ambition_reviews": "",
                "source": "LinkedIn",
            })
        log.info("[LinkedIn] %s → %d jobs", keyword, len(jobs))
    except Exception as e:
        log.warning("[LinkedIn] failed for '%s': %s", keyword, e)
    return jobs


# ── TimesJobs search ──────────────────────────────────────────────────────────
def fetch_timesjobs(keyword: str) -> list:
    jobs = []
    encoded = urllib.parse.quote(keyword)
    url = (
        f"https://www.timesjobs.com/candidate/job-search.html"
        f"?searchType=personalizedSearch&from=submit"
        f"&txtKeywords={encoded}&txtLocation=Bengaluru"
        f"&postWeek=1"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        titles    = re.findall(r'class="[^"]*joblist-comp-name[^"]*"[^>]*>\s*<[^>]*>\s*([^<]+)', html)
        companies = re.findall(r'class="[^"]*joblist-comp-name[^"]*"[^>]*>\s*([^<]+)', html)
        links     = re.findall(r'href="(https://www\.timesjobs\.com/job-detail/[^"]+)"', html)
        skills_   = re.findall(r'class="[^"]*tags[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL)
        for i in range(min(len(titles), len(links))):
            company = companies[i].strip() if i < len(companies) else ""
            skill_text = re.sub(r'<[^>]+>', ' ', skills_[i]).strip() if i < len(skills_) else ""
            jobs.append({
                "title": titles[i].strip(),
                "company": company,
                "skills_raw": skill_text.lower(),
                "salary_listed": "",
                "min_exp": "", "max_exp": "",
                "posted": "Last 7 days",
                "is_fresh": False,
                "link": links[i],
                "job_id": f"tj_{abs(hash(links[i]))}",
                "ambition_rating": "", "ambition_reviews": "",
                "source": "TimesJobs",
            })
        log.info("[TimesJobs] %s → %d jobs", keyword, len(jobs))
    except Exception as e:
        log.warning("[TimesJobs] failed for '%s': %s", keyword, e)
    return jobs


# ── Google Jobs via SerpAPI ───────────────────────────────────────────────────
def fetch_google_jobs(keyword: str, fresh_only: bool = False) -> list:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        log.warning("[SerpAPI] SERPAPI_KEY not set, skipping.")
        return []

    jobs = []
    params = {
        "engine": "google_jobs",
        "q": f"{keyword} jobs bengaluru",
        "location": "Bengaluru, Karnataka, India",
        "api_key": api_key,
        "hl": "en",
        "gl": "in",
    }
    if fresh_only:
        params["chips"] = "date_posted:today"

    url = "https://serpapi.com/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())

        for job in data.get("jobs_results", []):
            ext = job.get("detected_extensions", {})
            posted = ext.get("posted_at", "")
            is_fresh = any(x in posted.lower() for x in
                           ["hour", "just now", "today", "1 day", "yesterday"])

            # Get best apply link
            apply_options = job.get("apply_options", [])
            if apply_options:
                link = apply_options[0].get("link", "")
                via = apply_options[0].get("title", "")
            else:
                link = job.get("related_links", [{}])[0].get("link", "")
                via = job.get("via", "")

            source_map = {
                "linkedin": "LinkedIn 🔵",
                "indeed": "Indeed 🟡",
                "glassdoor": "Glassdoor 🟢",
                "naukri": "Naukri 🟠",
                "foundit": "Foundit 🔷",
                "simplyhired": "SimplyHired ⚪",
            }
            via_lower = via.lower()
            source = next((v for k, v in source_map.items() if k in via_lower), via)

            jobs.append({
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "skills_raw": job.get("description", "")[:300].lower(),
                "salary_listed": ext.get("salary", ""),
                "min_exp": "", "max_exp": "",
                "posted": posted,
                "is_fresh": is_fresh,
                "link": link,
                "job_id": f"serp_{abs(hash(link or job.get('title','')))}",
                "ambition_rating": "", "ambition_reviews": "",
                "source": f"Google Jobs → {source}",
            })

        log.info("[SerpAPI] '%s' → %d jobs", keyword, len(jobs))
    except Exception as e:
        log.warning("[SerpAPI] failed for '%s': %s", keyword, e)
    return jobs


# ── DuckDuckGo multi-source search ───────────────────────────────────────────
JOB_SITES = ["linkedin.com", "glassdoor.co.in", "naukri.com",
             "in.indeed.com", "foundit.in", "simplyhired.co.in",
             "instahyre.com", "cutshort.io"]

def fetch_duckduckgo_jobs(keyword: str) -> tuple:
    """Returns (individual_jobs[], listing_links[])"""
    jobs, listings = [], []
    data = urllib.parse.urlencode({
        "q": f"{keyword} jobs bengaluru",
        "b": "", "kl": "in-en",
    }).encode()
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")

        titles   = re.findall(r'<a[^>]+class="result__a"[^>]*>([^<]+)</a>', html)
        links    = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', html)
        snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>([^<]+)<', html)

        for i in range(len(titles)):
            link = links[i] if i < len(links) else ""
            if "duckduckgo.com/y.js" in link:
                continue
            if not any(site in link for site in JOB_SITES):
                continue

            title = titles[i].strip()
            snippet = snippets[i].strip() if i < len(snippets) else ""
            source = next((s.split(".")[0].capitalize() for s in JOB_SITES if s in link), "Web")
            source_icons = {"Linkedin": "🔵", "Glassdoor": "🟢", "Naukri": "🟠",
                            "Indeed": "🟡", "Foundit": "🔷", "Simplyhired": "⚪",
                            "Instahyre": "🟣", "Cutshort": "🔴"}
            icon = source_icons.get(source, "🌐")

            # Individual job post (specific title + company)
            is_individual = bool(re.search(r'(engineer|developer|architect|lead|manager)\s', title, re.I))
            is_listing_page = any(x in title.lower() for x in ["jobs in", "job vacancies", "openings in", "positions in"])

            if is_individual and not is_listing_page:
                company = _extract_company_from_snippet(snippet)
                jobs.append({
                    "title": title, "company": company,
                    "skills_raw": title.lower() + " " + snippet.lower(),
                    "salary_listed": "", "min_exp": "", "max_exp": "",
                    "posted": "Recent", "is_fresh": False,
                    "link": link, "job_id": f"ddg_{abs(hash(link))}",
                    "ambition_rating": "", "ambition_reviews": "",
                    "source": source,
                })
            else:
                # Listing page — send as quick search link
                listings.append({"title": title, "link": link, "icon": icon, "source": source})

        log.info("[DDG] '%s' → %d jobs + %d listing links", keyword, len(jobs), len(listings))
    except Exception as e:
        log.warning("[DDG] failed for '%s': %s", keyword, e)
    return jobs, listings


def _extract_company_from_snippet(snippet: str) -> str:
    # Try to extract company name from snippet text
    match = re.search(r'at\s+([A-Z][A-Za-z\s&]+?)[\s\-\|]', snippet)
    if match:
        return match.group(1).strip()
    return ""


# ── Indeed India ─────────────────────────────────────────────────────────────
def fetch_indeed(keyword: str) -> list:
    jobs = []
    encoded = urllib.parse.quote(keyword)
    url = (
        f"https://in.indeed.com/jobs?q={encoded}"
        f"&l=Bengaluru%2C+Karnataka&fromage=3&sort=date"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        # Extract from embedded JSON
        matches = re.findall(
            r'"jobTitle"\s*:\s*"([^"]+)".*?"companyName"\s*:\s*"([^"]+)".*?"jobKey"\s*:\s*"([^"]+)"',
            html, re.DOTALL
        )
        for title, company, job_key in matches[:10]:
            jobs.append({
                "title": title, "company": company,
                "skills_raw": title.lower(),
                "salary_listed": "", "min_exp": "", "max_exp": "",
                "posted": "Last 3 days", "is_fresh": False,
                "link": f"https://in.indeed.com/viewjob?jk={job_key}",
                "job_id": f"indeed_{job_key}",
                "ambition_rating": "", "ambition_reviews": "",
                "source": "Indeed",
            })
        log.info("[Indeed] %s → %d jobs", keyword, len(jobs))
    except Exception as e:
        log.warning("[Indeed] failed for '%s': %s", keyword, e)
    return jobs


# ── Direct company career portals ─────────────────────────────────────────────
COMPANY_PORTALS = [
    {
        "name": "Qualcomm",
        "url": "https://careers.qualcomm.com/careers/search?keywords=audio+dsp&location=Bengaluru",
        "title_pattern": r'"title"\s*:\s*"([^"]+)"',
        "link_pattern": r'"canonicalPositionUrl"\s*:\s*"([^"]+)"',
        "source": "Qualcomm Careers",
    },
    {
        "name": "Harman",
        "url": "https://harman.wd1.myworkdayjobs.com/wday/cxs/harman/HarmanCareers/jobs",
        "title_pattern": r'"title"\s*:\s*"([^"]+)"',
        "link_pattern": r'"externalPath"\s*:\s*"([^"]+)"',
        "source": "Harman Careers",
        "post_data": b'{"appliedFacets":{"locations":["Bangalore"]},"limit":20,"searchText":"audio dsp"}',
    },
    {
        "name": "Ittiam",
        "url": "https://www.ittiam.com/careers/",
        "title_pattern": r'<h[23][^>]*>\s*([^<]*(?:audio|dsp|embedded|firmware)[^<]*)\s*</h[23]>',
        "link_pattern": r'href="(https://www\.ittiam\.com/careers/[^"]+)"',
        "source": "Ittiam Careers",
    },
    {
        "name": "Texas Instruments",
        "url": "https://careers.ti.com/search/#t=Jobs&numberOfResults=10&s=relevancy&SearchParameters[0][field]=category&SearchParameters[0][value]=Software%20Engineering&SearchParameters[1][field]=site_name&SearchParameters[1][value]=External&SearchParameters[2][field]=country_filter&SearchParameters[2][value]=India",
        "title_pattern": r'"jobTitle"\s*:\s*"([^"]+)"',
        "link_pattern": r'"jobUrl"\s*:\s*"([^"]+)"',
        "source": "TI Careers",
    },
]


def fetch_company_portal(portal: dict) -> list:
    jobs = []
    try:
        post_data = portal.get("post_data")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/json,*/*",
            "Content-Type": "application/json" if post_data else "text/html",
        }
        req = urllib.request.Request(portal["url"], data=post_data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            content = r.read().decode("utf-8", errors="replace")

        titles = re.findall(portal["title_pattern"], content, re.IGNORECASE)
        links  = re.findall(portal["link_pattern"], content, re.IGNORECASE)

        for i in range(min(len(titles), max(len(links), 1))):
            title = titles[i].strip()
            link = links[i] if i < len(links) else portal["url"]
            if not link.startswith("http"):
                link = "https://" + portal["name"].lower().replace(" ", "") + ".com" + link
            jobs.append({
                "title": title,
                "company": portal["name"],
                "skills_raw": title.lower(),
                "salary_listed": "", "min_exp": "", "max_exp": "",
                "posted": "Unknown", "is_fresh": False,
                "link": link,
                "job_id": f"{portal['name'].lower()}_{abs(hash(title))}",
                "ambition_rating": "", "ambition_reviews": "",
                "source": portal["source"],
            })
        log.info("[%s] → %d jobs", portal["source"], len(jobs))
    except Exception as e:
        log.warning("[%s] failed: %s", portal["source"], e)
    return jobs


# ── LinkedIn referral posts via DuckDuckGo ────────────────────────────────────
def fetch_linkedin_referrals() -> list:
    referrals = []
    queries = [
        'site:linkedin.com/posts "audio dsp" "bengaluru" "referral" OR "hiring" OR "opening"',
        'site:linkedin.com/posts "embedded c" "audio" "bangalore" "refer" OR "dm me" OR "hiring"',
    ]
    for query in queries:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode("utf-8", errors="replace")
            # Extract LinkedIn post links and snippets
            results = re.findall(
                r'href="(https://www\.linkedin\.com/posts/[^"]+)"[^>]*>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                html, re.DOTALL
            )
            for link, snippet in results[:5]:
                clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()[:150]
                referrals.append({
                    "link": link,
                    "snippet": clean_snippet,
                    "source": "LinkedIn Referral Post",
                })
            time.sleep(1)
        except Exception as e:
            log.warning("[LinkedIn Referrals] failed: %s", e)
    log.info("[LinkedIn Referrals] found %d posts", len(referrals))
    return referrals


def format_referral_section(referrals: list) -> str:
    if not referrals:
        return ""
    msg = "\n📢 <b>LinkedIn Referral Posts</b>\n━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(referrals[:5], 1):
        msg += f"\n{i}. {r['snippet']}\n"
        msg += f"🔗 <a href='{r['link']}'>View Post</a>\n"
    return msg


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    date_str = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    all_jobs = []
    seen_ids = set()

    def add_jobs(job_list):
        for job in job_list:
            if job["job_id"] not in seen_ids and is_relevant(job):
                all_jobs.append(job)
                seen_ids.add(job["job_id"])

    # ── Naukri (primary) ──
    for keyword in SEARCH_KEYWORDS:
        log.info("[Naukri] %s", keyword)
        raw_list = fetch_naukri_jobs(keyword, results=20)
        log.info("Got %d results", len(raw_list))
        parsed = []
        for raw in raw_list:
            job_id = str(raw.get("jobId", ""))
            if job_id not in seen_ids:
                job = parse_naukri_job(raw)
                job["source"] = "Naukri"
                parsed.append(job)
        add_jobs(parsed)
        time.sleep(1)

    # ── Google Jobs via SerpAPI (LinkedIn, Indeed, Glassdoor, company sites) ──
    for keyword in ["audio dsp c developer", "audio embedded c engineer"]:
        add_jobs(fetch_google_jobs(keyword, fresh_only=True))   # today only first
        time.sleep(1)
    for keyword in ["audio dsp c engineer bengaluru", "audio firmware c developer"]:
        add_jobs(fetch_google_jobs(keyword, fresh_only=False))  # broader search
        time.sleep(1)

    # ── DuckDuckGo multi-source (LinkedIn, Glassdoor, Indeed, Foundit, etc.) ──
    all_listings = []
    seen_listing_links = set()
    for keyword in ["audio dsp c developer", "audio embedded c engineer",
                    "audio dsp firmware engineer"]:
        indiv_jobs, listing_links = fetch_duckduckgo_jobs(keyword)
        add_jobs(indiv_jobs)
        for l in listing_links:
            if l["link"] not in seen_listing_links:
                all_listings.append(l)
                seen_listing_links.add(l["link"])
        time.sleep(1.5)

    # ── Direct company portals ──
    for portal in COMPANY_PORTALS:
        add_jobs(fetch_company_portal(portal))
        time.sleep(1)

    # ── LinkedIn referral posts ──
    referrals = fetch_linkedin_referrals()

    # Sort: fresh first, then priority companies
    all_jobs.sort(key=lambda j: (
        not j["is_fresh"],
        not any(c in j["company"].lower() for c in PRIORITY_COMPANIES),
    ))

    fresh = sum(j["is_fresh"] for j in all_jobs)
    log.info("Total relevant: %d | Fresh: %d | Referral posts: %d",
             len(all_jobs), fresh, len(referrals))

    # Send job alerts
    for msg in build_messages(all_jobs, date_str):
        send_telegram(msg)
        time.sleep(0.5)

    # Send referral posts
    ref_section = format_referral_section(referrals)
    if ref_section:
        send_telegram(ref_section)

    # Send quick search links (LinkedIn, Glassdoor, Indeed, etc.)
    if all_listings:
        links_msg = "🔍 <b>Search on Multiple Platforms</b>\n"
        links_msg += "👆 Tap any to browse all matching jobs:\n\n"
        seen_sources = set()
        for l in all_listings[:10]:
            if l["source"] not in seen_sources:
                links_msg += f"{l['icon']} <a href='{l['link']}'>{l['title'][:60]}</a>\n"
                seen_sources.add(l["source"])
        send_telegram(links_msg)

    log.info("Done.")


if __name__ == "__main__":
    main()
