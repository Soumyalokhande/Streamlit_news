# Streamlit News Dashboard — auto-refresh + strong geo normalization + curation
# Save as: Streamlit_app.py

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
from gspread.utils import rowcol_to_a1
import tldextract

# ======================== PLACEHOLDERS YOU SHOULD EDIT ========================
# Minimal sample feeds so the app runs. Replace/expand with your real feeds.
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
    "Infrastructure & Energy": [
        # Google News
        {"name": "Google News – Wind Energy", "url": "https://news.google.com/search?q=\"wind+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Solar Energy", "url": "https://news.google.com/search?q=\"solar+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Renewable Energy", "url": "https://news.google.com/search?q=\"renewable+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Battery Energy Storage", "url": "https://news.google.com/search?q=\"battery+energy+storage\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Power Generation", "url": "https://news.google.com/search?q=\"power+generation\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Utilities Infrastructure", "url": "https://news.google.com/search?q=\"utilities+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Greenfield Project", "url": "https://news.google.com/search?q=\"greenfield+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Brownfield Project", "url": "https://news.google.com/search?q=\"brownfield+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Community Solar", "url": "https://news.google.com/search?q=\"community+solar\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – EV Charging Station", "url": "https://news.google.com/search?q=\"ev+charging+station\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Hydrogen Production", "url": "https://news.google.com/search?q=\"hydrogen+production\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Roads Construction", "url": "https://news.google.com/search?q=\"roads+construction\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Transport Infrastructure", "url": "https://news.google.com/search?q=\"transport+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Railway Project", "url": "https://news.google.com/search?q=\"railway+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Highways Upgrade", "url": "https://news.google.com/search?q=\"highways+upgrade\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – PPP Project", "url": "https://news.google.com/search?q=\"ppp+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – DBFOM Contract", "url": "https://news.google.com/search?q=\"dbfom+contract\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Digital Infrastructure", "url": "https://news.google.com/search?q=\"digital+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Fiber Broadband", "url": "https://news.google.com/search?q=\"fiber+broadband\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Telecom Towers", "url": "https://news.google.com/search?q=\"telecom+towers\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Data Centre", "url": "https://news.google.com/search?q=\"data+centre\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – 5G Rollout", "url": "https://news.google.com/search?q=\"5g+rollout\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Cloud Infrastructure", "url": "https://news.google.com/search?q=\"cloud+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Student Housing", "url": "https://news.google.com/search?q=\"student+housing\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Hospital Construction", "url": "https://news.google.com/search?q=\"hospital+construction\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Museum Project", "url": "https://news.google.com/search?q=\"museum+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Science Centre", "url": "https://news.google.com/search?q=\"science+centre\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Storage Facility", "url": "https://news.google.com/search?q=\"storage+facility\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Water Infrastructure", "url": "https://news.google.com/search?q=\"water+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Wastewater Treatment", "url": "https://news.google.com/search?q=\"wastewater+treatment\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Gas Pipeline", "url": "https://news.google.com/search?q=\"gas+pipeline\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Public Infrastructure Investment", "url": "https://news.google.com/search?q=\"public+infrastructure+investment\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Infrastructure Acquisition", "url": "https://news.google.com/search?q=\"infrastructure+acquisition\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},

        # Yahoo News
        {"name": "Yahoo News – Wind Energy", "url": "https://news.search.yahoo.com/search?p=\"wind+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Solar Energy", "url": "https://news.search.yahoo.com/search?p=\"solar+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Renewable Energy", "url": "https://news.search.yahoo.com/search?p=\"renewable+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Battery Energy Storage", "url": "https://news.search.yahoo.com/search?p=\"battery+energy+storage\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Power Generation", "url": "https://news.search.yahoo.com/search?p=\"power+generation\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Utilities Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"utilities+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Greenfield Project", "url": "https://news.search.yahoo.com/search?p=\"greenfield+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Brownfield Project", "url": "https://news.search.yahoo.com/search?p=\"brownfield+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Community Solar", "url": "https://news.search.yahoo.com/search?p=\"community+solar\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – EV Charging Station", "url": "https://news.search.yahoo.com/search?p=\"ev+charging+station\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Hydrogen Production", "url": "https://news.search.yahoo.com/search?p=\"hydrogen+production\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Roads Construction", "url": "https://news.search.yahoo.com/search?p=\"roads+construction\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Transport Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"transport+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Railway Project", "url": "https://news.search.yahoo.com/search?p=\"railway+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Highways Upgrade", "url": "https://news.search.yahoo.com/search?p=\"highways+upgrade\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – PPP Project", "url": "https://news.search.yahoo.com/search?p=\"ppp+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – DBFOM Contract", "url": "https://news.search.yahoo.com/search?p=\"dbfom+contract\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Digital Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"digital+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Fiber Broadband", "url": "https://news.search.yahoo.com/search?p=\"fiber+broadband\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Telecom Towers", "url": "https://news.search.yahoo.com/search?p=\"telecom+towers\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Data Centre", "url": "https://news.search.yahoo.com/search?p=\"data+centre\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – 5G Rollout", "url": "https://news.search.yahoo.com/search?p=\"5g+rollout\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Cloud Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"cloud+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Student Housing", "url": "https://news.search.yahoo.com/search?p=\"student+housing\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Hospital Construction", "url": "https://news.search.yahoo.com/search?p=\"hospital+construction\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Museum Project", "url": "https://news.search.yahoo.com/search?p=\"museum+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Science Centre", "url": "https://news.search.yahoo.com/search?p=\"science+centre\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Storage Facility", "url": "https://news.search.yahoo.com/search?p=\"storage+facility\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Water Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"water+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Wastewater Treatment", "url": "https://news.search.yahoo.com/search?p=\"wastewater+treatment\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Gas Pipeline", "url": "https://news.search.yahoo.com/search?p=\"gas+pipeline\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Public Infrastructure Investment", "url": "https://news.search.yahoo.com/search?p=\"public+infrastructure+investment\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Infrastructure Acquisition", "url": "https://news.search.yahoo.com/search?p=\"infrastructure+acquisition\"", "source_type": "News Aggregator"},

        # Bing News
        {"name": "Bing News – Wind Energy", "url": "https://www.bing.com/news/search?q=\"wind+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Solar Energy", "url": "https://www.bing.com/news/search?q=\"solar+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Renewable Energy", "url": "https://www.bing.com/news/search?q=\"renewable+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Battery Energy Storage", "url": "https://www.bing.com/news/search?q=\"battery+energy+storage\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Power Generation", "url": "https://www.bing.com/news/search?q=\"power+generation\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Utilities Infrastructure", "url": "https://www.bing.com/news/search?q=\"utilities+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Greenfield Project", "url": "https://www.bing.com/news/search?q=\"greenfield+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Brownfield Project", "url": "https://www.bing.com/news/search?q=\"brownfield+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Community Solar", "url": "https://www.bing.com/news/search?q=\"community+solar\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – EV Charging Station", "url": "https://www.bing.com/news/search?q=\"ev+charging+station\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Hydrogen Production", "url": "https://www.bing.com/news/search?q=\"hydrogen+production\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Roads Construction", "url": "https://www.bing.com/news/search?q=\"roads+construction\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Transport Infrastructure", "url": "https://www.bing.com/news/search?q=\"transport+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Railway Project", "url": "https://www.bing.com/news/search?q=\"railway+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Highways Upgrade", "url": "https://www.bing.com/news/search?q=\"highways+upgrade\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – PPP Project", "url": "https://www.bing.com/news/search?q=\"ppp+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – DBFOM Contract", "url": "https://www.bing.com/news/search?q=\"dbfom+contract\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Digital Infrastructure", "url": "https://www.bing.com/news/search?q=\"digital+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Fiber Broadband", "url": "https://www.bing.com/news/search?q=\"fiber+broadband\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Telecom Towers", "url": "https://www.bing.com/news/search?q=\"telecom+towers\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Data Centre", "url": "https://www.bing.com/news/search?q=\"data+centre\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – 5G Rollout", "url": "https://www.bing.com/news/search?q=\"5g+rollout\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Cloud Infrastructure", "url": "https://www.bing.com/news/search?q=\"cloud+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        ],
    "Infrastructure & Energy": [
        # Google News
        {"name": "Google News – Wind Energy", "url": "https://news.google.com/search?q=\"wind+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Solar Energy", "url": "https://news.google.com/search?q=\"solar+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Renewable Energy", "url": "https://news.google.com/search?q=\"renewable+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Battery Energy Storage", "url": "https://news.google.com/search?q=\"battery+energy+storage\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Power Generation", "url": "https://news.google.com/search?q=\"power+generation\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Utilities Infrastructure", "url": "https://news.google.com/search?q=\"utilities+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Greenfield Project", "url": "https://news.google.com/search?q=\"greenfield+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Brownfield Project", "url": "https://news.google.com/search?q=\"brownfield+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Community Solar", "url": "https://news.google.com/search?q=\"community+solar\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – EV Charging Station", "url": "https://news.google.com/search?q=\"ev+charging+station\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Hydrogen Production", "url": "https://news.google.com/search?q=\"hydrogen+production\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Roads Construction", "url": "https://news.google.com/search?q=\"roads+construction\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Transport Infrastructure", "url": "https://news.google.com/search?q=\"transport+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Railway Project", "url": "https://news.google.com/search?q=\"railway+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Highways Upgrade", "url": "https://news.google.com/search?q=\"highways+upgrade\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – PPP Project", "url": "https://news.google.com/search?q=\"ppp+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – DBFOM Contract", "url": "https://news.google.com/search?q=\"dbfom+contract\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Digital Infrastructure", "url": "https://news.google.com/search?q=\"digital+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Fiber Broadband", "url": "https://news.google.com/search?q=\"fiber+broadband\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Telecom Towers", "url": "https://news.google.com/search?q=\"telecom+towers\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Data Centre", "url": "https://news.google.com/search?q=\"data+centre\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – 5G Rollout", "url": "https://news.google.com/search?q=\"5g+rollout\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Cloud Infrastructure", "url": "https://news.google.com/search?q=\"cloud+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Student Housing", "url": "https://news.google.com/search?q=\"student+housing\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Hospital Construction", "url": "https://news.google.com/search?q=\"hospital+construction\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Museum Project", "url": "https://news.google.com/search?q=\"museum+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Science Centre", "url": "https://news.google.com/search?q=\"science+centre\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Storage Facility", "url": "https://news.google.com/search?q=\"storage+facility\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Water Infrastructure", "url": "https://news.google.com/search?q=\"water+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Wastewater Treatment", "url": "https://news.google.com/search?q=\"wastewater+treatment\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Gas Pipeline", "url": "https://news.google.com/search?q=\"gas+pipeline\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Public Infrastructure Investment", "url": "https://news.google.com/search?q=\"public+infrastructure+investment\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Infrastructure Acquisition", "url": "https://news.google.com/search?q=\"infrastructure+acquisition\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},

        # Yahoo News (mirrors same keyword set)
        {"name": "Yahoo News – Wind Energy", "url": "https://news.search.yahoo.com/search?p=\"wind+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Solar Energy", "url": "https://news.search.yahoo.com/search?p=\"solar+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Renewable Energy", "url": "https://news.search.yahoo.com/search?p=\"renewable+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Battery Energy Storage", "url": "https://news.search.yahoo.com/search?p=\"battery+energy+storage\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Power Generation", "url": "https://news.search.yahoo.com/search?p=\"power+generation\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Utilities Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"utilities+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Greenfield Project", "url": "https://news.search.yahoo.com/search?p=\"greenfield+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Brownfield Project", "url": "https://news.search.yahoo.com/search?p=\"brownfield+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Community Solar", "url": "https://news.search.yahoo.com/search?p=\"community+solar\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – EV Charging Station", "url": "https://news.search.yahoo.com/search?p=\"ev+charging+station\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Hydrogen Production", "url": "https://news.search.yahoo.com/search?p=\"hydrogen+production\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Roads Construction", "url": "https://news.search.yahoo.com/search?p=\"roads+construction\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Transport Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"transport+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Railway Project", "url": "https://news.search.yahoo.com/search?p=\"railway+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Highways Upgrade", "url": "https://news.search.yahoo.com/search?p=\"highways+upgrade\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – PPP Project", "url": "https://news.search.yahoo.com/search?p=\"ppp+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – DBFOM Contract", "url": "https://news.search.yahoo.com/search?p=\"dbfom+contract\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Digital Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"digital+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Fiber Broadband", "url": "https://news.search.yahoo.com/search?p=\"fiber+broadband\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Telecom Towers", "url": "https://news.search.yahoo.com/search?p=\"telecom+towers\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Data Centre", "url": "https://news.search.yahoo.com/search?p=\"data+centre\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – 5G Rollout", "url": "https://news.search.yahoo.com/search?p=\"5g+rollout\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Cloud Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"cloud+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Student Housing", "url": "https://news.search.yahoo.com/search?p=\"student+housing\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Hospital Construction", "url": "https://news.search.yahoo.com/search?p=\"hospital+construction\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Museum Project", "url": "https://news.search.yahoo.com/search?p=\"museum+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Science Centre", "url": "https://news.search.yahoo.com/search?p=\"science+centre\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Storage Facility", "url": "https://news.search.yahoo.com/search?p=\"storage+facility\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Water Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"water+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Wastewater Treatment", "url": "https://news.search.yahoo.com/search?p=\"wastewater+treatment\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Gas Pipeline", "url": "https://news.search.yahoo.com/search?p=\"gas+pipeline\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Public Infrastructure Investment", "url": "https://news.search.yahoo.com/search?p=\"public+infrastructure+investment\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Infrastructure Acquisition", "url": "https://news.search.yahoo.com/search?p=\"infrastructure+acquisition\"", "source_type": "News Aggregator"},

        # Bing News (mirrors same keyword set)
        {"name": "Bing News – Wind Energy", "url": "https://www.bing.com/news/search?q=\"wind+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Solar Energy", "url": "https://www.bing.com/news/search?q=\"solar+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Renewable Energy", "url": "https://www.bing.com/news/search?q=\"renewable+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Battery Energy Storage", "url": "https://www.bing.com/news/search?q=\"battery+energy+storage\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Power Generation", "url": "https://www.bing.com/news/search?q=\"power+generation\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Utilities Infrastructure", "url": "https://www.bing.com/news/search?q=\"utilities+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Greenfield Project", "url": "https://www.bing.com/news/search?q=\"greenfield+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Brownfield Project", "url": "https://www.bing.com/news/search?q=\"brownfield+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Community Solar", "url": "https://www.bing.com/news/search?q=\"community+solar\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – EV Charging Station", "url": "https://www.bing.com/news/search?q=\"ev+charging+station\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Hydrogen Production", "url": "https://www.bing.com/news/search?q=\"hydrogen+production\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Roads Construction", "url": "https://www.bing.com/news/search?q=\"roads+construction\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Transport Infrastructure", "url": "https://www.bing.com/news/search?q=\"transport+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Railway Project", "url": "https://www.bing.com/news/search?q=\"railway+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Highways Upgrade", "url": "https://www.bing.com/news/search?q=\"highways+upgrade\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – PPP Project", "url": "https://www.bing.com/news/search?q=\"ppp+project\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – DBFOM Contract", "url": "https://www.bing.com/news/search?q=\"dbfom+contract\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Digital Infrastructure", "url": "https://www.bing.com/news/search?q=\"digital+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Fiber Broadband", "url": "https://www.bing.com/news/search?q=\"fiber+broadband\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Telecom Towers", "url": "https://www.bing.com/news/search?q=\"telecom+towers\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Data Centre", "url": "https://www.bing.com/news/search?q=\"data+centre\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – 5G Rollout", "url": "https://www.bing.com/news/search?q=\"5G+Rollout\"&cc=US", "source_type": "News Aggregator"},
        ],
    "Infrastructure & Energy": [
        # ---- Google News ----
        {"name": "Google News – Wind Energy", "url": "https://news.google.com/search?q=\"wind+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Solar Energy", "url": "https://news.google.com/search?q=\"solar+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Renewable Energy", "url": "https://news.google.com/search?q=\"renewable+energy\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Battery Energy Storage", "url": "https://news.google.com/search?q=\"battery+energy+storage\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Power Utilities", "url": "https://news.google.com/search?q=\"power+utilities\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Greenfield Project", "url": "https://news.google.com/search?q=\"greenfield+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Brownfield Project", "url": "https://news.google.com/search?q=\"brownfield+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Public Infrastructure", "url": "https://news.google.com/search?q=\"public+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Transport Infrastructure", "url": "https://news.google.com/search?q=\"transport+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Railway Project", "url": "https://news.google.com/search?q=\"railway+project\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Digital Infrastructure", "url": "https://news.google.com/search?q=\"digital+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Fiber Broadband", "url": "https://news.google.com/search?q=\"fiber+broadband\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Telecom Towers", "url": "https://news.google.com/search?q=\"telecom+towers\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Data Centres", "url": "https://news.google.com/search?q=\"data+centres\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – 5G Infrastructure", "url": "https://news.google.com/search?q=\"5g+infrastructure\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – EV Charging", "url": "https://news.google.com/search?q=\"ev+charging\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Student Housing", "url": "https://news.google.com/search?q=\"student+housing\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Hospitals", "url": "https://news.google.com/search?q=\"hospital+construction\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},
        {"name": "Google News – Gas Pipeline", "url": "https://news.google.com/search?q=\"gas+pipeline\"&hl=en-US&gl=US&ceid=US:en", "source_type": "News Aggregator"},

        # ---- Yahoo News ----
        {"name": "Yahoo News – Wind Energy", "url": "https://news.search.yahoo.com/search?p=\"wind+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Solar Energy", "url": "https://news.search.yahoo.com/search?p=\"solar+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Renewable Energy", "url": "https://news.search.yahoo.com/search?p=\"renewable+energy\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Battery Energy Storage", "url": "https://news.search.yahoo.com/search?p=\"battery+energy+storage\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Power Utilities", "url": "https://news.search.yahoo.com/search?p=\"power+utilities\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Greenfield Project", "url": "https://news.search.yahoo.com/search?p=\"greenfield+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Brownfield Project", "url": "https://news.search.yahoo.com/search?p=\"brownfield+project\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Public Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"public+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Transport Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"transport+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Digital Infrastructure", "url": "https://news.search.yahoo.com/search?p=\"digital+infrastructure\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Data Centres", "url": "https://news.search.yahoo.com/search?p=\"data+centres\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – EV Charging", "url": "https://news.search.yahoo.com/search?p=\"ev+charging\"", "source_type": "News Aggregator"},
        {"name": "Yahoo News – Hospitals", "url": "https://news.search.yahoo.com/search?p=\"hospital+construction\"", "source_type": "News Aggregator"},

        # ---- Bing News ----
        {"name": "Bing News – Wind Energy", "url": "https://www.bing.com/news/search?q=\"wind+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Solar Energy", "url": "https://www.bing.com/news/search?q=\"solar+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Renewable Energy", "url": "https://www.bing.com/news/search?q=\"renewable+energy\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Battery Energy Storage", "url": "https://www.bing.com/news/search?q=\"battery+energy+storage\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Power Utilities", "url": "https://www.bing.com/news/search?q=\"power+utilities\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Transport Infrastructure", "url": "https://www.bing.com/news/search?q=\"transport+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Data Centres", "url": "https://www.bing.com/news/search?q=\"data+centres\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – 5G Infrastructure", "url": "https://www.bing.com/news/search?q=\"5g+infrastructure\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – EV Charging", "url": "https://www.bing.com/news/search?q=\"ev+charging\"&cc=US", "source_type": "News Aggregator"},
        {"name": "Bing News – Hospitals", "url": "https://www.bing.com/news/search?q=\"hospital+construction\"&cc=US", "source_type": "News Aggregator"},
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

DAYS_LIMIT = 10
MAX_ARTICLES_PER_RUN = 200_000_000                 # keep reasonable for Sheets quotas
APPEND_SLEEP_SEC = 0.3                     # small pause between writes
GOOGLE_SHEET_NAME = "Agentis News Feed 2"

SHEET_HEADERS = [
    "title","summary","link","published","category",
    "source","geography","source_type",
    "ai_summary","full_text",
    "normalized_geography","transaction_type","relevance",
    "geo_confidence","geo_override"   # <-- added
]

# ======================== GEO NORMALIZATION ========================
US_STATES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia",
    "hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland","massachusetts",
    "michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey",
    "new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island",
    "south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia",
    "wisconsin","wyoming"
}
US_ABBR = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI",
    "MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT",
    "VT","VA","WA","WV","WI","WY"
}
CA_PROVINCES = {
    "alberta","british columbia","manitoba","new brunswick","newfoundland and labrador",
    "nova scotia","ontario","prince edward island","quebec","saskatchewan"
}
CA_ABBR = {"AB","BC","MB","NB","NL","NS","ON","PE","QC","SK"}

US_COMMON_CITIES = {
    "new york","los angeles","chicago","houston","phoenix","philadelphia","san antonio","san diego","dallas","san jose",
    "austin","jacksonville","fort worth","columbus","charlotte","san francisco","indianapolis","seattle","denver",
    "washington","boston","nashville","el paso","detroit","memphis","portland"
}
CA_COMMON_CITIES = {
    "toronto","montreal","vancouver","calgary","edmonton","ottawa","winnipeg","quebec city","hamilton","kitchener",
    "london","victoria","saskatoon","regina","halifax","windsor","st. john's","markham","vaughan","mississauga","brampton"
}

CC_MAP = {
    "us": "US", "ca": "Canada", "uk": "UK", "gb": "UK", "au": "Australia",
    "de": "Germany", "fr": "France", "es": "Spain", "it": "Italy", "in": "India",
}

def _domain_hint(url: str) -> str | None:
    if not url:
        return None
    try:
        ext = tldextract.extract(url)
        cc = ext.suffix.split(".")[-1].lower() if ext.suffix else ""
        return CC_MAP.get(cc)
    except Exception:
        return None

def normalize_geography_strong(raw_text: str, link: str = "") -> tuple[str, int]:
    """
    Return (country_label, confidence 0-100).
    Fuses: domain ccTLD, direct mentions, states/provinces/abbrev, common cities, GeoText, city/ST regex.
    """
    text = (raw_text or "").strip()
    low = f" {text.lower()} "
    scores: dict[str, int] = {}

    def bump(label, pts): scores[label] = scores.get(label, 0) + pts

    # 1) Domain hint
    hint = _domain_hint(link)
    if hint: bump(hint, 25)

    # 2) Direct mentions
    if any(tok in low for tok in [" united states ", " u.s. ", " usa ", " america "]): bump("US", 40)
    if " canada " in low: bump("Canada", 40)

    # 3) State / province + abbreviations
    if any(f" {s} " in low for s in US_STATES): bump("US", 35)
    if re.search(rf"\b({'|'.join(US_ABBR)})\b", text): bump("US", 30)
    if any(f" {p} " in low for p in CA_PROVINCES): bump("Canada", 35)
    if re.search(rf"\b({'|'.join(CA_ABBR)})\b", text): bump("Canada", 30)

    # 4) Common cities
    if any(f" {c} " in low for c in US_COMMON_CITIES): bump("US", 22)
    if any(f" {c} " in low for c in CA_COMMON_CITIES): bump("Canada", 22)

    # 5) GeoText countries
    try:
        places = GeoText(text)
        for ctry in places.countries:
            lc = ctry.lower()
            if "united states" in lc or "usa" in lc or "u.s." in lc: bump("US", 28)
            elif "canada" in lc: bump("Canada", 28)
    except Exception:
        pass

    # 6) City, ST patterns
    if re.search(rf"\b[A-Z][a-zA-Z.\- ]+,\s?({'|'.join(US_ABBR)})\b", text): bump("US", 26)
    if re.search(rf"\b[A-Z][a-zA-Z.\- ]+,\s?({'|'.join(CA_ABBR)})\b", text): bump("Canada", 26)

    if not scores:
        return ("Other", 10)

    label = max(scores, key=scores.get)
    conf = min(100, scores[label])
    return (label, conf)

# ======================== TRANSACTION TAGGING ========================
TX_PATTERNS = {
    "M&A": [
        r"\bacquires?\b", r"\bacquisition\b", r"\bmerger\b", r"\bmerges?\b",
        r"\btakeover\b", r"\bbuyout\b", r"\bsale of\b", r"\bsells?\b", r"\bdivest(s|iture|ment)\b"
    ],
    "Financial Close": [
        r"\bfinancial close\b", r"\breaches? financial close\b", r"\bfunded\b", r"\bdebt financing\b",
        r"\bproject finance\b", r"\bnon-recourse\b", r"\bterm loan\b"
    ],
    "Launch": [
        r"\blaunch(es|ed)?\b", r"\bopens?\b", r"\bgos? live\b"
    ],
    "Pre-launch": [
        r"\bpre[- ]?launch\b", r"\bpreliminary\b", r"\bterm sheet\b", r"\bmandate(d)?\b", r"\bRFP\b", r"\bmarket sounding\b"
    ],
}

def tag_transaction_type(text: str) -> str:
    if not text:
        return "Other"
    t = text.lower()
    for label, pats in TX_PATTERNS.items():
        for p in pats:
            if re.search(p, t):
                return label
    return "Other"

# ======================== SHEETS HELPERS ========================
@st.cache_resource
def connect_to_sheet(sheet_name=GOOGLE_SHEET_NAME):
    credentials_dict = dict(st.secrets["gcp_service_account"])  # put JSON dict in secrets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def ensure_headers(sheet):
    header_row = sheet.row_values(2)
    if header_row != SHEET_HEADERS:
        end_a1 = rowcol_to_a1(2, len(SHEET_HEADERS))  # e.g., "O2"
        sheet.update(f"A2:{end_a1}", [SHEET_HEADERS])

def insert_header_if_missing(sheet):
    ensure_headers(sheet)
    if not sheet.cell(1,1).value or sheet.cell(1,1).value != "last_run":
        sheet.update_cell(1, 1, "last_run")
        sheet.update_cell(1, 2, (datetime.now() - timedelta(days=DAYS_LIMIT)).isoformat())

def get_last_run(sheet):
    try:
        val = sheet.cell(1,2).value
        return pd.to_datetime(val) if val else (datetime.now() - timedelta(days=DAYS_LIMIT))
    except Exception:
        return datetime.now() - timedelta(days=DAYS_LIMIT)

def set_last_run(sheet):
    sheet.update_cell(1, 2, datetime.now().isoformat())

def clean_html(raw_html):
    return re.sub(r'<[^>]+>', '', raw_html or "").strip()

def detect_geography(text):
    if not text:
        return "Unknown"
    places = GeoText(text)
    return places.countries[0] if places.countries else (places.cities[0] if places.cities else "Unknown")

def fetch_article_fallback_bs4(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        tag = soup.find('div', {'class': 'article-content'}) or soup.find('article')
        return tag.get_text(strip=True) if tag else ""
    except Exception:
        return ""

def article_matches_keywords(text):
    return any(re.search(rf'\b{re.escape(k.lower())}\b', (text or "").lower()) for k in KEYWORDS)

def build_link_to_row_map(sheet):
    values = sheet.get_all_values()
    link_idx = SHEET_HEADERS.index("link")
    link_to_row = {}
    for i, row in enumerate(values[2:], start=3):  # data starts at row 3
        if len(row) > link_idx and row[link_idx]:
            link_to_row[row[link_idx]] = i
    return link_to_row

def _batch_update_single_column(links, target_col_name, value_or_callable):
    """Generic single-cell batch updater by link."""
    if not links:
        return 0
    sheet = connect_to_sheet()
    link_to_row = build_link_to_row_map(sheet)
    col_idx = SHEET_HEADERS.index(target_col_name) + 1

    requests_payload = []
    for link in links:
        r = link_to_row.get(link)
        if r:
            a1 = rowcol_to_a1(r, col_idx)
            new_val = value_or_callable(link) if callable(value_or_callable) else value_or_callable
            requests_payload.append({"range": a1, "values": [[new_val]]})

    if not requests_payload:
        return 0
    sheet.batch_update(requests_payload)
    return len(requests_payload)

def batch_update_relevance(links, label):
    return _batch_update_single_column(links, "relevance", label)

def batch_update_geo_override(links, override_label):
    return _batch_update_single_column(links, "geo_override", override_label)

def insert_article(article):
    sheet = connect_to_sheet()
    row = [
        article.get('title', ""), article.get('summary', ""), article.get('link', ""), article.get('published', ""),
        article.get('category', ""), article.get('source', ""), article.get('geography', ""), article.get('source_type', ""),
        article.get('ai_summary', ""), article.get('full_text', ""),
        article.get('normalized_geography', "Unknown"), article.get('transaction_type', "Other"),
        article.get('relevance', "unknown"),
        article.get('geo_confidence', 0), article.get('geo_override', "")
    ]
    sheet.append_row(row, value_input_option='USER_ENTERED')
    time.sleep(APPEND_SLEEP_SEC)

# ======================== FETCHER ========================
def fetch_and_store_feeds():
    sheet = connect_to_sheet()
    insert_header_if_missing(sheet)
    last_run = get_last_run(sheet)
    count = 0

    # Single read to load existing links
    all_rows = sheet.get_all_values()[1:]  # skip row1 meta
    link_idx = SHEET_HEADERS.index("link")
    existing_links = set(row[link_idx] for row in all_rows if len(row) > link_idx and row[link_idx])

    for category, feeds in RSS_FEEDS.items():
        for feed_info in feeds:
            feed = feedparser.parse(feed_info['url'])
            for entry in getattr(feed, "entries", []):
                if count >= MAX_ARTICLES_PER_RUN:
                    set_last_run(sheet)
                    return count

                title = (entry.get('title') or "").strip()
                link  = (entry.get('link')  or "").strip()
                summary = clean_html(entry.get('summary') or entry.get('description') or "")

                if not title or not link:
                    continue
                if not article_matches_keywords(f"{title} {summary}"):
                    continue
                if link in existing_links:
                    continue

                # published logic
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime(*entry.published_parsed[:6])
                    published = dt.isoformat()
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    dt = datetime(*entry.updated_parsed[:6])
                    published = dt.isoformat()
                else:
                    continue

                pub_date = pd.to_datetime(published, errors='coerce')
                if pd.isnull(pub_date) or pub_date <= last_run:
                    continue

                full_text = fetch_article_fallback_bs4(link)
                geo_text = " ".join([title, summary, full_text or ""])
                geography = detect_geography(full_text or summary or title)
                normalized_geo, geo_conf = normalize_geography_strong(geo_text, link=link)
                tx_type = tag_transaction_type(geo_text)

                insert_article({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'published': published,
                    'category': category,
                    'source': feed_info.get('name', ''),
                    'geography': geography,
                    'source_type': feed_info.get('source_type', ''),
                    'full_text': full_text,
                    'ai_summary': "",
                    'normalized_geography': normalized_geo,
                    'transaction_type': tx_type,
                    'relevance': "unknown",
                    'geo_confidence': geo_conf,
                    'geo_override': ""
                })
                existing_links.add(link)
                count += 1

    set_last_run(sheet)
    return count

# ======================== DATA LOAD ========================
def load_data():
    sheet = connect_to_sheet()
    ensure_headers(sheet)
    data = sheet.get_all_records(expected_headers=SHEET_HEADERS, head=2)
    df = pd.DataFrame(data)
    for col in SHEET_HEADERS:
        if col not in df.columns:
            df[col] = ""
    if not df.empty:
        df['published'] = pd.to_datetime(df['published'], errors='coerce')
    return df

def effective_geo_col(df: pd.DataFrame) -> pd.Series:
    # prefer manual override if set
    override = df["geo_override"].astype(str).str.strip()
    eff = override.where(override != "", df["normalized_geography"])
    return eff

# ======================== UI ========================
st.set_page_config("Agentis News Dashboard", layout="wide")
st.title("Agentis Filtered News Dashboard")

# Auto-refresh every 15 minutes (optional)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15 * 60 * 1000, key="auto_refresh_15min")
except Exception:
    st.info("Tip: install `streamlit-autorefresh` to enable background refresh.")

top_col1, top_col2 = st.columns([1,2])
with top_col1:
    if st.button("Fetch latest news", type="primary", use_container_width=True):
        with st.spinner("Fetching latest news and updating sheet…"):
            try:
                added = fetch_and_store_feeds()
                st.success(f"Fetched and stored {added} new articles.")
            except gspread.exceptions.APIError as e:
                st.error(f"Google Sheets API error. Try again later. ({e})")
            except Exception as e:
                st.error(f"Error during fetch: {e}")

df = load_data()

with top_col2:
    last_dt = df['published'].max() if not df.empty else None
    st.caption(f"Last data update: {last_dt.date() if pd.notnull(last_dt) else 'No data loaded yet.'}")

if df.empty:
    st.info("No news articles yet.")
    st.stop()

# -------- Filters --------
with st.sidebar:
    st.markdown("## Filters")
    category_filter = st.selectbox("Category", [""] + sorted(df["category"].dropna().unique().tolist()))
    source_filter   = st.selectbox("Source",   [""] + sorted(df["source"].dropna().unique().tolist()))
    geography_filter_raw = st.selectbox("Raw Geography (optional)", [""] + sorted(df["geography"].dropna().unique().tolist()))
    only_us_canada = st.checkbox("Show only US/Canada (effective geo)", value=True)
    tx_filter = st.multiselect(
        "Transaction types",
        ["M&A", "Financial Close", "Pre-launch", "Launch", "Other"],
        default=["M&A", "Financial Close", "Pre-launch", "Launch"]
    )
    relevance_only = st.checkbox("Only relevant", value=False)
    low_conf_only = st.checkbox("Low geo confidence (<=40)", value=False)
    date_from = st.date_input("Published From", value=None)
    date_to   = st.date_input("Published To",   value=None)
    search = st.text_input("Search (title/summary/source/category/type)")

filtered = df.copy()
eff_geo = effective_geo_col(filtered)
filtered = filtered.assign(effective_geo=eff_geo)

if category_filter:
    filtered = filtered[filtered["category"] == category_filter]
if source_filter:
    filtered = filtered[filtered["source"] == source_filter]
if geography_filter_raw:
    filtered = filtered[filtered["geography"] == geography_filter_raw]
if only_us_canada:
    filtered = filtered[filtered["effective_geo"].isin(["US", "Canada"])]
if tx_filter:
    filtered = filtered[filtered["transaction_type"].isin(tx_filter)]
if relevance_only:
    filtered = filtered[filtered["relevance"].str.lower() == "relevant"]
if low_conf_only:
    # geo_confidence may be empty string; coerce to numeric safely
    gc = pd.to_numeric(filtered["geo_confidence"], errors="coerce").fillna(0)
    filtered = filtered[gc <= 40]
if date_from:
    filtered = filtered[filtered["published"] >= pd.to_datetime(date_from)]
if date_to:
    filtered = filtered[filtered["published"] <= pd.to_datetime(date_to)]
if search:
    tokens = search.lower().split()
    def rowtext(r):
        return f"{r['title']} {r['summary']} {r['source']} {r['category']} {r['transaction_type']} {r['effective_geo']}".lower()
    filtered = filtered[filtered.apply(lambda r: all(t in rowtext(r) for t in tokens), axis=1)]

filtered = filtered.sort_values(by="published", ascending=False)

st.subheader(f"Results ({len(filtered)})")
if filtered.empty:
    st.warning("No articles match these filters.")
else:
    # Clickable titles (hide raw link), include geo/conf
    display_df = filtered[[
        "published","title","category","source","summary","link",
        "transaction_type","effective_geo","geo_confidence","relevance"
    ]].copy()
    display_df["title"] = display_df.apply(lambda row: f'<a href="{row["link"]}" target="_blank">{row["title"]}</a>', axis=1)
    display_df = display_df.drop(columns="link")
    st.write("_(Click the title to open the article)_")
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    csv = filtered[[
        "published","title","category","source","summary","link",
        "transaction_type","effective_geo","geo_confidence","relevance"
    ]].to_csv(index=False)
    st.download_button("Download as CSV", csv, "filtered_news.csv", "text/csv")

    # -------- Curation --------
    st.markdown("---")
    st.subheader("Curate relevance & geo override")

    table_for_edit = filtered[[
        "published","title","category","source","summary","link",
        "transaction_type","effective_geo","geo_confidence","relevance"
    ]].copy()
    table_for_edit.insert(0, "select", False)
    edited = st.data_editor(
        table_for_edit,
        hide_index=True,
        use_container_width=True,
        key="edit_table",
    )
    selected_links = edited[edited["select"]]["link"].tolist()

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,4])
    with c1:
        if st.button("Relevant ✅", disabled=len(selected_links)==0, use_container_width=True):
            n = batch_update_relevance(selected_links, "relevant")
            st.success(f"Updated {n} row(s) to relevant.")
            st.experimental_rerun()
    with c2:
        if st.button("Not Relevant 🚫", disabled=len(selected_links)==0, use_container_width=True):
            n = batch_update_relevance(selected_links, "not_relevant")
            st.success(f"Updated {n} row(s) to not_relevant.")
            st.experimental_rerun()
    with c3:
        if st.button("Set Geo: US", disabled=len(selected_links)==0, use_container_width=True):
            n = batch_update_geo_override(selected_links, "US")
            st.success(f"Set geo_override=US for {n} row(s).")
            st.experimental_rerun()
    with c4:
        if st.button("Set Geo: Canada", disabled=len(selected_links)==0, use_container_width=True):
            n = batch_update_geo_override(selected_links, "Canada")
            st.success(f"Set geo_override=Canada for {n} row(s).")
            st.experimental_rerun()





