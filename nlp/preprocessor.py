"""
文本预处理模块 - 基于规则的简单中文分词
"""
import re
import logging

logger = logging.getLogger(__name__)

STOP_WORDS = set("的了是在有我一个人不这就为能被也都和与他对此而但没或以于之因为所以可以没有这些那个什么怎么已经还是之后关于如果只是通过应该需要虽然可能不过")

class TextPreprocessor:
    """文本预处理器 - 无需jieba的简易版本"""

    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        # 只保留中英文、数字、基础标点
        text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9,.!?;:\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text):
        """基于字符二元组 + 空格分隔的简单分词"""
        if not text:
            return []
        # 按空格和标点分割
        words = re.split(r"[\s,.!?;:，。！？；：、()（）\[\]【】]+", text)
        tokens = []
        for w in words:
            if not w:
                continue
            if re.match(r"^[\u4e00-\u9fff]+$", w):
                # 中文：使用二元分词（相邻字符组合）
                for i in range(len(w) - 1):
                    tokens.append(w[i:i+2])
            elif len(w) > 1:
                tokens.append(w)
        return tokens

    def remove_stopwords(self, tokens):
        return [t for t in tokens if t not in STOP_WORDS and len(t.strip()) > 1]

    def preprocess(self, text):
        text = self.clean_text(text)
        tokens = self.tokenize(text)
        tokens = self.remove_stopwords(tokens)
        return " ".join(tokens)
