import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import re
import requests
from bs4 import BeautifulSoup
from geotext import GeoText
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ======= CONFIG =======
DAYS_LIMIT = 5
MAX_ARTICLES_PER_RUN = 10000000

GOOGLE_SHEET_NAME = "Agentis News Feed"
SERVICE_ACCOUNT_FILE = "service_account.json"

RSS_FEEDS = {
    "Renewable Energy": [
        {"name": "Renewables Now", "url": "https://renewablesnow.com/news.rss", "logo": "https://renewablesnow.com/favicon.ico", "source_type": "Media"},
        {"name": "PV Magazine", "url": "https://www.pv-magazine.com/feed/", "logo": "https://www.pv-magazine.com/favicon.ico", "source_type": "Media"},
        {"name": "Renewable Energy World", "url": "https://www.renewableenergyworld.com/feed/", "logo": "https://www.renewableenergyworld.com/favicon.ico", "source_type": "Media"},
        {"name": "Solar Power World", "url": "https://www.solarpowerworldonline.com/feed/", "logo": "https://www.solarpowerworldonline.com/favicon.ico", "source_type": "Media"},
        {"name": "Wind Power Engineering", "url": "https://www.windpowerengineering.com/feed/", "logo": "https://www.windpowerengineering.com/favicon.ico", "source_type": "Media"},
        {"name": "Energy Storage News", "url": "https://www.energy-storage.news/feed/", "logo": "https://www.energy-storage.news/favicon.ico", "source_type": "Media"},
        {"name": "Clean Energy Wire", "url": "https://www.cleanenergywire.org/rss", "logo": "https://www.cleanenergywire.org/favicon.ico", "source_type": "Media"},
        {"name": "Climate Change News", "url": "https://www.climatechangenews.com/feed/", "logo": "https://www.climatechangenews.com/favicon.ico", "source_type": "Media"},
        {"name": "ReCharge News", "url": "https://www.rechargenews.com/rss", "logo": "https://www.rechargenews.com/favicon.ico", "source_type": "Media"},
        {"name": "PV Tech", "url": "https://www.pv-tech.org/rss/", "logo": "https://www.pv-tech.org/favicon.ico", "source_type": "Media"},
        {"name": "Green Car Congress", "url": "https://www.greencarcongress.com/feed.xml", "logo": "https://www.greencarcongress.com/favicon.ico", "source_type": "Media"},
        {"name": "The Energy Mix", "url": "https://www.theenergymix.com/feed/", "logo": "https://www.theenergymix.com/favicon.ico", "source_type": "Media"},
        {"name": "Sustainability Times", "url": "https://www.sustainability-times.com/feed/", "logo": "https://www.sustainability-times.com/favicon.ico", "source_type": "Media"},
        {"name": "E&E News", "url": "https://www.eenews.net/rss", "logo": "https://www.eenews.net/favicon.ico", "source_type": "Media"},
        {"name": "Energy.gov Solar", "url": "https://www.energy.gov/eere/solar/rss.xml", "logo": "https://www.energy.gov/favicon.ico", "source_type": "Government"},
        {"name": "Energy.gov Wind", "url": "https://www.energy.gov/eere/wind/rss.xml", "logo": "https://www.energy.gov/favicon.ico", "source_type": "Government"}
    ],

    "Utilities & Grids": [
        {"name": "Utility Dive", "url": "https://www.utilitydive.com/feeds/news/", "logo": "https://www.utilitydive.com/favicon.ico", "source_type": "Media"},
        {"name": "Energy Central", "url": "https://www.energycentral.com/rss", "logo": "https://www.energycentral.com/favicon.ico", "source_type": "Media"},
        {"name": "Energy Manager Today", "url": "https://www.energymanagertoday.com/feed/", "logo": "https://www.energymanagertoday.com/favicon.ico", "source_type": "Media"},
        {"name": "Smart Energy International", "url": "https://www.smart-energy.com/feed/", "logo": "https://www.smart-energy.com/favicon.ico", "source_type": "Media"},
        {"name": "WaterWorld", "url": "https://www.waterworld.com/rss.xml", "logo": "https://www.waterworld.com/favicon.ico", "source_type": "Media"},
        {"name": "Municipal Sewer & Water", "url": "https://www.mswmag.com/rss/news.rss", "logo": "https://www.mswmag.com/favicon.ico", "source_type": "Media"},
        {"name": "GasWorld", "url": "https://www.gasworld.com/rss.xml", "logo": "https://www.gasworld.com/favicon.ico", "source_type": "Media"},
        {"name": "Power Technology", "url": "https://www.power-technology.com/feed/", "logo": "https://www.power-technology.com/favicon.ico", "source_type": "Media"},
        {"name": "Ofgem News", "url": "https://www.ofgem.gov.uk/publications/rss.xml", "logo": "https://www.ofgem.gov.uk/favicon.ico", "source_type": "Government"}
    ],

    "Digital Infrastructure": [
        {"name": "Telecoms.com", "url": "https://www.telecoms.com/feed/", "logo": "https://www.telecoms.com/favicon.ico", "source_type": "Media"},
        {"name": "Fierce Telecom", "url": "https://www.fiercetelecom.com/rss.xml", "logo": "https://www.fiercetelecom.com/favicon.ico", "source_type": "Media"},
        {"name": "Light Reading", "url": "https://www.lightreading.com/rss_simple.asp", "logo": "https://www.lightreading.com/favicon.ico", "source_type": "Media"},
        {"name": "Data Center Dynamics", "url": "https://www.datacenterdynamics.com/en/rss/", "logo": "https://www.datacenterdynamics.com/favicon.ico", "source_type": "Media"},
        {"name": "DgtlInfra", "url": "https://www.dgtlinfra.com/feed/", "logo": "https://www.dgtlinfra.com/favicon.ico", "source_type": "Media"},
        {"name": "Broadband TV News", "url": "https://www.broadbandtvnews.com/feed/", "logo": "https://www.broadbandtvnews.com/favicon.ico", "source_type": "Media"},
        {"name": "Mobile World Live", "url": "https://www.mobileworldlive.com/rss/", "logo": "https://www.mobileworldlive.com/favicon.ico", "source_type": "Media"},
        {"name": "RCR Wireless", "url": "https://www.rcrwireless.com/rss.xml", "logo": "https://www.rcrwireless.com/favicon.ico", "source_type": "Media"},
        {"name": "TeleGeography", "url": "https://www.telegeography.com/feed/", "logo": "https://www.telegeography.com/favicon.ico", "source_type": "Media"},
        {"name": "Capacity Media", "url": "https://www.capacitymedia.com/feed/", "logo": "https://www.capacitymedia.com/favicon.ico", "source_type": "Media"}
    ],

    "Public-Private Partnerships (PPP) & Social Infrastructure": [
        {"name": "InfraPPP", "url": "https://www.infrapppworld.com/rss", "logo": "https://www.infrapppworld.com/favicon.ico", "source_type": "Media"},
        {"name": "Global Infrastructure Hub", "url": "https://cdn.gihub.org/infrastructure-news/rss.xml", "logo": "https://cdn.gihub.org/favicon.ico", "source_type": "Government"},
        {"name": "Engineering News-Record", "url": "https://www.enr.com/rss/feed", "logo": "https://www.enr.com/favicon.ico", "source_type": "Media"},
        {"name": "Smart Cities Dive", "url": "https://www.smartcitiesdive.com/feeds/all/", "logo": "https://www.smartcitiesdive.com/favicon.ico", "source_type": "Media"},
        {"name": "Construction Dive", "url": "https://www.constructiondive.com/feeds/all/", "logo": "https://www.constructiondive.com/favicon.ico", "source_type": "Media"},
    ],

    "Investment & Project Finance": [
        {"name": "Infrastructure Investor", "url": "https://www.infrastructureinvestor.com/feed/", "logo": "https://www.infrastructureinvestor.com/favicon.ico", "source_type": "Finance"},
        {"name": "IJGlobal", "url": "https://www.ijglobal.com/rss/news", "logo": "https://www.ijglobal.com/favicon.ico", "source_type": "Finance"},
        {"name": "Private Equity International", "url": "https://www.privateequityinternational.com/feed/", "logo": "https://www.privateequityinternational.com/favicon.ico", "source_type": "Finance"},
        {"name": "PitchBook News", "url": "https://pitchbook.com/news/reports/feed", "logo": "https://pitchbook.com/favicon.ico", "source_type": "Finance"},
        {"name": "Preqin", "url": "https://www.preqin.com/insights/rss", "logo": "https://www.preqin.com/favicon.ico", "source_type": "Finance"},
        {"name": "PE Hub", "url": "https://www.pehub.com/feed/", "logo": "https://www.pehub.com/favicon.ico", "source_type": "Finance"},
        {"name": "Crunchbase News", "url": "https://news.crunchbase.com/feed/", "logo": "https://news.crunchbase.com/favicon.ico", "source_type": "Finance"},
        {"name": "AltAssets", "url": "https://www.altassets.net/rss", "logo": "https://www.altassets.net/favicon.ico", "source_type": "Finance"},
        {"name": "Financier Worldwide", "url": "https://www.financierworldwide.com/feed/", "logo": "https://www.financierworldwide.com/favicon.ico", "source_type": "Finance"},
        {"name": "Private Equity Wire", "url": "https://www.privateequitywire.co.uk/rss.xml", "logo": "https://www.privateequitywire.co.uk/favicon.ico", "source_type": "Finance"},
        {"name": "Project Finance Law", "url": "https://www.projectfinance.law/feed/", "logo": "https://www.projectfinance.law/favicon.ico", "source_type": "Finance"},
        {"name": "Devex", "url": "https://www.devex.com/news/feed", "logo": "https://www.devex.com/favicon.ico", "source_type": "Media"}
    ],

    "Energy Markets & Policy": [
        {"name": "S&P Global Market Intelligence", "url": "https://www.spglobal.com/marketintelligence/en/news-insights/latest-news/feed", "logo": "https://www.spglobal.com/favicon.ico", "source_type": "Finance"},
        {"name": "Bloomberg Energy Podcast", "url": "https://www.bloomberg.com/feeds/podcast/energy.xml", "logo": "https://www.bloomberg.com/favicon.ico", "source_type": "Media"},
        {"name": "Fitch Ratings News", "url": "https://www.fitchratings.com/rss/news", "logo": "https://www.fitchratings.com/favicon.ico", "source_type": "Finance"},
        {"name": "Reuters News", "url": "https://www.reuters.com/tools/rss", "logo": "https://www.reuters.com/favicon.ico", "source_type": "Media"},
        {"name": "International Energy Agency", "url": "https://www.iea.org/rss/news", "logo": "https://www.iea.org/favicon.ico", "source_type": "Government"},
        {"name": "Energy Information Administration", "url": "https://www.eia.gov/tools/rss/rss.xml", "logo": "https://www.eia.gov/favicon.ico", "source_type": "Government"},
        {"name": "Energy Policy Tracker", "url": "https://www.energypolicytracker.org/feed/", "logo": "https://www.energypolicytracker.org/favicon.ico", "source_type": "Media"}
    ],

    "Government & Regulatory": [
        {"name": "FERC News", "url": "https://www.ferc.gov/news-events/rss-feeds", "logo": "https://www.ferc.gov/favicon.ico", "source_type": "Government"},
        {"name": "EPA News Releases", "url": "https://www.epa.gov/newsreleases/rss.xml", "logo": "https://www.epa.gov/favicon.ico", "source_type": "Government"},
        {"name": "US Department of Energy", "url": "https://www.energy.gov/news.xml", "logo": "https://www.energy.gov/favicon.ico", "source_type": "Government"},
        {"name": "European Commission Energy", "url": "https://ec.europa.eu/energy/rss.xml", "logo": "https://ec.europa.eu/favicon.ico", "source_type": "Government"}
    ],

    "General Business & Finance": [
        {"name": "Wall Street Journal Energy", "url": "https://www.wsj.com/xml/rss/3_7455.xml", "logo": "https://www.wsj.com/favicon.ico", "source_type": "Finance"},
        {"name": "Financial Times", "url": "https://www.ft.com/?format=rss", "logo": "https://www.ft.com/favicon.ico", "source_type": "Finance"},
        {"name": "CNBC Energy", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "logo": "https://www.cnbc.com/favicon.ico", "source_type": "Media"},
        {"name": "Bloomberg Energy", "url": "https://www.bloomberg.com/feed/podcast/energy.xml", "logo": "https://www.bloomberg.com/favicon.ico", "source_type": "Media"},
        {"name": "Reuters Business News", "url": "https://www.reuters.com/tools/rss", "logo": "https://www.reuters.com/favicon.ico", "source_type": "Media"},
        {"name": "MarketWatch Energy", "url": "https://www.marketwatch.com/rss/topstories", "logo": "https://www.marketwatch.com/favicon.ico", "source_type": "Media"},
        {"name": "Investing.com Energy", "url": "https://www.investing.com/rss/news.rss", "logo": "https://www.investing.com/favicon.ico", "source_type": "Finance"}
    ],

    "Finance": [
        {"name": "Investing.com Energy", "url": "https://www.investing.com/rss/news.rss", "logo": "https://www.investing.com/favicon.ico", "source_type": "Finance"},
        {"name": "Reuters Business News", "url": "http://feeds.reuters.com/reuters/businessNews", "logo": "https://www.reuters.com/favicon.ico", "source_type": "Finance"},
        {"name": "Bloomberg Markets", "url": "https://www.bloomberg.com/feed/podcast/etf-report.xml", "logo": "https://www.bloomberg.com/favicon.ico", "source_type": "Finance"},
    ],
    "Technology": [
        {"name": "TechCrunch", "url": "http://feeds.feedburner.com/TechCrunch/", "logo": "https://techcrunch.com/favicon.ico", "source_type": "Technology"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "logo": "https://www.theverge.com/favicon.ico", "source_type": "Technology"},
        {"name": "Wired", "url": "https://www.wired.com/feed/rss", "logo": "https://www.wired.com/favicon.ico", "source_type": "Technology"},
    ],
    "General": [
        {"name": "CNN Top Stories", "url": "http://rss.cnn.com/rss/edition.rss", "logo": "https://www.cnn.com/favicon.ico", "source_type": "General"},
        {"name": "BBC World News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "logo": "https://www.bbc.com/favicon.ico", "source_type": "General"},
    ],

    "Other / Miscellaneous": []
}

KEYWORDS = [
    # General infrastructure & investment
    "infrastructure", "asset management", "fundraising", "investment", "fund", "private equity", "capital", "deal", "transaction",
    "acquisition", "merger", "portfolio", "exit", "valuation", "due diligence", "limited partner", "general partner", "commitment",
    "divestment", "capital raise", "secondary market", "co-investment", "dry powder", "yield", "cash flow", "IRR", "MOIC", "LP", "GP",
    "fee", "management fee", "carry", "capital call", "distribution", "bridge loan", "mezzanine", "senior debt", "subordinated debt",
    "leveraged buyout", "LBO",

    # Renewable energy & generation
    "solar", "pv", "photovoltaic", "wind", "offshore wind", "onshore wind", "battery", "energy storage", "hydrogen", "fuel cell",
    "renewable", "clean energy", "green energy", "carbon", "carbon credits", "carbon neutral", "emissions", "net zero", "climate",
    "energy transition", "distributed energy resources", "DER", "power purchase agreement", "PPA", "grid", "transmission", "distribution",
    "microgrid", "smart grid", "load balancing", "energy efficiency", "capacity", "dispatchable", "curtailment", "capacity factor",
    "generation asset", "photovoltaics", "solar farm", "wind farm", "renewable project", "green hydrogen",

    # Energy storage & battery
    "battery storage", "lithium-ion", "solid state battery", "BESS", "ESS", "battery plant", "battery capacity", "grid-scale battery",
    "battery facility", "energy storage system",

    # Utilities, water, gas & grid
    "utility", "utilities", "smart meter", "load shedding", "peak demand", "power outage", "sewer", "municipal water", "wastewater",
    "utility-scale", "grid reliability", "load management", "electric utility", "water utility", "gas utility",

    # Telecom & digital infrastructure
    "fiber", "ftth", "5g", "5g rollout", "digital infrastructure", "telecom", "broadband", "internet service provider", "ISP", "network",
    "data center", "edge computing", "cloud", "wireless", "wireline", "satellite", "mobile network", "telecommunications", "carrier",
    "tower", "fiber optic", "latency", "bandwidth", "spectrum", "IoT", "internet of things",

    # Financial & corporate terms
    "EBITDA", "revenue", "margin", "earnings", "cash flow", "debt", "leverage", "credit rating", "default", "bankruptcy", "loan",
    "interest rate", "covenant", "synergy", "earnout", "breakup fee", "lockup", "ipo", "public offering", "private placement",
    "underwriting", "valuation", "market cap", "shareholder", "stake", "ownership", "dividend", "earnings call", "guidance",

    # Policy, regulation, and government
    "policy", "regulation", "government", "tariff", "incentive", "subsidy", "tax credit", "environmental", "EPA", "FERC", "grid operator",
    "energy commission", "public utility commission", "renewable portfolio standard", "RPS", "net metering", "emission standard",
    "DOE", "US Department of Energy", "Ofgem", "European Commission", "IEA",

    # M&A specifics and legal jargon
    "buyout", "takeover", "hostile takeover", "due diligence", "purchase agreement", "stock purchase", "asset purchase", "merger agreement",
    "earnout", "closing conditions", "material adverse effect", "representations", "warranties",

    # Industry-specific technology and terms
    "turbine", "inverter", "substation", "transformer", "conduit", "conductor", "panel", "module", "rack", "tracker", "biomass",
    "geothermal", "hydropower", "tidal", "wave", "energy management system", "EMS", "HVDC", "EV charging", "charging station",

    # Smart cities, digital tech & resilience
    "smart city", "urban infrastructure", "resilient infrastructure", "urban planning", "infrastructure resilience", "smart lighting",
    "infrastructure monitoring", "sensors", "AI infrastructure", "smart infrastructure", "infrastructure analytics"
]

@st.cache_resource
def connect_to_sheet(sheet_name="Agentis News Feed"):
    # Use dict from secrets
    credentials_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(credentials_dict), scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def ensure_headers(sheet):
    desired_headers = [
        "title", "summary", "link", "published", "category",
        "source", "geography", "source_type", "ai_summary", "full_text"
    ]
    header_row = sheet.row_values(2)
    if header_row != desired_headers:
        if header_row:
            sheet.delete_row(2)
        sheet.insert_row(desired_headers, index=2)

def is_article_duplicate(sheet, link):
    links = [row[2] for row in sheet.get_all_values()[1:] if len(row) > 2]
    return link in links

def insert_article(article):
    sheet = connect_to_sheet()
    if is_article_duplicate(sheet, article['link']):
        return
    row = [
        article['title'], article['summary'], article['link'], article['published'],
        article['category'], article['source'], article['geography'], article['source_type'],
        article['ai_summary'], article['full_text']
    ]
    sheet.append_row(row, value_input_option='USER_ENTERED')

def get_last_run(sheet):
    val = sheet.cell(1,2).value if sheet.cell(1,2).value else None  # cell B1
    try:
        return pd.to_datetime(val)
    except:
        return datetime.now() - timedelta(days=DAYS_LIMIT)

def set_last_run(sheet):
    sheet.update_cell(1, 2, datetime.now().isoformat())

def insert_header_if_missing(sheet):
    first_row = sheet.row_values(2)
    if not first_row or first_row[0].lower() != "title":
        sheet.insert_row([
            "title", "summary", "link", "published", "category",
            "source", "geography", "source_type", "ai_summary", "full_text"
        ], index=2)
    if not sheet.cell(1,1).value or sheet.cell(1,1).value != "last_run":
        sheet.update_cell(1, 1, "last_run")
        sheet.update_cell(1, 2, (datetime.now() - timedelta(days=DAYS_LIMIT)).isoformat())

def clean_html(raw_html):
    return re.sub(r'<[^>]+>', '', raw_html).strip()

def detect_geography(text):
    if not text:
        return "Unknown"
    places = GeoText(text)
    return places.countries[0] if places.countries else (places.cities[0] if places.cities else "Unknown")

def call_openai_summary(text):
        return "" # Or: "AI summary disabled."

def fetch_article_fallback_bs4(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        tag = soup.find('div', {'class': 'article-content'}) or soup.find('article')
        return tag.get_text(strip=True) if tag else ""
    except:
        return ""

def article_matches_keywords(text):
    return any(re.search(rf'\b{re.escape(k.lower())}\b', text.lower()) for k in KEYWORDS)

def fetch_and_store_feeds():
    sheet = connect_to_sheet()
    insert_header_if_missing(sheet)
    last_run = get_last_run(sheet)
    count = 0
    for category, feeds in RSS_FEEDS.items():
        for feed_info in feeds:
            feed = feedparser.parse(feed_info['url'])
            for entry in feed.entries:
                if count >= MAX_ARTICLES_PER_RUN:
                    set_last_run(sheet)
                    return count
                title = entry.get('title', '').strip()
                summary = clean_html(entry.get('summary', '') or entry.get('description', ''))
                link = entry.get('link', '').strip()

                if not article_matches_keywords(f"{title} {summary}"):
                    continue

                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_dt = datetime(*entry.published_parsed[:6])
                    published = published_dt.isoformat()
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_dt = datetime(*entry.updated_parsed[:6])
                    published = published_dt.isoformat()
                else:
                    continue

                pub_date = pd.to_datetime(published, errors='coerce')
                if pd.isnull(pub_date) or pub_date <= last_run:
                    continue

                full_text = fetch_article_fallback_bs4(link)
                geography = detect_geography(full_text)
                ai_summary = call_openai_summary(full_text)

                insert_article({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'published': published,
                    'category': category,
                    'source': feed_info['name'],
                    'geography': geography,
                    'source_type': feed_info['source_type'],
                    'full_text': full_text,
                    'ai_summary': ai_summary
                })
                count += 1
    set_last_run(sheet)
    return count

def load_data():
    sheet = connect_to_sheet()
    ensure_headers(sheet)
    headers = [
        "title", "summary", "link", "published", "category",
        "source", "geography", "source_type", "ai_summary", "full_text"
    ]
    data = sheet.get_all_records(expected_headers=headers, head=2)
    df = pd.DataFrame(data)
    if not df.empty:
        df['published'] = pd.to_datetime(df['published'], errors='coerce')
    return df

# ---- Streamlit UI ----

st.set_page_config("Agentis News Dashboard", layout="wide")
st.title("Agentis Filtered News Dashboard")


if st.button("Fetch latest news", type="primary"):
    with st.spinner("Fetching latest news and updating sheet..."):
        added = fetch_and_store_feeds()
        st.success(f"Fetched and stored {added} new articles.")

df = load_data()

st.caption(f"Last data update: {df['published'].max().date() if not df.empty else 'No data loaded yet.'}")

if df.empty:
    st.info("No news articles yet.")
    st.stop()

# Sidebar Filters
with st.sidebar:
    st.markdown("## Filters")
    category_filter = st.selectbox("Category", [""] + sorted(df["category"].dropna().unique().tolist()))
    geography_filter = st.selectbox("Geography", [""] + sorted(df["geography"].dropna().unique().tolist()))
    source_type_filter = st.selectbox("Source Type", [""] + sorted(df["source_type"].dropna().unique().tolist()))
    source_filter = st.selectbox("Source", [""] + sorted(df["source"].dropna().unique().tolist()))
    date_from = st.date_input("Published From", value=None)
    date_to = st.date_input("Published To", value=None)
    search = st.text_input("Search (title, summary, etc)")

# Apply Filters
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
        lambda row: all(token in f"{row['title']} {row['summary']} {row['source']} {row['category']} {row['source_type']}".lower() for token in tokens),
        axis=1
    )]

filtered = filtered.sort_values(by="published", ascending=False)

# Show Table
st.write(f"### Showing {len(filtered)} articles")

if filtered.empty:
    st.warning("No articles match these filters.")
else:
    st.dataframe(filtered[["published", "title", "category", "source", "summary", "ai_summary"]], use_container_width=True)
    csv = filtered.to_csv(index=False)
    st.download_button("Download as CSV", csv, "filtered_news.csv", "text/csv")


