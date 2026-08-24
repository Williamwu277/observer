from typing import List

from models import ScrapeResult, ScrapeStatus, StatusResult


MAX_LISTINGS_IN_SUMMARY = 50


def _format_duration(seconds: float) -> str:
    rounded_seconds = round(seconds)
    minutes, seconds = divmod(rounded_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def _format_english_list(items: List[str]) -> str:
    if not items:
        return "None"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _count_phrase(count: int, singular: str, plural: str = "") -> str:
    noun = singular if count == 1 else plural or f"{singular}s"
    return f"{count} {noun}"


def _summarize_error(result: StatusResult) -> str:
    if result.error:
        return result.error.strip().splitlines()[-1]
    if result.status == ScrapeStatus.QUESTIONABLE:
        return "No jobs were found; human review is required."
    return "No new error details were reported."


def _notification_summary(
    attempts: int, successes: int, notifications_skipped: bool
) -> str:
    if notifications_skipped:
        return "Discord notifications were skipped in debug mode."
    if attempts == 0:
        return "No job notifications were needed."
    if attempts == successes:
        delivery_word = "delivery" if attempts == 1 else "deliveries"
        return f"Job notifications sent successfully ({attempts} {delivery_word})."
    return (
        "Job notifications partially succeeded "
        f"({successes} of {attempts} notification groups succeeded)."
    )


def build_run_summary(
    status_results: List[StatusResult],
    total_listings: int,
    new_listings: List[ScrapeResult],
    expired_listings: int,
    elapsed_seconds: float,
    notification_attempts: int,
    notification_successes: int,
    notifications_skipped: bool,
) -> str:
    """Build a human-readable summary of a completed scraper run."""
    passed = sorted(
        result.company_name
        for result in status_results
        if result.status in (ScrapeStatus.OPERATIONAL, ScrapeStatus.CONFIDENT)
    )
    needs_review = sorted(
        (
            result
            for result in status_results
            if result.status == ScrapeStatus.QUESTIONABLE
        ),
        key=lambda result: result.company_name,
    )
    failed = sorted(
        (result for result in status_results if result.status == ScrapeStatus.DOWN),
        key=lambda result: result.company_name,
    )
    sorted_new_listings = sorted(
        new_listings,
        key=lambda result: (result.company_name.lower(), result.title.lower()),
    )

    total_transfer = sum(result.request_size for result in status_results)
    average_scrape_time = (
        sum(result.scrape_time for result in status_results) / len(status_results)
        if status_results
        else 0
    )

    lines = [
        f"Scrape run completed in {_format_duration(elapsed_seconds)}.",
        "",
        f"Companies checked: {len(status_results)}",
        f"Passed ({len(passed)}): {_format_english_list(passed)}",
        (
            f"Needs review ({len(needs_review)}): "
            f"{_format_english_list([result.company_name for result in needs_review])}"
        ),
        (
            f"Failed ({len(failed)}): "
            f"{_format_english_list([result.company_name for result in failed])}"
        ),
        "",
        "Listings:",
        f"- {_count_phrase(total_listings, 'listing')} found during the scrape",
        f"- {_count_phrase(len(sorted_new_listings), 'new listing')} added",
        f"- {_count_phrase(expired_listings, 'listing')} marked expired",
        "",
        "New listings:",
    ]

    for listing in sorted_new_listings[:MAX_LISTINGS_IN_SUMMARY]:
        lines.append(f"- {listing.company_name} — {listing.title} — {listing.url}")
    if not sorted_new_listings:
        lines.append("- None")
    elif len(sorted_new_listings) > MAX_LISTINGS_IN_SUMMARY:
        remaining = len(sorted_new_listings) - MAX_LISTINGS_IN_SUMMARY
        lines.append(f"- ...and {_count_phrase(remaining, 'more listing')}")

    lines.extend(["", "Failed companies:"])
    if failed:
        for result in failed:
            lines.append(f"- {result.company_name} — {_summarize_error(result)}")
    else:
        lines.append("- None")

    lines.extend(["", "Needs review:"])
    if needs_review:
        for result in needs_review:
            lines.append(f"- {result.company_name} — {_summarize_error(result)}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "Resources:",
            f"- {total_transfer:.1f} MB transferred",
            f"- Average scrape time: {average_scrape_time:.1f}s per company",
            (
                "- "
                + _notification_summary(
                    notification_attempts,
                    notification_successes,
                    notifications_skipped,
                )
            ),
        ]
    )

    return "\n".join(lines)
