# Streamlit_app.py
import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import requests
from bs4 import BeautifulSoup
from geotext import GeoText
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# CONFIG
# =========================
DAYS_LIMIT = 10
MAX_ARTICLES_PER_RUN = 1_000_000  # effectively unlimited for manual runs
GOOGLE_SHEET_NAME = "Agentis News Feed"

RSS_FEEDS = {
    "Renewable Energy": [
        {"name": "Renewables Now", "url": "https://renewablesnow.com/news.rss", "source_type": "Media"},
        {"name": "PV Magazine", "url": "https://www.pv-magazine.com/feed/", "source_type": "Media"},
        {"name": "Renewable Energy World", "url": "https://www.renewableenergyworld.com/feed/", "source_type": "Media"},
        {"name": "Solar Power World", "url": "https://www.solarpowerworldonline.com/feed/", "source_type": "Media"},
        {"name": "Wind Power Engineering", "url": "https://www.windpowerengineering.com/feed/", "source_type": "Media"},
        {"name": "Energy Storage News", "url": "https://www.energy-storage.news/feed/", "source_type": "Media"},
        {"name": "Clean Energy Wire", "url": "https://www.cleanenergywire.org/rss", "source_type": "Media"},
        {"name": "Climate Change News", "url": "https://www.climatechangenews.com/feed/", "source_type": "Media"},
        {"name": "ReCharge News", "url": "https://www.rechargenews.com/rss", "source_type": "Media"},
        {"name": "PV Tech", "url": "https://www.pv-tech.org/rss/", "source_type": "Media"},
        {"name": "Green Car Congress", "url": "https://www.greencarcongress.com/feed.xml", "source_type": "Media"},
        {"name": "The Energy Mix", "url": "https://www.theenergymix.com/feed/", "source_type": "Media"},
        {"name": "Sustainability Times", "url": "https://www.sustainability-times.com/feed/", "source_type": "Media"},
        {"name": "E&E News", "url": "https://www.eenews.net/rss", "source_type": "Media"},
        {"name": "Energy.gov Solar", "url": "https://www.energy.gov/eere/solar/rss.xml", "source_type": "Government"},
        {"name": "Energy.gov Wind", "url": "https://www.energy.gov/eere/wind/rss.xml", "source_type": "Government"},
    ],
    "Utilities & Grids": [
        {"name": "Utility Dive", "url": "https://www.utilitydive.com/feeds/news/", "source_type": "Media"},
        {"name": "Energy Central", "url": "https://www.energycentral.com/rss", "source_type": "Media"},
        {"name": "Energy Manager Today", "url": "https://www.energymanagertoday.com/feed/", "source_type": "Media"},
        {"name": "Smart Energy International", "url": "https://www.smart-energy.com/feed/", "source_type": "Media"},
        {"name": "WaterWorld", "url": "https://www.waterworld.com/rss.xml", "source_type": "Media"},
        {"name": "Municipal Sewer & Water", "url": "https://www.mswmag.com/rss/news.rss", "source_type": "Media"},
        {"name": "GasWorld", "url": "https://www.gasworld.com/rss.xml", "source_type": "Media"},
        {"name": "Power Technology", "url": "https://www.power-technology.com/feed/", "source_type": "Media"},
        {"name": "Ofgem News", "url": "https://www.ofgem.gov.uk/publications/rss.xml", "source_type": "Government"},
    ],
    "Digital Infrastructure": [
        {"name": "Telecoms.com", "url": "https://www.telecoms.com/feed/", "source_type": "Media"},
        {"name": "Fierce Telecom", "url": "https://www.fiercetelecom.com/rss.xml", "source_type": "Media"},
        {"name": "Light Reading", "url": "https://www.lightreading.com/rss_simple.asp", "source_type": "Media"},
        {"name": "Data Center Dynamics", "url": "https://www.datacenterdynamics.com/en/rss/", "source_type": "Media"},
        {"name": "DgtlInfra", "url": "https://www.dgtlinfra.com/feed/", "source_type": "Media"},
        {"name": "Broadband TV News", "url": "https://www.broadbandtvnews.com/feed/", "source_type": "Media"},
        {"name": "Mobile World Live", "url": "https://www.mobileworldlive.com/rss/", "source_type": "Media"},
        {"name": "RCR Wireless", "url": "https://www.rcrwireless.com/rss.xml", "source_type": "Media"},
        {"name": "TeleGeography", "url": "https://www.telegeography.com/feed/", "source_type": "Media"},
        {"name": "Capacity Media", "url": "https://www.capacitymedia.com/feed/", "source_type": "Media"},
    ],
    "Public-Private Partnerships (PPP) & Social Infrastructure": [
        {"name": "InfraPPP", "url": "https://www.infrapppworld.com/rss", "source_type": "Media"},
        {"name": "Global Infrastructure Hub", "url": "https://cdn.gihub.org/infrastructure-news/rss.xml", "source_type": "Government"},
        {"name": "Engineering News-Record", "url": "https://www.enr.com/rss/feed", "source_type": "Media"},
        {"name": "Smart Cities Dive", "url": "https://www.smartcitiesdive.com/feeds/all/", "source_type": "Media"},
        {"name": "Construction Dive", "url": "https://www.constructiondive.com/feeds/all/", "source_type": "Media"},
    ],
    "Investment & Project Finance": [
        {"name": "Infrastructure Investor", "url": "https://www.infrastructureinvestor.com/feed/", "source_type": "Finance"},
        {"name": "IJGlobal", "url": "https://www.ijglobal.com/rss/news", "source_type": "Finance"},
        {"name": "Private Equity International", "url": "https://www.privateequityinternational.com/feed/", "source_type": "Finance"},
        {"name": "PitchBook News", "url": "https://pitchbook.com/news/reports/feed", "source_type": "Finance"},
        {"name": "Preqin", "url": "https://www.preqin.com/insights/rss", "source_type": "Finance"},
        {"name": "PE Hub", "url": "https://www.pehub.com/feed/", "source_type": "Finance"},
        {"name": "Crunchbase News", "url": "https://news.crunchbase.com/feed/", "source_type": "Finance"},
        {"name": "AltAssets", "url": "https://www.altassets.net/rss", "source_type": "Finance"},
        {"name": "Financier Worldwide", "url": "https://www.financierworldwide.com/feed/", "source_type": "Finance"},
        {"name": "Private Equity Wire", "url": "https://www.privateequitywire.co.uk/rss.xml", "source_type": "Finance"},
        {"name": "Project Finance Law", "url": "https://www.projectfinance.law/feed/", "source_type": "Finance"},
        {"name": "Devex", "url": "https://www.devex.com/news/feed", "source_type": "Media"},
    ],
    "Energy Markets & Policy": [
        {"name": "S&P Global Market Intelligence", "url": "https://www.spglobal.com/marketintelligence/en/news-insights/latest-news/feed", "source_type": "Finance"},
        {"name": "Bloomberg Energy Podcast", "url": "https://www.bloomberg.com/feeds/podcast/energy.xml", "source_type": "Media"},
        {"name": "Fitch Ratings News", "url": "https://www.fitchratings.com/rss/news", "source_type": "Finance"},
        {"name": "Reuters News", "url": "https://www.reuters.com/tools/rss", "source_type": "Media"},
        {"name": "International Energy Agency", "url": "https://www.iea.org/rss/news", "source_type": "Government"},
        {"name": "Energy Information Administration", "url": "https://www.eia.gov/tools/rss/rss.xml", "source_type": "Government"},
        {"name": "Energy Policy Tracker", "url": "https://www.energypolicytracker.org/feed/", "source_type": "Media"},
    ],
    "Government & Regulatory": [
        {"name": "FERC News", "url": "https://www.ferc.gov/news-events/rss-feeds", "source_type": "Government"},
        {"name": "EPA News Releases", "url": "https://www.epa.gov/newsreleases/rss.xml", "source_type": "Government"},
        {"name": "US Department of Energy", "url": "https://www.energy.gov/news.xml", "source_type": "Government"},
        {"name": "European Commission Energy", "url": "https://ec.europa.eu/energy/rss.xml", "source_type": "Government"},
    ],
    "General Business & Finance": [
        {"name": "Wall Street Journal Energy", "url": "https://www.wsj.com/xml/rss/3_7455.xml", "source_type": "Finance"},
        {"name": "Financial Times", "url": "https://www.ft.com/?format=rss", "source_type": "Finance"},
        {"name": "CNBC Energy", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "source_type": "Media"},
        {"name": "Bloomberg Energy", "url": "https://www.bloomberg.com/feed/podcast/energy.xml", "source_type": "Media"},
        {"name": "Reuters Business News", "url": "https://www.reuters.com/tools/rss", "source_type": "Media"},
        {"name": "MarketWatch Energy", "url": "https://www.marketwatch.com/rss/topstories", "source_type": "Media"},
        {"name": "Investing.com Energy", "url": "https://www.investing.com/rss/news.rss", "source_type": "Finance"},
    ],
    "Finance": [
        {"name": "Investing.com Energy", "url": "https://www.investing.com/rss/news.rss", "source_type": "Finance"},
        {"name": "Reuters Business News", "url": "http://feeds.reuters.com/reuters/businessNews", "source_type": "Finance"},
        {"name": "Bloomberg Markets", "url": "https://www.bloomberg.com/feed/podcast/etf-report.xml", "source_type": "Finance"},
    ],
    "Technology": [
        {"name": "TechCrunch", "url": "http://feeds.feedburner.com/TechCrunch/","source_type": "Technology"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml","source_type": "Technology"},
        {"name": "Wired", "url": "https://www.wired.com/feed/rss","source_type": "Technology"},
    ],
    "General": [
        {"name": "CNN Top Stories", "url": "http://rss.cnn.com/rss/edition.rss", "source_type": "General"},
        {"name": "BBC World News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source_type": "General"},
    ],
    "Other / Miscellaneous": [],
}

KEYWORDS = [
    "infrastructure","asset management","fundraising","investment","fund","private equity","capital","deal","transaction",
    "acquisition","merger","portfolio","exit","valuation","limited partner","general partner","commitment","divestment",
    "solar","pv","photovoltaic","wind","offshore wind","onshore wind","battery","energy storage","hydrogen","renewable",
    "clean energy","grid","transmission","distribution","microgrid","smart grid","energy efficiency","capacity","PPA",
    "utility","utilities","power outage","water","wastewater","grid reliability",
    "fiber","ftth","5g","digital infrastructure","telecom","broadband","data center","cloud","wireless","tower",
    "EBITDA","revenue","margin","earnings","cash flow","debt","leverage","credit rating",
    "policy","regulation","government","tariff","subsidy","tax credit","EPA","FERC","DOE","Ofgem","IEA",
    "buyout","takeover","due diligence","merger agreement",
    "turbine","inverter","substation","transformer","hvdc","ev charging","charging station",
    "smart city","resilient infrastructure","sensors","AI infrastructure",
]

# =========================
# GOOGLE SHEETS HELPERS
# =========================
@st.cache_resource
def connect_to_sheet(sheet_name: str = GOOGLE_SHEET_NAME):
    credentials_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(credentials_dict), scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def ensure_headers(sheet):
    desired = ["title","summary","link","published","category","source","geography","source_type","ai_summary","full_text"]
    row2 = sheet.row_values(2)
    if row2 != desired:
        if row2:
            sheet.delete_row(2)
        sheet.insert_row(desired, index=2)
    # bootstrap last_run (row1)
    if not sheet.cell(1,1).value or sheet.cell(1,1).value != "last_run":
        sheet.update_cell(1,1,"last_run")
        sheet.update_cell(1,2,(datetime.now() - timedelta(days=DAYS_LIMIT)).isoformat())

def get_last_run(sheet) -> datetime:
    val = sheet.cell(1,2).value
    try:
        return pd.to_datetime(val)
    except Exception:
        return datetime.now() - timedelta(days=DAYS_LIMIT)

def set_last_run(sheet):
    sheet.update_cell(1,2, datetime.now().isoformat())

# =========================
# FETCHING HELPERS
# =========================
def clean_html(raw_html:str) -> str:
    return re.sub(r"<[^>]+>", "", raw_html or "").strip()

def detect_geography(text:str) -> str:
    if not text:
        return "Unknown"
    places = GeoText(text)
    return places.countries[0] if places.countries else (places.cities[0] if places.cities else "Unknown")

def fetch_article_fallback_bs4(url:str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find("div", {"class": "article-content"}) or soup.find("article")
        return tag.get_text(strip=True) if tag else ""
    except Exception:
        return ""

def article_matches_keywords(text:str) -> bool:
    text_l = (text or "").lower()
    return any(re.search(rf"\b{re.escape(k.lower())}\b", text_l) for k in KEYWORDS)

@st.cache_data(ttl=300)
def get_cached_links():
    """Prefer a narrow range read of the link column to reduce quota usage."""
    sheet = connect_to_sheet()
    try:
        vals = sheet.get_values("C3:C")
        return set(v[0] for v in vals if v)
    except Exception:
        # Fallback to broader read if needed
        all_rows = sheet.get_all_values()[1:]
        return set(r[2] for r in all_rows if len(r) > 2)

def fetch_and_store_feeds():
    sheet = connect_to_sheet()
    ensure_headers(sheet)
    last_run = get_last_run(sheet)

    try:
        existing_links = get_cached_links()
    except Exception:
        all_rows = sheet.get_all_values()[1:]
        existing_links = set(r[2] for r in all_rows if len(r) > 2)

    rows_to_append = []
    count = 0
    BATCH_SIZE = 50
    RATE_LIMIT_SECONDS = 0.5

    def flush_rows():
        nonlocal rows_to_append
        if not rows_to_append:
            return
        delay = 1.0
        for _ in range(5):
            try:
                sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
                rows_to_append = []
                get_cached_links.clear()  # invalidate cache after write
                return
            except gspread.exceptions.APIError as e:
                es = str(e)
                if "429" in es or "Quota exceeded" in es:
                    time.sleep(delay)
                    delay = min(delay * 2, 10)
                else:
                    raise

    for category, feeds in RSS_FEEDS.items():
        for feed_info in feeds:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries:
                if count >= MAX_ARTICLES_PER_RUN:
                    flush_rows()
                    return count

                title = (entry.get("title") or "").strip()
                summary = clean_html(entry.get("summary", "") or entry.get("description", "") or "")
                link = (entry.get("link") or "").strip()
                if not title or not link:
                    continue

                if link in existing_links:
                    continue

                if not article_matches_keywords(f"{title} {summary}"):
                    continue

                published = None
                if getattr(entry, "published_parsed", None):
                    published = datetime(*entry.published_parsed[:6]).isoformat()
                elif getattr(entry, "updated_parsed", None):
                    published = datetime(*entry.updated_parsed[:6]).isoformat()
                else:
                    continue

                pub_date = pd.to_datetime(published, errors="coerce")
                if pd.isna(pub_date) or pub_date <= last_run:
                    continue

                full_text = fetch_article_fallback_bs4(link)
                geography = detect_geography(full_text)

                rows_to_append.append([
                    title, summary, link, published,
                    category, feed_info["name"], geography, feed_info["source_type"],
                    "", full_text  # keep schema (ai_summary empty)
                ])
                existing_links.add(link)
                count += 1

                if len(rows_to_append) >= BATCH_SIZE:
                    flush_rows()

                time.sleep(RATE_LIMIT_SECONDS)
            time.sleep(0.5)  # brief pause between feeds

    flush_rows()
    set_last_run(sheet)  # only advance when full pass completes
    return count

def load_data():
    sheet = connect_to_sheet()
    ensure_headers(sheet)
    headers = ["title","summary","link","published","category","source","geography","source_type","ai_summary","full_text"]
    data = sheet.get_all_records(expected_headers=headers, head=2)
    df = pd.DataFrame(data)
    if not df.empty:
        df["published"] = pd.to_datetime(df["published"], errors="coerce")
    return df

# =========================
# UI
# =========================
st.set_page_config("Agentis News Dashboard", layout="wide")
st.title("Agentis Filtered News Dashboard")

# Optional self-refresh while open (requires extra dependency)
# from streamlit_autorefresh import st_autorefresh
# st_autorefresh(interval=5*60*1000, limit=10000, key="auto")  # every 5 min

colA, colB = st.columns([1,1])
with colA:
    if st.button("Fetch latest news", type="primary"):
        with st.spinner("Fetching latest news and updating sheet..."):
            added = fetch_and_store_feeds()
            st.success(f"Fetched and stored {added} new articles.")
with colB:
    st.caption("Tip: keep this open and click the button periodically. For auto-refresh, install `streamlit-autorefresh` and uncomment the code.")

df = load_data()
st.caption(f"Last data update: {df['published'].max().date() if not df.empty else 'No data loaded yet.'}")

if df.empty:
    st.info("No news articles yet.")
    st.stop()

# Filters
with st.sidebar:
    st.markdown("## Filters")
    category_filter = st.selectbox("Category", [""] + sorted(df["category"].dropna().unique().tolist()))
    geography_filter = st.selectbox("Geography", [""] + sorted(df["geography"].dropna().unique().tolist()))
    source_type_filter = st.selectbox("Source Type", [""] + sorted(df["source_type"].dropna().unique().tolist()))
    source_filter = st.selectbox("Source", [""] + sorted(df["source"].dropna().unique().tolist()))
    date_from = st.date_input("Published From", value=None)
    date_to = st.date_input("Published To", value=None)
    search = st.text_input("Search (title, summary, etc)")

filtered = df.copy()
if category_filter:
    filtered = filtered[filtered["category"] == category_filter]
if geography_filter:
    filtered = filtered[filtered["geography"] == geography_filter]
if source_type_filter:
    filtered = filtered[filtered["source_type"] == source_type_filter]
if source_filter:
    filtered = filtered[filtered["source"] == source_filter]
if date_from:
    filtered = filtered[filtered["published"] >= pd.to_datetime(date_from)]
if date_to:
    filtered = filtered[filtered["published"] <= pd.to_datetime(date_to)]
if search:
    tokens = search.lower().split()
    filtered = filtered[filtered.apply(
        lambda r: all(t in f"{r['title']} {r['summary']} {r['source']} {r['category']} {r['source_type']}".lower() for t in tokens),
        axis=1
    )]

filtered = filtered.sort_values(by="published", ascending=False)

st.write(f"### Showing {len(filtered)} articles")

if filtered.empty:
    st.warning("No articles match these filters.")
else:
    # clickable titles, no ai_summary in table
    display_df = filtered[["published","title","category","source","summary","link"]].copy()
    display_df["title"] = display_df.apply(lambda row: f'<a href="{row["link"]}" target="_blank">{row["title"]}</a>', axis=1)
    display_df = display_df.drop(columns="link")
    st.write("_(Click on an article title to open the link)_")
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    csv = filtered[["published","title","category","source","summary","link"]].to_csv(index=False)
    st.download_button("Download as CSV", csv, "filtered_news.csv", "text/csv")
