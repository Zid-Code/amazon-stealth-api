# main.py - ULTIMATE STEALTH AMAZON API (WINDOWS PRODUCTION READY)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup
import time
import random
import re
from collections import Counter
from textblob import TextBlob
from datetime import datetime
import urllib.parse
import cloudscraper
import requests

app = FastAPI(
    title="Ultimate Ghost Stealth API",
    description="Amazon product data extraction with anti-detection",
    version="8.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ANTI-DETECTION TECHNIQUES ====================
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

ACCEPT_LANGUAGES = ['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'en-CA,en;q=0.9']
REFERERS = ['https://www.google.com/', 'https://www.bing.com/', 'https://duckduckgo.com/']
PLATFORMS = ['Windows', 'macOS', 'Linux']

def get_fingerprint():
    return {
        'user_agent': random.choice(USER_AGENTS),
        'accept_language': random.choice(ACCEPT_LANGUAGES),
        'referer': random.choice(REFERERS),
        'platform': random.choice(PLATFORMS),
    }

def add_random_param(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    query_params['_'] = [str(random.randint(100000, 999999))]
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

# ==================== CURRENCY & SENTIMENT ====================
def fast_currency_convert(price: float):
    return {"USD": round(price, 2), "EUR": round(price * 0.92, 2), "GBP": round(price * 0.79, 2)}

def analyze_sentiment(soup):
    reviews = []
    review_elements = soup.select('.review-text-content span')[:10]
    for elem in review_elements:
        text = elem.text.strip()
        if len(text) > 10:
            polarity = TextBlob(text).sentiment.polarity
            reviews.append(polarity)
    if not reviews:
        return {"status": "No reviews", "score": 0}
    avg = sum(reviews) / len(reviews)
    return {
        "status": "Positive" if avg > 0.1 else "Negative" if avg < -0.1 else "Neutral",
        "score": round(avg, 2),
        "count": len(reviews)
    }

# ==================== MAIN SCRAPER ====================
def scrape_amazon(url: str):
    fingerprint = get_fingerprint()
    url = add_random_param(url)
    
    time.sleep(random.uniform(2.0, 4.0))
    
    headers = {
        'User-Agent': fingerprint['user_agent'],
        'Accept-Language': fingerprint['accept_language'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': fingerprint['referer'],
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # استخدام cloudscraper لتجاوز Cloudflare
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.select_one('#productTitle')
        price = soup.select_one('.a-price .a-offscreen') or soup.select_one('#priceblock_ourprice')
        image = soup.select_one('#landingImage')
        rating = soup.select_one('.a-icon-alt')
        stock = soup.select_one('#availability span')
        
        if not title:
            return {"success": False, "error": "Blocked by Amazon - Product not found"}
        
        raw_price = price.text.strip() if price else "N/A"
        price_num = float(re.sub(r'[^\d.]', '', raw_price)) if any(d.isdigit() for d in raw_price) else 0.0
        
        return {
            "success": True,
            "title": title.text.strip(),
            "price": raw_price,
            "converted_prices": fast_currency_convert(price_num),
            "image": image.get('src') if image else None,
            "rating": rating.text.strip() if rating else None,
            "stock": stock.text.strip() if stock else "Unknown",
            "ai_sentiment": analyze_sentiment(soup),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== API ENDPOINTS ====================
class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    if "amazon." not in request.url.lower():
        raise HTTPException(status_code=400, detail="URL must be an Amazon product page")
    result = scrape_amazon(request.url)
    return result

@app.get("/health")
def health():
    return {"status": "alive", "version": "8.0.0", "techniques": 8}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)