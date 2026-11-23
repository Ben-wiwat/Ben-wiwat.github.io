#!/usr/bin/env python3
"""Update both pages with manually entered Google Scholar statistics."""

import json
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGES = (ROOT / "index.html", ROOT / "publications.html")


def nonnegative_integer(text, description):
    text = text.strip()
    if not re.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)", text):
        raise ValueError(f"{description} must be a non-negative whole number")
    return int(text.replace(",", ""))


def read_stats():
    print("Enter the all-time metrics and ten consecutive annual counts from Google Scholar.")
    metrics = {
        "citations": nonnegative_integer(input("Total citations: "), "Total citations"),
        "h-index": nonnegative_integer(input("h-index: "), "h-index"),
        "i10-index": nonnegative_integer(input("i10-index: "), "i10-index"),
    }
    first_year = nonnegative_integer(input("First year of the ten-year chart: "), "First year")
    if first_year < 1900 or first_year + 9 > date.today().year:
        raise ValueError("The chart must cover ten years from 1900 up to the current year")
    years = list(range(first_year, first_year + 10))
    values = input(f"Citations for {years[0]}-{years[-1]}, oldest first (10 comma-separated numbers): ").split(",")
    if len(values) != 10 or any(not re.fullmatch(r"[0-9]+", value.strip()) for value in values):
        raise ValueError("Enter exactly ten non-negative whole numbers separated by commas")
    counts = [int(value.strip()) for value in values]
    if sum(counts) > metrics["citations"]:
        raise ValueError("Annual citations exceed the total")
    return metrics, years, counts


def replace_once(text, pattern, replacement, description):
    updated, count = re.subn(pattern, replacement, text)
    if count != 1:
        raise ValueError(f"Expected exactly one {description}; found {count}")
    return updated


def update_page(html, metrics, years, counts):
    for key, value in metrics.items():
        pattern = rf'(<td data-scholar="{re.escape(key)}">)\d+(</td>)'
        html = replace_once(html, pattern, lambda m: f"{m[1]}{value}{m[2]}", key)
    pattern = (
        r"(labels:\s*)\[[^\]]*\](,\s*datasets:\s*\[\{\s*"
        r"label:\s*'Citations per year',\s*backgroundColor:\s*\[\],\s*data:\s*)"
        r"\[[^\]]*\]"
    )
    return replace_once(
        html,
        pattern,
        lambda m: f"{m[1]}{json.dumps([str(year) for year in years])}{m[2]}{json.dumps(counts)}",
        "citation chart",
    )


def main():
    metrics, years, counts = read_stats()
    updates = []
    for page in PAGES:
        with page.open(encoding="utf-8", newline="") as file:
            original = file.read()
        updates.append((page, original, update_page(original, metrics, years, counts)))
    for page, original, content in updates:
        if content != original:
            with page.open("w", encoding="utf-8", newline="") as file:
                file.write(content)
    print(f"Updated citation statistics for {years[0]}-{years[-1]} in both pages.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError, EOFError, KeyboardInterrupt) as error:
        print(f"\nCould not update Google Scholar statistics: {error or 'input cancelled'}", file=sys.stderr)
        sys.exit(1)
