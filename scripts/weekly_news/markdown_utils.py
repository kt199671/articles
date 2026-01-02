"""Markdown to HTML conversion utilities for note.com."""

import markdown
from bs4 import BeautifulSoup
from typing import List


# note.com allowed HTML tags
ALLOWED_TAGS: List[str] = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "ul", "ol", "li",
    "strong", "em", "b", "i", "u",
    "a", "blockquote", "pre", "code",
    "img", "figure", "figcaption",
]


def markdown_to_note_html(markdown_text: str) -> str:
    """
    Convert markdown to note.com compatible HTML.

    note.com uses a specific subset of HTML tags.
    This function converts markdown and sanitizes the output.

    Args:
        markdown_text: Markdown formatted text

    Returns:
        HTML string compatible with note.com
    """
    # Convert markdown to HTML using python-markdown
    md = markdown.Markdown(
        extensions=[
            "extra",           # Tables, fenced code blocks, etc.
            "nl2br",           # Newline to <br>
            "sane_lists",      # Better list handling
        ],
        output_format="html5"
    )

    html = md.convert(markdown_text)

    # Sanitize HTML for note.com
    html = sanitize_for_note(html)

    return html


def sanitize_for_note(html: str) -> str:
    """
    Remove unsupported HTML tags and attributes for note.com.

    Args:
        html: HTML string to sanitize

    Returns:
        Sanitized HTML string
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove disallowed tags (keep content)
    for tag in soup.find_all():
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()

    # Sanitize attributes
    for tag in soup.find_all():
        # Keep only safe attributes
        if tag.name == "a":
            # Keep only href for links
            attrs = dict(tag.attrs)
            tag.attrs.clear()
            if "href" in attrs:
                tag["href"] = attrs["href"]

        elif tag.name == "img":
            # Keep src and alt for images
            attrs = dict(tag.attrs)
            tag.attrs.clear()
            if "src" in attrs:
                tag["src"] = attrs["src"]
            if "alt" in attrs:
                tag["alt"] = attrs["alt"]

        else:
            # Remove all attributes for other tags
            tag.attrs.clear()

    return str(soup)


def validate_html_for_note(html: str) -> bool:
    """
    Validate if HTML contains only note.com compatible tags.

    Args:
        html: HTML string to validate

    Returns:
        True if valid, False otherwise
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all():
        if tag.name not in ALLOWED_TAGS:
            return False

    return True
