import sys, json, time, socket, urllib.request
sys.path.insert(0, "E:/东方南通/agricultural-news-analysis")

import os
db_path = "E:/东方南通/agricultural-news-analysis/data/agricultural_news.db"
if os.path.exists(db_path):
    os.remove(db_path)
print("Fresh start...")

from config import config; config.ensure_dirs()
from backend.database import DatabaseManager
from backend.api import create_app, set_db_manager
from crawler import AgriculturalNewsCrawler
from nlp import NewsClassifier, NewsSummarizer, SentimentAnalyzer, HotTopicAnalyzer

db = DatabaseManager(); db.conn; set_db_manager(db)
clf = NewsClassifier(); sa = SentimentAnalyzer(); ha = HotTopicAnalyzer()

# Crawl headlines only (fast)
nc = AgriculturalNewsCrawler()
all_articles = []
for src in nc.sources:
    try:
        articles = nc.crawl_source(src)
        all_articles.extend(articles)
        print(f"  {src.name}: {len(articles)} articles")
    except Exception as e:
        print(f"  {src.name}: error - {str(e)[:50]}")

# Classify + sentiment
for a in all_articles:
    r1 = clf.classify(a.get("title",""))
    a["category"] = r1["category"]
    r2 = sa.analyze(a.get("title",""))
    a["sentiment"] = r2["label"]
    a["sentiment_score"] = r2["score"]
    a["risk_score"] = r2.get("risk_score", 0.0)

db.save_news(all_articles)
print(f"Total: {len(all_articles)} articles saved")

# Analysis
if all_articles:
    arts = db.get_all_news(500)
    db.save_analysis("full_analysis", ha.full_analysis(arts))
    db.save_analysis("hot_keywords", {"keywords": ha.extract_keywords([a.get("title","") for a in arts], 30)})
    db.save_analysis("trend", {"trend": ha.trend_over_time(arts)})

stats = db.get_statistics()
print(f"Stats: {json.dumps(stats, ensure_ascii=False)}")

# Find port
for port in range(8000, 8010):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: s.bind(("0.0.0.0", port)); s.close(); break
    except: s.close()
else: port = 8000

# Start server
import asyncio
from aiohttp import web
app = create_app()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
runner = web.AppRunner(app)
loop.run_until_complete(runner.setup())
site = web.TCPSite(runner, "0.0.0.0", port)
loop.run_until_complete(site.start())

# Test
time.sleep(1)
endpoints = ["/api/health","/api/statistics","/api/news","/api/disasters","/api/analysis","/api/analysis/hot-keywords","/api/analysis/trend","/dashboard"]
for path in endpoints:
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3)
        print(f"[200] {path} ({len(r.read())} bytes)")
    except Exception as e:
        print(f"[FAIL] {path}: {str(e)[:40]}")

print(f"\nAll OK! Dashboard: http://localhost:{port}/dashboard")
loop.run_forever()
