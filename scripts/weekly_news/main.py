"""Main orchestrator for weekly coworking space news automation."""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

from .config import MAGAZINE_PATH, WEEK_FORMAT, MAX_RETRIES, RETRY_DELAY, LOG_FORMAT, LOG_LEVEL
from .researcher import CoworkingResearcher
from .note_api import NoteAPIClient, LoginError, NoteAPIError


# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """Errors that should trigger retry logic."""
    pass


class FatalError(Exception):
    """Errors that should immediately fail the workflow."""
    pass


def get_current_week_number() -> str:
    """
    Get current week number in Japanese format.

    Returns:
        Week number string (e.g., "2026年01週")
    """
    now = datetime.now()
    week_number = now.strftime(WEEK_FORMAT)
    return week_number


def get_output_path(week_number: str) -> Path:
    """
    Generate full path for weekly article.

    Args:
        week_number: Week number string

    Returns:
        Path object for article file
    """
    filename = f"{week_number}.md"
    return MAGAZINE_PATH / filename


def save_markdown(file_path: Path, content: str) -> None:
    """
    Save markdown content to file.

    Args:
        file_path: Path to save file
        content: Markdown content
    """
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved article to {file_path}")


def validate_environment() -> None:
    """
    Validate required environment variables are set.

    Raises:
        FatalError: If required environment variables are missing
    """
    required_vars = [
        "GEMINI_API_KEY",
        "TAVILY_API_KEY",
        "NOTE_EMAIL",
        "NOTE_PASSWORD",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise FatalError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    logger.info("Environment validation passed")


def main(dry_run: bool = False) -> int:
    """
    Main workflow orchestrator.

    Args:
        dry_run: If True, skip note.com publishing

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # 1. Validate environment
        logger.info("Starting weekly coworking space news automation...")
        validate_environment()

        # 2. Determine week number and file path
        week_number = get_current_week_number()
        output_path = get_output_path(week_number)

        logger.info(f"Target week: {week_number}")
        logger.info(f"Output path: {output_path}")

        # 3. Check if article already exists
        if output_path.exists():
            logger.info(f"Article already exists: {output_path}")
            logger.info("Skipping generation to avoid duplicates")
            return 0

        # 4. Research coworking trends
        logger.info("Step 1: Gathering coworking space trends...")
        researcher = CoworkingResearcher()

        try:
            research_data = researcher.gather_weekly_trends(days=7)
        except Exception as e:
            raise RetryableError(f"Failed to gather trends: {e}")

        if research_data.total_results == 0:
            logger.warning("No research results found. Generating article anyway...")

        # 5. Generate article
        logger.info("Step 2: Generating article with AI...")

        try:
            article_md = researcher.generate_article(research_data, week_number)
        except Exception as e:
            raise RetryableError(f"Failed to generate article: {e}")

        # 6. Validate article
        logger.info("Step 3: Validating article...")
        validation = researcher.validate_article(article_md)

        if not validation.valid:
            logger.warning(f"Article validation failed: {validation.errors}")
            logger.info("Attempting to regenerate article...")

            try:
                article_md = researcher.generate_article(research_data, week_number)
                validation = researcher.validate_article(article_md)

                if not validation.valid:
                    logger.warning("Second validation also failed, proceeding anyway")

            except Exception as e:
                logger.warning(f"Regeneration failed: {e}, using original")

        if validation.warnings:
            logger.info(f"Validation warnings: {validation.warnings}")

        # 7. Save markdown file
        logger.info("Step 4: Saving markdown file...")
        save_markdown(output_path, article_md)

        # 8. Publish to note.com (unless dry run)
        if dry_run:
            logger.info("Dry run mode: Skipping note.com publishing")
            logger.info("Article saved successfully!")
            return 0

        logger.info("Step 5: Publishing to note.com...")

        magazine_id = os.getenv("NOTE_MAGAZINE_ID")
        if not magazine_id:
            logger.warning("NOTE_MAGAZINE_ID not set, creating draft without magazine")

        note_client = NoteAPIClient()

        try:
            draft_url = note_client.create_draft(
                title=f"週刊コワーキングスペース {week_number}",
                content_markdown=article_md,
                magazine_id=magazine_id
            )

            logger.info(f"Draft created successfully: {draft_url}")

        except LoginError as e:
            raise FatalError(f"note.com login failed: {e}")

        except NoteAPIError as e:
            raise RetryableError(f"note.com API error: {e}")

        # 9. Success
        logger.info("=" * 60)
        logger.info("SUCCESS!")
        logger.info(f"Article: {output_path}")
        logger.info(f"Draft URL: {draft_url}")
        logger.info("=" * 60)

        return 0

    except FatalError as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Workflow failed")
        return 1

    except RetryableError as e:
        logger.error(f"Retryable error: {e}")
        logger.error("Workflow failed (consider retry)")
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        logger.error("Workflow failed")
        return 1


def cli():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Weekly Coworking Space News Automation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip note.com publishing (local file only)"
    )

    args = parser.parse_args()

    exit_code = main(dry_run=args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
