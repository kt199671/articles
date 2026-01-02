"""AI-powered research article generation for coworking space research."""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass

import google.generativeai as genai
from tavily import TavilyClient

from .config import (
    SEARCH_QUERIES,
    TARGET_CHAR_COUNT_MIN,
    TARGET_CHAR_COUNT_MAX,
    SECTIONS_MIN,
    SECTIONS_MAX,
    GEMINI_TIMEOUT,
    TAVILY_TIMEOUT,
)


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result from Tavily."""
    title: str
    url: str
    content: str
    score: float
    published_date: str


@dataclass
class ResearchData:
    """Aggregated research data."""
    results: List[SearchResult]
    query_count: int
    total_results: int


class ValidationResult:
    """Article validation result."""
    def __init__(self, valid: bool, errors: List[str], warnings: List[str]):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings


class CoworkingResearchLabWriter:
    """
    AI-powered writer for academic-style coworking space research articles.

    Uses Tavily for research and Google Gemini for article generation.
    """

    def __init__(self):
        """Initialize writer with API clients."""
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-3-flash-preview')

        self.tavily_client = TavilyClient(
            api_key=os.getenv("TAVILY_API_KEY")
        )

    def gather_research_data(self, days: int = 30) -> ResearchData:
        """
        Search for latest coworking space research using Tavily.

        Args:
            days: Number of days to look back (default: 30 for research)

        Returns:
            ResearchData object with aggregated results
        """
        logger.info(f"Gathering research data from the past {days} days...")

        all_results: List[SearchResult] = []

        for query in SEARCH_QUERIES:
            logger.info(f"Searching: {query}")

            try:
                response = self.tavily_client.search(
                    query=query,
                    max_results=7,
                    days=days,
                    search_depth="advanced"
                )

                # Parse results
                for result in response.get("results", []):
                    search_result = SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        score=result.get("score", 0.0),
                        published_date=result.get("published_date", "")
                    )
                    all_results.append(search_result)

            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue

        # Deduplicate by URL
        unique_results = self._deduplicate_results(all_results)

        # Sort by score (relevance)
        unique_results.sort(key=lambda x: x.score, reverse=True)

        # Take top 20 results for research depth
        top_results = unique_results[:20]

        logger.info(f"Found {len(top_results)} unique results from {len(SEARCH_QUERIES)} queries")

        return ResearchData(
            results=top_results,
            query_count=len(SEARCH_QUERIES),
            total_results=len(top_results)
        )

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Deduplicate results by URL.

        Args:
            results: List of search results

        Returns:
            Deduplicated list
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results

    def generate_article(self, research_data: ResearchData, week_number: str) -> str:
        """
        Generate academic-style article using Google Gemini based on research data.

        Args:
            research_data: Research data from gather_research_data
            week_number: Week number string (e.g., "2026年01週")

        Returns:
            Article text in markdown format
        """
        logger.info("Generating academic research article with Google Gemini 3.0 Flash...")

        prompt = f"""あなたはコワーキングスペースに関する専門研究者です。過去1ヶ月の最新研究・トレンド・調査結果を基に、note投稿用の学術的な研究記事（Markdown形式）を執筆してください。

【記事の特徴】
・対象マガジン：「コワーキングの場づくり研究室」
・文字数：5,000〜8,000文字
・トーン：学術的・専門的、しかし読みやすい
・構成：序論・本論（5-7章）・結論
・参考文献：各章で言及した研究や記事の出典を明記

【執筆スタイルのガイドライン】
1. 客観的なデータ・研究に基づく論述
2. 概念の深い掘り下げ（サードプレイス、ウェルビーイング、ハイブリッドワークなど）
3. 社会学・心理学・経営学などの学際的アプローチ
4. 実践的な示唆・提言を含む
5. 絵文字は一切使用しない
6. 自然な文体で、AIが書いたとわからないようにする

【記事構成の例】
```
# [タイトル]：コワーキングスペースに関する学術的・実践的なテーマ

## 1. はじめに：問題提起
- 現代社会における働き方の変化
- 本記事で扱うテーマの重要性

## 2-7. 本論（各章2-3の小見出し）
例：
- サードプレイスの概念と現代的意義
- ハイブリッドワーク環境におけるウェルビーイング
- コミュニティ形成のメカニズム
- 空間デザインと生産性の関係
- グローバルトレンドと日本の状況
- 実践事例の分析

## 8. 結論：まとめと提言
- 主要な発見のまとめ
- 運営者・利用者・社会への提言

## 参考文献
- 各章で言及した研究・記事・データソースのリスト
```

【重要な注意事項】
- 既存の研究記事のように深い考察を行う
- 単なるニュースまとめではなく、テーマを掘り下げた論考とする
- 具体的なデータ・統計・研究結果を積極的に引用する
- 各主張には根拠を示す
- 絵文字は絶対に使用しない
- 自然で説得力のある文章構成

---

以下のリサーチデータを基に、最も重要かつ興味深いテーマを1つ選定し、それについての学術的研究記事を執筆してください。
複数のデータソースを統合し、独自の視点で分析・考察を加えてください。

【リサーチデータ】
{self._format_research_data(research_data)}

【出力形式】
上記の構成に従って、Markdown形式で学術的な研究記事を出力してください。
"""

        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 8000,
                }
            )

            article = response.text

            logger.info(f"Article generated ({len(article)} characters)")
            return article

        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            raise

    def _format_research_data(self, research_data: ResearchData) -> str:
        """
        Format research data for prompt.

        Args:
            research_data: Research data to format

        Returns:
            Formatted string
        """
        formatted = []

        for i, result in enumerate(research_data.results, 1):
            formatted.append(f"""
【データソース {i}】
タイトル: {result.title}
URL: {result.url}
公開日: {result.published_date}
関連度: {result.score:.2f}
内容:
{result.content[:800]}...
""")

        return "\n".join(formatted)

    def validate_article(self, article_md: str) -> ValidationResult:
        """
        Validate generated article meets requirements.

        Args:
            article_md: Article markdown text

        Returns:
            ValidationResult object
        """
        char_count = len(article_md)
        sections = article_md.count("## ")  # Main sections

        errors = []
        warnings = []

        # Check character count
        if char_count < TARGET_CHAR_COUNT_MIN:
            errors.append(f"Article too short: {char_count} chars (min {TARGET_CHAR_COUNT_MIN})")
        elif char_count > TARGET_CHAR_COUNT_MAX:
            warnings.append(f"Article too long: {char_count} chars (max {TARGET_CHAR_COUNT_MAX})")

        # Check section count
        if sections < SECTIONS_MIN:
            errors.append(f"Too few sections: {sections} (min {SECTIONS_MIN})")
        elif sections > SECTIONS_MAX + 2:  # Allow some flexibility
            warnings.append(f"Many sections: {sections} (recommended max {SECTIONS_MAX})")

        # Check for required elements
        if "# " not in article_md:
            errors.append("Missing main title (# heading)")

        if "はじめに" not in article_md and "序論" not in article_md:
            warnings.append("Missing introduction section")

        if "結論" not in article_md and "まとめ" not in article_md:
            warnings.append("Missing conclusion section")

        if "参考" not in article_md:
            warnings.append("Missing references section")

        logger.info(f"Validation: {char_count} chars, {sections} sections")

        if errors:
            logger.warning(f"Validation errors: {errors}")
        if warnings:
            logger.info(f"Validation warnings: {warnings}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
