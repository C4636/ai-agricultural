"""
数据库模块 - 添加搜索、日期筛选、市场数据
"""
import json, sqlite3, logging, re
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = str(config.DB_DIR / "agricultural_news.db")
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._init_tables()
        return self._conn

    def _init_tables(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id TEXT PRIMARY KEY, title TEXT, url TEXT, source TEXT,
                date TEXT, content TEXT, summary TEXT,
                category TEXT DEFAULT '综合资讯',
                sentiment TEXT DEFAULT 'neutral',
                sentiment_score REAL DEFAULT 0.5,
                risk_score REAL DEFAULT 0.0, crawled_at TEXT
            );
            CREATE TABLE IF NOT EXISTS disaster_warnings (
                id TEXT PRIMARY KEY, source TEXT, region TEXT, title TEXT,
                url TEXT, date TEXT, alert_level TEXT, severity INTEGER DEFAULT 99,
                disaster_type TEXT, risk_score REAL DEFAULT 0.0, description TEXT, crawled_at TEXT
            );
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT, result_json TEXT, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, url TEXT, category TEXT,
                date TEXT, content TEXT, crawled_at TEXT
            );
        """)
        self.conn.commit()

    def save_news(self, articles):
        c = self.conn.cursor()
        count = 0
        for a in articles:
            try:
                c.execute("INSERT OR IGNORE INTO news_articles VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (a["id"], a.get("title",""), a.get("url",""), a.get("source",""),
                     a.get("date",""), a.get("content",""), a.get("summary",""),
                     a.get("category","综合资讯"), a.get("sentiment","neutral"),
                     a.get("sentiment_score",0.5), a.get("risk_score",0.0), ""))
                if c.rowcount > 0: count += 1
            except Exception as e:
                logger.error(f"保存新闻失败: {e}")
        self.conn.commit()
        return count

    def save_disasters(self, warnings):
        c = self.conn.cursor()
        count = 0
        for w in warnings:
            try:
                c.execute("INSERT OR IGNORE INTO disaster_warnings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (w["id"], w.get("source",""), w.get("region",""), w.get("title",""),
                     w.get("url",""), w.get("date",""), w.get("alert_level","未知"),
                     w.get("severity",99), w.get("disaster_type","未知"), w.get("risk_score",0.0),
                     w.get("description",""), ""))
                if c.rowcount > 0: count += 1
            except: pass
        self.conn.commit()
        return count

    def save_market_data(self, items):
        c = self.conn.cursor()
        count = 0
        for item in items:
            try:
                c.execute("INSERT OR IGNORE INTO market_data (title, url, category, date, content, crawled_at) VALUES (?,?,?,?,?,?)",
                    (item.get("title",""), item.get("url",""), item.get("category",""),
                     item.get("date",""), item.get("content",""), datetime.now().isoformat()))
                if c.rowcount > 0: count += 1
            except: pass
        self.conn.commit()
        return count

    def save_analysis(self, analysis_type, result):
        c = self.conn.cursor()
        c.execute("INSERT INTO analysis_results (analysis_type, result_json, created_at) VALUES (?,?,?)",
            (analysis_type, json.dumps(result, ensure_ascii=False), datetime.now().isoformat()))
        self.conn.commit()

    def get_all_news(self, limit=100, offset=0, category=None):
        c = self.conn.cursor()
        if category:
            c.execute("SELECT * FROM news_articles WHERE category=? ORDER BY date DESC LIMIT ? OFFSET ?", (category, limit, offset))
        else:
            c.execute("SELECT * FROM news_articles ORDER BY date DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(r) for r in c.fetchall()]

    def search_news(self, keyword, limit=50):
        """按关键词搜索新闻标题"""
        c = self.conn.cursor()
        like = f"%{keyword}%"
        c.execute("SELECT * FROM news_articles WHERE title LIKE ? ORDER BY date DESC LIMIT ?", (like, limit))
        return [dict(r) for r in c.fetchall()]

    def get_news_by_date_range(self, start_date, end_date, limit=200):
        """按日期范围筛选"""
        c = self.conn.cursor()
        c.execute("SELECT * FROM news_articles WHERE date >= ? AND date <= ? ORDER BY date DESC LIMIT ?",
            (start_date, end_date, limit))
        return [dict(r) for r in c.fetchall()]

    def get_news_by_keyword_and_date(self, keyword, start_date=None, end_date=None, limit=50):
        """关键词+日期组合筛选"""
        c = self.conn.cursor()
        like = f"%{keyword}%"
        if start_date and end_date:
            c.execute("SELECT * FROM news_articles WHERE title LIKE ? AND date >= ? AND date <= ? ORDER BY date DESC LIMIT ?",
                (like, start_date, end_date, limit))
        else:
            c.execute("SELECT * FROM news_articles WHERE title LIKE ? ORDER BY date DESC LIMIT ?", (like, limit))
        return [dict(r) for r in c.fetchall()]

    def get_sentiment_summary(self, start_date=None, end_date=None):
        """获取情感摘要统计"""
        c = self.conn.cursor()
        if start_date and end_date:
            c.execute("SELECT COUNT(*), AVG(sentiment_score), SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END), SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) FROM news_articles WHERE date >= ? AND date <= ?", (start_date, end_date))
        else:
            c.execute("SELECT COUNT(*), AVG(sentiment_score), SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END), SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) FROM news_articles")
        row = c.fetchone()
        total = row[0] or 0
        avg = row[1] or 0.5
        pos = row[2] or 0
        neg = row[3] or 0
        score = round(avg * 10, 1)
        label = "正向" if score >= 7 else ("负向" if score <= 4 else "中性")
        return {"total": total, "positive": pos, "negative": neg, "avg_score": avg, "score_10": score, "label": label}

    def get_market_data(self, limit=30):
        c = self.conn.cursor()
        c.execute("SELECT * FROM market_data ORDER BY date DESC LIMIT ?", (limit,))
        return [dict(r) for r in c.fetchall()]

    def get_active_disasters(self, limit=50):
        c = self.conn.cursor()
        c.execute("SELECT * FROM disaster_warnings ORDER BY severity ASC LIMIT ?", (limit,))
        return [dict(r) for r in c.fetchall()]

    def get_recent_analysis(self, analysis_type, limit=1):
        c = self.conn.cursor()
        c.execute("SELECT * FROM analysis_results WHERE analysis_type=? ORDER BY created_at DESC LIMIT ?", (analysis_type, limit))
        results = []
        for r in c.fetchall():
            d = dict(r)
            d["result"] = json.loads(d.get("result_json", "{}"))
            results.append(d["result"])
        return results

    def get_statistics(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM news_articles"); tn = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM disaster_warnings"); td = c.fetchone()[0]
        c.execute("SELECT category, COUNT(*) FROM news_articles GROUP BY category")
        cats = {r[0]: r[1] for r in c.fetchall()}
        return {"total_news": tn, "total_disasters": td, "category_counts": cats}

    def clear_demo_data(self):
        """清除所有演示数据，保留真实爬虫数据"""
        c = self.conn.cursor()
        c.execute("DELETE FROM news_articles WHERE source='demo'")
        c.execute("DELETE FROM disaster_warnings WHERE id LIKE 'w%'")
        c.execute("DELETE FROM analysis_results")
        self.conn.commit()
        logger.info("Demo data cleared.")

    def close(self):
        if self._conn: self._conn.close(); self._conn = None