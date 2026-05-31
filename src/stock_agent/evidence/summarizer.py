from __future__ import annotations


def summarize_news(title: str, snippet: str, max_chars: int = 240) -> str:
    title = title.strip()
    snippet = snippet.strip()
    if title and snippet:
        summary = f"{title} - {snippet}"
    else:
        summary = title or snippet

    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 1].rstrip() + "..."
