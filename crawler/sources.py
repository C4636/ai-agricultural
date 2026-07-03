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
    page_url_template: str = ""  # 分页模板，如 "https://www.agri.cn/zx/nyyw/index_{page}.html"

@dataclass  
class DisasterSource:
    name: str
    url: str
    encoding: str = "utf-8"
    region: str = ""
    selector: str = ""

# === 农业新闻源（实测可用）===
# 使用更通用的选择器，匹配多种常见的列表页HTML结构
NEWS_SOURCES = [
    # ===== 农信网首页精选（各栏目最新文章） =====
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

    # ===== 农信网栏目列表页（带分页，获取大量历史文章） =====
    # 使用通用选择器 ul li 匹配列表结构
    NewsSource(name="农信网-要闻列表", url="https://www.agri.cn/zx/nyyw/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.agri.cn/zx/nyyw/index_{page}.html"),
    NewsSource(name="农信网-生产列表", url="https://www.agri.cn/sc/scdt/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.agri.cn/sc/scdt/index_{page}.html"),
    NewsSource(name="农信网-气象列表", url="https://www.agri.cn/sc/nyqx/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.agri.cn/sc/nyqx/index_{page}.html"),
    NewsSource(name="农信网-通知公告", url="https://www.agri.cn/zx/tzgg/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.agri.cn/zx/tzgg/index_{page}.html"),
    NewsSource(name="农信网-全国联播", url="https://www.agri.cn/zx/qqxw/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.agri.cn/zx/qqxw/index_{page}.html"),

    # ===== 农业农村部 =====
    NewsSource(name="农业农村部", url="http://www.moa.gov.cn/xw/zwdt/",
               article_selector="li.ztlb",
               title_selector="a",
               date_selector="span"),

    # ===== 新增数据源：新华网三农频道 =====
    NewsSource(name="新华网-三农", url="http://www.xinhuanet.com/politics/sannong/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span"),

    # ===== 新增数据源：中国农业信息网 =====
    NewsSource(name="中国农业信息网", url="http://www.agri.cn/",
               article_selector="a[href*=nyyw], a[href*=scdt], a[href*=nyqx]",
               title_selector="",
               date_selector="span.time"),

    # ===== 中国气象网 - 农业气象专栏 =====
    # 每日发布农业专项预警、农田渍涝、春播冻害、秋收连阴雨风险等
    NewsSource(name="中国气象网-农业气象", url="https://www.cma.gov.cn/2011xwzx/2011xqxxw/2011xqxyw/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.cma.gov.cn/2011xwzx/2011xqxxw/2011xqxyw/index_{page}.html"),
    NewsSource(name="中国气象网-气象要闻", url="https://www.cma.gov.cn/2011xwzx/2011xqxxw/2011xqxyw/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.cma.gov.cn/2011xwzx/2011xqxxw/2011xqqxw/index_{page}.html"),

    # ===== 中国水利部 - 防汛抗旱/水旱灾害 =====
    # 江河洪水、涝灾、农田积水灾情通报、防汛抗旱预警
    NewsSource(name="水利部-防汛抗旱", url="http://www.mwr.gov.cn/xw/slyw/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="http://www.mwr.gov.cn/xw/slyw/index_{page}.html"),
    NewsSource(name="水利部-水旱灾害", url="http://www.mwr.gov.cn/zwjg/zwxx/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="http://www.mwr.gov.cn/zwjg/zwxx/index_{page}.html"),

    # ===== 自然资源部 - 地质灾害 =====
    # 滑坡、泥石流等山地农田灾害预警、地质灾害涉农灾情报道
    NewsSource(name="自然资源部-要闻", url="https://www.mnr.gov.cn/dt/yw/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.mnr.gov.cn/dt/yw/index_{page}.html"),
    NewsSource(name="自然资源部-灾害防控", url="https://www.mnr.gov.cn/dt/zhfp/",
               article_selector="ul li",
               title_selector="a",
               date_selector="span",
               page_url_template="https://www.mnr.gov.cn/dt/zhfp/index_{page}.html"),
]

DISASTER_SOURCES = [
    DisasterSource(name="中国天气网灾害预警", url="http://www.weather.com.cn/alarm/",
                   region="全国", selector="ul.alarm-list li"),
    # 中国气象网 - 气象灾害预警
    DisasterSource(name="中国气象网-灾害预警", url="https://www.cma.gov.cn/2011xwzx/2011xqxxw/2011xyj/",
                   region="全国", selector="ul li"),
    # 水利部 -  flood warnings
    DisasterSource(name="水利部-水旱灾害防御", url="http://www.mwr.gov.cn/xw/slyw/",
                   region="全国", selector="ul li"),
    # 自然资源部 - 地质灾害预警
    DisasterSource(name="自然资源部-地质灾害", url="https://www.mnr.gov.cn/dt/zhfp/",
                   region="全国", selector="ul li"),
]