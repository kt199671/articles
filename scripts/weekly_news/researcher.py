"""AI-powered research and article generation for coworking space news."""

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
    NEWS_ITEMS_MIN,
    NEWS_ITEMS_MAX,
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


class CoworkingResearcher:
    """
    AI-powered researcher for coworking space industry trends.

    Uses Tavily for web search and Google Gemini for article generation.
    """

    def __init__(self):
        """Initialize researcher with API clients."""
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-3-flash-preview')

        self.tavily_client = TavilyClient(
            api_key=os.getenv("TAVILY_API_KEY")
        )

    def gather_weekly_trends(self, days: int = 7) -> ResearchData:
        """
        Search for latest coworking space trends using Tavily.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            ResearchData object with aggregated results
        """
        logger.info(f"Gathering trends from the past {days} days...")

        all_results: List[SearchResult] = []

        for query in SEARCH_QUERIES:
            logger.info(f"Searching: {query}")

            try:
                response = self.tavily_client.search(
                    query=query,
                    max_results=5,
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

        # Take top 15 results
        top_results = unique_results[:15]

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
        Generate article using Google Gemini based on research data.

        Args:
            research_data: Research data from gather_weekly_trends
            week_number: Week number string (e.g., "2026年01週")

        Returns:
            Article text in markdown format
        """
        logger.info("Generating article with Google Gemini 3.0 Flash...")

        # 週番号から日付を取得（その週の金曜日）
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")

        prompt = f"""過去1週間の「コワーキングスペース」に関する日本の最新ニュースを3〜5件調査し、note投稿用の記事（Markdown形式）を作成してください。

【記事の要件】
・タイトル：「【週刊】コワーキングスペース通信（{date_str}号）」形式
・構成：導入 → ニュース紹介（カテゴリ別） → まとめ → ハッシュタグ
・情報源：各ニュースの末尾に「記事タイトル（URL）」を必ず記載
・ハッシュタグ：#コワーキングスペース #働き方改革 #リモートワーク #最新ニュース
・形式：noteにコピー＆ペーストできるMarkdown形式で出力。生成AIの記事とはわからないように、絵文字は入れないで。

【記事構成の詳細】
1. タイトル（# 見出し）：【週刊】コワーキングスペース通信（{date_str}号）
2. 導入部：今週のコワーキングスペース業界の動向を簡潔に紹介（100-150文字）
3. ニュース紹介：カテゴリ別に3-5件のニュースを紹介
   - 各ニュースは ## 見出しで記載
   - カテゴリ例：新規開業、サービス拡充、業界動向、イベント情報など
   - 各ニュース200-400文字
   - 末尾に必ず出典を記載：「参考：記事タイトル（URL）」
4. まとめ：今週のトピックの総括（100-150文字）
5. ハッシュタグ：#コワーキングスペース #働き方改革 #リモートワーク #最新ニュース

【注意事項】
- 絵文字は一切使用しないこと
- 自然な文体で、AIが書いたとわからないようにすること
- 客観的かつプロフェッショナルなトーン
- 日本国内のニュースを優先すること

---

以下のリサーチデータを基に、重要度の高い3-5個のニュースを選定し、記事を執筆してください。

【リサーチデータ】
{self._format_research_data(research_data)}

【出力形式】
上記の構成に従って、Markdown形式で出力してください。
"""

        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 3000,
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
【ニュース {i}】
タイトル: {result.title}
URL: {result.url}
公開日: {result.published_date}
関連度: {result.score:.2f}
内容:
{result.content[:500]}...
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
        news_items = article_md.count("## ")  # カテゴリ見出しをカウント

        errors = []
        warnings = []

        # Check character count (タイトル・ハッシュタグ含め緩めの基準)
        if char_count < 1000:
            errors.append(f"Article too short: {char_count} chars (min 1000)")
        elif char_count > 3500:
            warnings.append(f"Article too long: {char_count} chars (max 3500)")

        # Check news item count
        if news_items < NEWS_ITEMS_MIN:
            errors.append(f"Too few news items: {news_items} (min {NEWS_ITEMS_MIN})")
        elif news_items > NEWS_ITEMS_MAX:
            warnings.append(f"Too many news items: {news_items} (max {NEWS_ITEMS_MAX})")

        # Check for required elements
        if "【週刊】コワーキングスペース通信" not in article_md:
            errors.append("Missing required title format")

        if "#コワーキングスペース" not in article_md:
            warnings.append("Missing required hashtags")

        if "参考：" not in article_md and "参照：" not in article_md:
            warnings.append("Missing source citations")

        logger.info(f"Validation: {char_count} chars, {news_items} items")

        if errors:
            logger.warning(f"Validation errors: {errors}")
        if warnings:
            logger.info(f"Validation warnings: {warnings}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
