import sys, json
sys.path.insert(0, "E:/东方南通/agricultural-news-analysis")

import os, shutil

# Clear old database to start fresh
db_path = "E:/东方南通/agricultural-news-analysis/data/agricultural_news.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print("Old database cleared")

from config import config; config.ensure_dirs()

# Initialize database
from backend.database import DatabaseManager
from backend.api import create_app, set_db_manager

db = DatabaseManager()
db.conn
set_db_manager(db)

# Crawl real news from all sources
from crawler import AgriculturalNewsCrawler
from nlp import NewsClassifier, NewsSummarizer, SentimentAnalyzer, HotTopicAnalyzer

nc = AgriculturalNewsCrawler()
clf = NewsClassifier()
sa = SentimentAnalyzer()
ha = HotTopicAnalyzer()

all_articles = []
for src in nc.sources:
    articles = nc.crawl_source(src)
    print(src.name + ": " + str(len(articles)) + " articles")
    all_articles.extend(articles)

# NLP processing
if all_articles:
    # Classify
    for a in all_articles:
        result = clf.classify(a.get("title",""), a.get("content",""))
        a["category"] = result["category"]
    
    # Sentiment
    for a in all_articles:
        result = sa.analyze(a.get("title","") + " " + a.get("content",""))
        a["sentiment"] = result["label"]
        a["sentiment_score"] = result["score"]
        a["risk_score"] = result.get("risk_score", 0.0)
    
    # Save to database
    db.save_news(all_articles)
    print(f"Saved {len(all_articles)} articles to database")

    # Run analysis
    articles_from_db = db.get_all_news(500)
    db.save_analysis("full_analysis", ha.full_analysis(articles_from_db))
    db.save_analysis("hot_keywords", {"keywords": ha.extract_keywords(
        [a.get("title","") for a in articles_from_db if a.get("title")], 30)})
    db.save_analysis("trend", {"trend": ha.trend_over_time(articles_from_db)})

# Print stats
stats = db.get_statistics()
print()
print("Database statistics:", json.dumps(stats, ensure_ascii=False, indent=2))
print()

# Start server
import socket
for port in range(8000, 8010):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", port))
        s.close()
        break
    except:
        s.close()
else:
    port = 8000

app = create_app()
import asyncio
from aiohttp import web
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
runner = web.AppRunner(app)
loop.run_until_complete(runner.setup())
site = web.TCPSite(runner, "0.0.0.0", port)
loop.run_until_complete(site.start())

print(f"Server: http://localhost:{port}")
print(f"Dashboard: http://localhost:{port}/dashboard")
print()
loop.run_forever()
