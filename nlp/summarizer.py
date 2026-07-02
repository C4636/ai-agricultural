"""
Summarizer - Extractive text summarizer for Chinese agricultural news
"""
import logging
import re

logger = logging.getLogger(__name__)

class NewsSummarizer:
    """Extractive news summarizer"""

    def __init__(self):
        self._model = None

    def summarize(self, text, max_length=200):
        if not text or len(text) < 50:
            return text or ""

        sentences = re.split(r"[。！？!?]", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not sentences:
            return text[:max_length]

        keywords = ["预警", "预计", "影响", "提醒", "注意", "建议", "同比",
                     "增长", "下降", "报告", "发布", "通知", "重要"]

        scored = []
        for s in sentences:
            score = sum(1 for kw in keywords if kw in s)
            if any(c.isdigit() for c in s):
                score += 0.5
            scored.append((score, s))

        scored.sort(reverse=True)
        result = []
        total_len = 0
        for _, s in scored:
            if total_len + len(s) > max_length and result:
                break
            result.append(s)
            total_len += len(s)

        summary = "。".join(result)
        if len(summary) > max_length:
            summary = summary[:max_length]
        return summary

    def summarize_batch(self, articles, max_length=200):
        for article in articles:
            if article.get("content"):
                article["summary"] = self.summarize(article["content"], max_length)
        return articles
