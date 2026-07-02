from dataclasses import dataclass

@dataclass
class NewsSource:
    name: str
    url: str
    encoding: str = "utf-8"
    article_selector: str = ""
    title_selector: str = "a"
    date_selector: str = ""
    page_start: int = 1

@dataclass  
class DisasterSource:
    name: str
    url: str
    encoding: str = "utf-8"
    region: str = ""
    selector: str = ""

# === 农业新闻源（实测可用）===
NEWS_SOURCES = [
    NewsSource(name="农信网-要闻", url="https://www.agri.cn/",
               article_selector="div.news_content a[href*=nyyw]",
               title_selector="",
               date_selector="span.time"),
    NewsSource(name="农信网-生产", url="https://www.agri.cn/",
               article_selector="div.sc_box_list a[href*=scdt]",
               title_selector="",
               date_selector="span.time"),
    NewsSource(name="农信网-气象", url="https://www.agri.cn/",
               article_selector="div.sc_box_list a[href*=nyqx]",
               title_selector="",
               date_selector="span.time"),
    NewsSource(name="农业农村部", url="http://www.moa.gov.cn/xw/zwdt/",
               article_selector="li.ztlb",
               title_selector="a",
               date_selector="span"),
]

DISASTER_SOURCES = [
    DisasterSource(name="中国天气网灾害预警", url="http://www.weather.com.cn/alarm/",
                   region="全国", selector="ul.alarm-list li"),
]