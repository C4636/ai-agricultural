"""
农业新闻爬虫 - 使用 urllib + lxml
"""
import hashlib, json, random, re, time, logging, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, quote

from lxml import html as lxml_html

from config import config
from .sources import NewsSource, NEWS_SOURCES

logger = logging.getLogger(__name__)


def safe_url(url):
    """对URL中的中文进行百分号编码"""
    return quote(url, safe=":/?#[]@!$&'()*+,;=-_.~%")


class AgriculturalNewsCrawler:
    def __init__(self, sources=None):
        self.sources = sources or NEWS_SOURCES
        self.raw_dir = config.RAW_DIR / "news"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _request(self, url):
        for attempt in range(config.MAX_RETRIES):
            try:
                req = urllib.request.Request(
                    safe_url(url),
                    headers={"User-Agent": config.USER_AGENT,
                             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
                )
                with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as resp:
                    html_bytes = resp.read()
                    ct = resp.headers.get("Content-Type", "")
                    enc = "utf-8"
                    if "charset=" in ct:
                        enc = ct.split("charset=")[-1].split(";")[0].strip()
                    return html_bytes.decode(enc, errors="replace")
            except Exception as e:
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.REQUEST_DELAY * (attempt + 1))
                    continue
                logger.warning(f"请求失败: {url} - {e}")
                return None

    def _extract_content(self, url):
        html = self._request(url)
        if not html:
            return ""
        try:
            doc = lxml_html.fromstring(html)
        except Exception:
            return ""
        for tag in doc.xpath("//script|//style|//nav|//footer"):
            if tag.getparent() is not None:
                tag.getparent().remove(tag)
        for xp in ["//div[contains(@class,'article-content')]",
                    "//div[contains(@class,'content')]",
                    "//div[contains(@class,'text')]",
                    "//article", "//div[@id='content']"]:
            els = doc.xpath(xp)
            if els:
                return "\n".join(els[0].text_content().split())
        ps = doc.xpath("//p")
        texts = [p.text_content().strip() for p in ps if len(p.text_content().strip()) > 20]
        return "\n".join(texts[:20]) if texts else ""

    def _parse_date(self, s):
        if not s:
            return datetime.now().strftime("%Y-%m-%d")
        s = s.strip()
        now = datetime.now()
        # Use actual Chinese chars, NOT \uXXXX escapes (those don't work in raw strings)
        pats = [
            # "2026-07-01" or "2026年07月01日"
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", r"\1-\2-\3"),
            (r"(\d{4})年(\d{1,2})月(\d{1,2})日?", r"\1-\2-\3"),
            # "07-02" (short date), "07月02日"
            (r"(\d{1,2})-(\d{1,2})", lambda m: f"{now.year}-{m.group(1)}-{m.group(2)}"),
            (r"(\d{1,2})月(\d{1,2})日?", lambda m: f"{now.year}-{m.group(1)}-{m.group(2)}"),
            # "今天", "昨天"
            ("今天", lambda _: now.strftime("%Y-%m-%d")),
            ("昨天", lambda _: (now.replace(day=now.day-1)).strftime("%Y-%m-%d")),
        ]
        for pat, rep in pats:
            if re.search(pat, s):
                try:
                    return re.sub(pat, rep, s, count=1)
                except Exception:
                    continue
        return now.strftime("%Y-%m-%d")

    def _gen_id(self, url, title):
        return hashlib.md5(f"{url}_{title}".encode("utf-8", errors="replace")).hexdigest()

    def crawl_source(self, source):
        articles = []
        html = self._request(source.url)
        if not html:
            return articles
        try:
            doc = lxml_html.fromstring(html)
        except Exception as e:
            logger.warning(f"HTML parse error: {e}")
            return articles
        items = doc.cssselect(source.article_selector) if source.article_selector else doc.xpath("//li")
        for item in items[:config.MAX_NEWS_PER_SOURCE]:
            try:
                el = None
                if source.title_selector:
                    found = item.cssselect(source.title_selector)
                    if found: el = found[0]
                elif item.tag == "a":
                    el = item
                elif item.xpath(".//a"):
                    el = item.xpath(".//a")[0]
                if el is None:
                    continue
                title = el.text_content().strip()
                link = el.get("href", "")
                # Skip nav links (短文本/关键词)
                if not title or len(title) < 5 or title in ["农业要闻","中心动态","全国信息联播","通知公告","更多","首页","机构","资讯","数据","生产","信息化","专题","视频"]:
                    continue
                if link and not link.startswith("http"):
                    link = urljoin(source.url, link)
                ds = ""
                if source.date_selector:
                    de = item.cssselect(source.date_selector)
                    if de:
                        ds = de[0].text_content().strip()
                articles.append({
                    "id": self._gen_id(link, title),
                    "title": title, "url": link,
                    "source": source.name,
                    "date": self._parse_date(ds),
                    "content": "", "summary": "",
                    "category": "", "sentiment": "",
                    "sentiment_score": 0.5, "risk_score": 0.0,
                    "crawled_at": datetime.now().isoformat(),
                })
            except Exception:
                continue
        for a in articles:
            # Use title as summary (skip content fetching for speed)
            a["content"] = a["title"]
            a["summary"] = a["title"]
        logger.info(f"{source.name}: {len(articles)} articles")
        return articles

    def crawl_all(self):
        all_articles = []
        for src in self.sources:
            all_articles.extend(self.crawl_source(src))
            time.sleep(config.REQUEST_DELAY)
        seen = set()
        uniq = []
        for a in all_articles:
            if a["id"] not in seen:
                seen.add(a["id"])
                uniq.append(a)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = self.raw_dir / f"news_{ts}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(uniq, f, ensure_ascii=False, indent=2)
        logger.info(f"Crawl done: {len(uniq)} articles")
        return uniq
