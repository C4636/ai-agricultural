"""数据库模块测试"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config


def test_database_init():
    """测试数据库初始化"""
    # 使用内存数据库测试
    from backend.database import DatabaseManager
    db = DatabaseManager("sqlite:///:memory:")
    db.connect()
    assert db._engine is not None, "引擎应初始化"
    assert db._session is not None, "会话工厂应初始化"


def test_save_and_query_news():
    """测试新闻存储与查询"""
    from backend.database import DatabaseManager
    db = DatabaseManager("sqlite:///:memory:")
    db.connect()

    articles = [{
        "id": "test001",
        "title": "测试新闻标题",
        "url": "https://example.com/news/1",
        "source": "测试源",
        "date": "2024-01-15",
        "content": "这是一条测试新闻内容",
        "summary": "测试摘要",
        "category": "政策法规",
        "sentiment": "positive",
        "sentiment_score": 0.8,
        "risk_score": 0.1,
    }]
    count = db.save_news(articles)
    assert count == 1, "应保存1条记录"

    results = db.get_all_news()
    assert len(results) == 1, "应查询到1条记录"
    assert results[0]["title"] == "测试新闻标题"


def test_statistics():
    """测试统计功能"""
    from backend.database import DatabaseManager
    db = DatabaseManager("sqlite:///:memory:")
    db.connect()
    stats = db.get_statistics()
    assert "total_news" in stats
    assert "total_disasters" in stats
    assert "category_counts" in stats


if __name__ == "__main__":
    print("数据库测试:")
    test_database_init()
    test_save_and_query_news()
    test_statistics()
    print("\n所有数据库测试通过!")
