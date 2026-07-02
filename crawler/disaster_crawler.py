"""
灾害预警爬虫 - 基于 urllib + lxml
"""
import hashlib, json, time, logging, urllib.request, urllib.error
from datetime import datetime
from urllib.parse import quote
from lxml import html as lxml_html

from config import config
from .sources import DISASTER_SOURCES

logger = logging.getLogger(__name__)


def safe_url(url):
    return quote(url, safe=":/?#[]@!$&'()*+,;=-_.~%")


class DisasterWarningCrawler:
    def __init__(self, sources=None):
        self.sources = sources or DISASTER_SOURCES
        self.raw_dir = config.RAW_DIR / "disasters"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _request(self, url):
        for attempt in range(config.MAX_RETRIES):
            try:
                req = urllib.request.Request(safe_url(url), headers={"User-Agent": config.USER_AGENT})
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

    def _parse_alert_level(self, text):
        levels = {"红色": 1, "橙色": 2, "黄色": 3, "蓝色": 4}
        for name, val in sorted(levels.items(), key=lambda x: x[1]):
            if name in text:
                return name, val
        return "未知", 99

    def _detect_type(self, text):
        for dt in ["风暴", "雨涝", "冰雹", "降温", "干旱", "地震"]:
            if dt in text:
                return dt
        return "未知"

    def _calc_risk(self, text):
        score = sum(w for kw, w in {"级":0.5,"预警":0.3,"强降雨":0.4,"大风":0.4,"冰雹":0.5,"降温":0.3}.items() if kw in text)
        return min(score, 1.0)

    def crawl_disaster_warnings(self):
        warnings = []
        for src in self.sources:
            logger.info(f"Crawl: {src.name}")
            html = self._request(src.url)
            if not html:
                continue
            try:
                doc = lxml_html.fromstring(html)
            except Exception:
                continue
            items = doc.cssselect(src.selector) if src.selector else doc.xpath("//li")
            for item in items[:config.MAX_NEWS_PER_SOURCE]:
                try:
                    text = item.text_content().strip()
                    if len(text) < 10:
                        continue
                    lvl_name, lvl_val = self._parse_alert_level(text)
                    a = item.xpath(".//a")
                    url = a[0].get("href", "") if a else ""
                    warnings.append({
                        "id": hashlib.md5(text[:100].encode("utf-8", errors="replace")).hexdigest(),
                        "source": src.name, "region": src.region,
                        "title": text[:120], "url": url,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "alert_level": lvl_name, "severity": lvl_val,
                        "disaster_type": self._detect_type(text),
                        "risk_score": self._calc_risk(text),
                        "description": text[:500],
                        "crawled_at": datetime.now().isoformat(),
                    })
                except Exception:
                    continue
            time.sleep(config.REQUEST_DELAY)
        if warnings:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            p = self.raw_dir / f"disasters_{ts}.json"
            with open(p, "w", encoding="utf-8") as f:
                json.dump(warnings, f, ensure_ascii=False, indent=2)
        logger.info(f"Done: {len(warnings)} warnings")
        return warnings

    def get_active_warnings(self):
        return self.crawl_disaster_warnings()
