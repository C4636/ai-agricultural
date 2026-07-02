"""API路由 - 添加搜索/日期筛选/情感摘要/市场数据端点"""
import json, logging, re
from datetime import datetime
from aiohttp import web
from config import config

logger = logging.getLogger(__name__)
_db_manager = None

def set_db_manager(db):
    global _db_manager; _db_manager = db

def get_db():
    global _db_manager
    if _db_manager is None:
        from backend.database import DatabaseManager
        _db_manager = DatabaseManager(); _db_manager.conn
    return _db_manager

def json_resp(data, status=200):
    return web.json_response(data, status=status, dumps=lambda o: json.dumps(o, ensure_ascii=False, default=str))

async def handle_index(request): return json_resp({"name":"农业新闻分析与预警系统","version":"1.0.0","status":"running"})
async def handle_statistics(request):
    try: return json_resp(get_db().get_statistics())
    except Exception as e: return json_resp({"error":str(e)},500)
async def handle_news(request):
    limit = int(request.query.get("limit","50"))
    offset = int(request.query.get("offset","0"))
    cat = request.query.get("category",None)
    start = request.query.get("start_date",None)
    end = request.query.get("end_date",None)
    kw = request.query.get("keyword",None)
    try:
        if kw: return json_resp(get_db().search_news(kw, limit))
        if start and end: return json_resp(get_db().get_news_by_date_range(start, end, limit))
        return json_resp(get_db().get_all_news(limit, offset, cat))
    except Exception as e: return json_resp({"error":str(e)},500)
async def handle_categories(request):
    return json_resp({"categories":config.CATEGORY_LABELS})
async def handle_disasters(request):
    limit = int(request.query.get("limit","50"))
    try: return json_resp(get_db().get_active_disasters(limit))
    except Exception as e: return json_resp({"error":str(e)},500)
async def handle_analysis(request):
    try:
        results = get_db().get_recent_analysis("full_analysis")
        return json_resp(results[0] if results else {"message":"暂无分析结果"})
    except: return json_resp({"error":"分析失败"},500)
async def handle_keywords(request):
    try:
        results = get_db().get_recent_analysis("hot_keywords")
        data = results[0] if results else {"keywords":[]}
        logger.info(f"[DEBUG] handle_keywords 返回: {{'keywords_count': {len(data.get('keywords',[]))}}}")
        return json_resp(data)
    except Exception as e: return json_resp({"error":str(e)},500)
async def handle_trend(request):
    try:
        results = get_db().get_recent_analysis("trend")
        data = results[0] if results else {"trend":{}}
        trend_keys = list(data.get("trend",{}).keys()) if data.get("trend") else []
        logger.info(f"[DEBUG] handle_trend 返回: {{'trend_dates': {trend_keys}}}")
        return json_resp(data)
    except Exception as e: return json_resp({"error":str(e)},500)
async def handle_sentiment_summary(request):
    """情感摘要 + 综合得分"""
    start = request.query.get("start_date",None)
    end = request.query.get("end_date",None)
    try:
        summary = get_db().get_sentiment_summary(start, end)
        # Add comparison
        summary["analysis"] = f"今日农业舆情综合得分 {summary['score_10']} 分，整体偏向{summary['label']}"
        return json_resp(summary)
    except Exception as e: return json_resp({"error":str(e)},500)
