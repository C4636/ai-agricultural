"""NLP模块测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SAMPLE_NEWS = {
    "title": "农业农村部发布2024年乡村振兴重点工作通知",
    "content": "农业农村部近日发布通知，要求各地扎实推进乡村振兴战略。通知强调要加强耕地保护，推进农业科技创新，提高粮食安全保障能力。各地要结合实际制定实施方案，确保各项政策措施落地见效。",
}
DISASTER_NEWS = {
    "title": "中央气象台发布暴雨红色预警：多地将迎强降雨",
    "content": "中央气象台今日发布暴雨红色预警，预计未来24小时华北地区将出现大范围强降雨天气，局部地区降雨量可达200毫米以上。农业部门提醒各地做好农田排涝准备，防范洪涝灾害对农作物造成的影响。",
}


def test_preprocessor():
    """测试文本预处理"""
    from nlp.preprocessor import TextPreprocessor
    tp = TextPreprocessor()
    cleaned = tp.clean_text(SAMPLE_NEWS["content"])
    assert len(cleaned) > 0, "清洗后的文本不应为空"
    tokens = tp.tokenize(cleaned)
    assert len(tokens) > 0, "分词结果不应为空"
    filtered = tp.remove_stopwords(tokens)
    assert len(filtered) > 0, "去停用词后不应为空"
    print(f"  预处理: {len(tokens)}词 -> {len(filtered)}关键词")


def test_classifier():
    """测试新闻分类器"""
    from nlp.classifier import NewsClassifier
    clf = NewsClassifier()
    # 测试政策类新闻
    result = clf.classify(SAMPLE_NEWS["title"], SAMPLE_NEWS["content"])
    assert result["category"] in ["政策法规", "综合资讯"], f"分类结果异常: {result['category']}"
    print(f"  分类结果: {result['category']}")
    # 测试灾害类新闻
    result2 = clf.classify(DISASTER_NEWS["title"], DISASTER_NEWS["content"])
    assert result2["category"] in ["灾害预警", "综合资讯"], f"分类结果异常: {result2['category']}"
    print(f"  灾害分类: {result2['category']}")


def test_summarizer():
    """测试摘要生成器"""
    from nlp.summarizer import NewsSummarizer
    sm = NewsSummarizer()
    summary = sm.summarize(SAMPLE_NEWS["content"], max_length=100)
    assert len(summary) > 0, "摘要不应为空"
    assert len(summary) <= len(SAMPLE_NEWS["content"]), "摘要不应超过原文"
    print(f"  摘要: {summary[:50]}...")


def test_sentiment():
    """测试情感分析"""
    from nlp.sentiment import SentimentAnalyzer
    sa = SentimentAnalyzer()
    # 正面新闻
    result = sa.analyze(SAMPLE_NEWS["title"] + SAMPLE_NEWS["content"])
    assert "label" in result, "情感分析应返回label"
    assert "risk_score" in result, "应返回风险分数"
    print(f"  情感: {result['label']}, 风险: {result['risk_score']:.2f}")
    # 灾害新闻
    result2 = sa.analyze(DISASTER_NEWS["title"] + DISASTER_NEWS["content"])
    print(f"  灾害情感: {result2['label']}, 风险: {result2['risk_score']:.2f}")


def test_analyzer():
    """测试热点分析器"""
    from nlp.analyzer import HotTopicAnalyzer
    ha = HotTopicAnalyzer()
    articles = [
        {**SAMPLE_NEWS, "category": "政策法规", "sentiment": "positive", "date": "2024-01-15"},
        {**DISASTER_NEWS, "category": "灾害预警", "sentiment": "negative", "date": "2024-01-16"},
    ]
    dist = ha.category_distribution(articles)
    assert "政策法规" in dist, "分类统计应包含政策法规"
    sentiment_dist = ha.sentiment_distribution(articles)
    assert "positive" in sentiment_dist, "情感统计应包含positive"
    keywords = ha.extract_keywords([a["title"] for a in articles], top_k=5)
    assert len(keywords) > 0, "应提取到关键词"
    trend = ha.trend_over_time(articles)
    assert "2024-01-15" in trend or "2024-01-16" in trend, "趋势分析应有日期"
    print(f"  关键词: {[k['word'] for k in keywords[:3]]}")


if __name__ == "__main__":
    print("NLP模块测试:")
    test_preprocessor()
    test_classifier()
    test_summarizer()
    test_sentiment()
    test_analyzer()
    print("\n所有NLP测试通过!")