async def handle_market(request):
    """市场数据"""
    try:
        from urllib.parse import urljoin
        from lxml import html as lxml_html
        import urllib.request
        base_url = "https://www.agri.cn/sj/"
        items = []
        with urllib.request.urlopen(urllib.request.Request(base_url, headers={"User-Agent":"Mozilla/5.0"}), timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        doc = lxml_html.fromstring(html)
        for sel in [".trends_list li", ".sj_news_list li", ".dynamic_content_list li"]:
            for item in doc.cssselect(sel):
                a = item.cssselect("a")
                if not a: continue
                title = a[0].text_content().strip()
                href = a[0].get("href","")
                if len(title) > 5:
                    # 用 urljoin 正确解析相对路径
                    items.append({"title":title, "url":urljoin(base_url, href), "source":"农信网-数据"})
        return json_resp({"total":len(items), "items":items[:30]})
    except Exception as e: return json_resp({"error":str(e), "items":[]},200)
async def handle_health(request):
    return json_resp({"status":"healthy","timestamp":datetime.now().isoformat()})
async def handle_dashboard(request):
    tp = config.BASE_DIR / "frontend" / "templates" / "dashboard.html"
    try: return web.Response(text=tp.read_text(encoding="utf-8"), content_type="text/html")
    except: return web.Response(text="Template not found", status=404)


async def handle_weather(request):
    """Weather API using Open-Meteo"""
    import urllib.request, json
    city = request.query.get("city", "")
    cities = {"北京":{"lat":39.90,"lon":116.40},"上海":{"lat":31.23,"lon":121.47},
        "广州":{"lat":23.13,"lon":113.26},"深圳":{"lat":22.54,"lon":114.06},
        "郑州":{"lat":34.75,"lon":113.65},"成都":{"lat":30.57,"lon":104.07},
        "武汉":{"lat":30.59,"lon":114.30},"西安":{"lat":34.26,"lon":108.94},
        "南京":{"lat":32.06,"lon":118.80},"杭州":{"lat":30.27,"lon":120.15},
        "哈尔滨":{"lat":45.80,"lon":126.53}}
    coords = cities.get(city, cities["郑州"])
    coords_str = "&".join([f"latitude={coords['lat']}", f"longitude={coords['lon']}"])
    api_url = "https://api.open-meteo.com/v1/forecast?" + coords_str + "&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum&current_weather=true&timezone=Asia/Shanghai"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = {"city": city, "current": data.get("current_weather",{}), "daily": data.get("daily",{})}
        return json_resp(result)
    except Exception as e:
        return json_resp({"error": str(e), "city": city}, 200)

def _parse_date_from_text(text):
    """从文本中提取日期，支持多种格式"""
    text = text.strip()
    # YYYY-MM-DD 或 YYYY/MM/DD
    m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
    if m: return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # YYYY年MM月DD日
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if m: return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # MM-DD（假设当前年份）
    m = re.search(r'(?<!\d)(\d{1,2})[-/](\d{1,2})(?!\d)', text)
    if m:
        mon, day = int(m.group(1)), int(m.group(2))
        if 1 <= mon <= 12 and 1 <= day <= 31:
            return f"{datetime.now().year}-{mon:02d}-{day:02d}"
    return None

def _parse_date_from_url(url):
    """从URL路径中提取日期，如 /2026/0702/xxx 或 /20260702/xxx"""
    m = re.search(r'/(\d{4})/(\d{2})(\d{2})/', url)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r'/(\d{4})(\d{2})(\d{2})/', url)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None

async def handle_crawl(request):
    """Manual crawl trigger"""
    import urllib.request, hashlib, re
    from urllib.parse import urljoin, quote
    from lxml import html as lxml_html
    from nlp import NewsClassifier, SentimentAnalyzer, HotTopicAnalyzer
    from crawler.sources import NEWS_SOURCES
    # 清除旧数据
    c = get_db().conn.cursor()
    c.execute("DELETE FROM news_articles")
    c.execute("DELETE FROM analysis_results")
    get_db().conn.commit()
    logger.info("已清空旧新闻和旧分析结果，准备重新爬取。")
    clf2 = NewsClassifier(); sa2 = SentimentAnalyzer(); ha2 = HotTopicAnalyzer()
    all_a = []
    today = datetime.now().strftime("%Y-%m-%d")
    for src in NEWS_SOURCES:
        try:
            url2 = quote(src.url, safe=":/?#[]@!$()*+,;=-_.~%")
            req = urllib.request.Request(url2, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            doc = lxml_html.fromstring(html)
            items = doc.cssselect(src.article_selector)
            for item in items[:config.MAX_NEWS_PER_SOURCE]:
                el = None
                if src.date_selector:
                    found = item.cssselect(src.date_selector)
                else:
                    found = item.cssselect('.date, .time, span.date, span.time, em, small')
                date_str = None
                for de in found:
                    dt = _parse_date_from_text(de.text_content())
                    if dt: date_str = dt; break
                if src.title_selector:
                    found = item.cssselect(src.title_selector)
                    if found: el = found[0]
                elif item.tag == "a": el = item
                elif item.xpath(".//a"): el = item.xpath(".//a")[0]
                if el is None: continue
                title = el.text_content().strip()
                link = el.get("href", "")
                if not title or len(title) < 5: continue
                if title in ["农业要闻","中心动态","全国信息联播","通知公告","更多","首页","机构","资讯"]: continue
                if link and not link.startswith("http"): link = urljoin(src.url, link)
                # 尝试从URL提取日期
                if not date_str:
                    date_str = _parse_date_from_url(link)
                all_a.append({"id":hashlib.md5((link+title).encode("utf-8")).hexdigest(),
                    "title":title,"url":link,"source":src.name,
                    "date":date_str or today,
                    "content":"","summary":"","category":"","sentiment":"",
                    "sentiment_score":0.5,"risk_score":0.0,"crawled_at":today})
        except Exception:
            pass
    for a in all_a:
        a["category"] = clf2.classify(a.get("title",""))["category"]
        r2 = sa2.analyze(a.get("title",""))
        a["sentiment"] = r2["label"]; a["sentiment_score"] = r2["score"]; a["risk_score"] = r2.get("risk_score",0.0)
    if all_a:
        saved = get_db().save_news(all_a)
        arts = get_db().get_all_news(500)
        logger.info(f"[DEBUG] 爬取新闻 {len(all_a)} 条, 保存 {saved} 条, 读取 {len(arts)} 条")
        # 检查文章有无日期
        empty_date = [a for a in arts if not a.get("date","")]
        dates_found = sorted(set(a.get("date","")[:10] for a in arts if a.get("date","")))
        logger.info(f"[DEBUG] 空日期文章: {len(empty_date)} 条, 日期分布: {dates_found}")
        # 检查类别分布
        cats_found = {}
        for a in arts:
            c = a.get("category","")
            cats_found[c] = cats_found.get(c,0)+1
        logger.info(f"[DEBUG] 类别分布: {cats_found}")
        # 计算趋势
        trend_data = ha2.trend_over_time(arts)
        logger.info(f"[DEBUG] trend_over_time 结果: {json.dumps(trend_data, ensure_ascii=False)}")
        get_db().save_analysis("full_analysis", ha2.full_analysis(arts))
        get_db().save_analysis("hot_keywords", {"keywords":ha2.extract_keywords([a.get("title","") for a in arts],30)})
        get_db().save_analysis("trend", {"trend":trend_data})
        # 验证保存
        saved_trend = get_db().get_recent_analysis("trend")
        logger.info(f"[DEBUG] 从DB读取趋势数据: {saved_trend[:1] if saved_trend else '空'}")
    return json_resp({"crawled":len(all_a),"total":get_db().get_statistics()["total_news"]})
def create_app():
    app = web.Application()
    app.router.add_get("/", handle_dashboard)
    app.router.add_get("/api/statistics", handle_statistics)
    app.router.add_get("/api/news", handle_news)
    app.router.add_get("/api/news/categories", handle_categories)
    app.router.add_get("/api/disasters", handle_disasters)
    app.router.add_get("/api/analysis", handle_analysis)
    app.router.add_get("/api/analysis/hot-keywords", handle_keywords)
    app.router.add_get("/api/analysis/trend", handle_trend)
    app.router.add_get("/api/analysis/sentiment-summary", handle_sentiment_summary)
    app.router.add_get("/api/market", handle_market)
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/weather", handle_weather)
    app.router.add_get("/api/crawl", handle_crawl)
    app.router.add_get("/dashboard", handle_dashboard)
    sd = str(config.BASE_DIR / "frontend" / "static")
    app.router.add_static("/static/", sd)
    return app