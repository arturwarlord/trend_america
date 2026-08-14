import json
import os
import re
from difflib import SequenceMatcher


INPUT_FILE = "data/trend_candidates.json"
OUTPUT_FILE = "data/top_trends.json"


STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "from",
    "is",
    "are",
    "was",
    "were",
    "this",
    "that",
    "new",
    "today",
    "latest",
    "news"
}


def normalize_title(title):

    if not title:
        return ""

    title = title.lower()

    title = re.sub(
        r"[^\w\s]",
        " ",
        title,
        flags=re.UNICODE
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    ).strip()

    return title


def get_keywords(title):

    normalized = normalize_title(title)

    words = normalized.split()

    return {
        word
        for word in words
        if len(word) >= 3
        and word not in STOP_WORDS
    }


def similarity(title_a, title_b):

    keywords_a = get_keywords(title_a)
    keywords_b = get_keywords(title_b)

    if not keywords_a or not keywords_b:
        return 0

    intersection = (
        keywords_a & keywords_b
    )

    union = (
        keywords_a | keywords_b
    )

    keyword_similarity = (
        len(intersection) /
        len(union)
    )

    text_similarity = SequenceMatcher(
        None,
        normalize_title(title_a),
        normalize_title(title_b)
    ).ratio()

    return (
        keyword_similarity * 0.7
        + text_similarity * 0.3
    )


def find_group(
    groups,
    title
):

    for group in groups:

        score = similarity(
            title,
            group["representative"]
        )

        if score >= 0.55:

            return group

    return None


def create_groups(trends):

    groups = []

    for trend in trends:

        title = trend.get(
            "title",
            ""
        ).strip()

        if not title:
            continue

        group = find_group(
            groups,
            title
        )

        if group is None:

            group = {
                "representative": title,
                "items": []
            }

            groups.append(group)

        group["items"].append(
            trend
        )

    return groups


def calculate_score(group):

    items = group["items"]

    countries = set()

    google_count = 0
    youtube_count = 0

    total_views = 0

    for item in items:

        country = item.get(
            "country"
        )

        if country:
            countries.add(country)

        source = item.get(
            "source"
        )

        if source == "google":
            google_count += 1

        elif source == "youtube":

            youtube_count += 1

            views = item.get(
                "views",
                0
            )

            try:
                total_views += int(
                    views
                )
            except (
                TypeError,
                ValueError
            ):
                pass

    country_score = min(
        len(countries) / 10,
        1
    )

    google_score = min(
        google_count / 10,
        1
    )

    youtube_score = min(
        youtube_count / 10,
        1
    )

    # Logarithmic view scoring.
    # Prevents one extremely large
    # video from dominating everything.

    if total_views <= 0:

        views_score = 0

    else:

        views_score = min(
            (
                total_views /
                10_000_000
            ) ** 0.5,
            1
        )

    score = (
        country_score * 40
        + google_score * 20
        + youtube_score * 20
        + views_score * 20
    )

    return {
        "topic": group["representative"],
        "normalized_topic": normalize_title(
            group["representative"]
        ),
        "global_score": round(
            score,
            2
        ),
        "countries": sorted(
            countries
        ),
        "country_count": len(
            countries
        ),
        "google_count": google_count,
        "youtube_count": youtube_count,
        "total_views": total_views,
        "sources": sorted(
            set(
                item.get(
                    "source",
                    ""
                )
                for item in items
            )
        )
    }


def analyze_trends(trends):

    print()
    print("================================")
    print("🧠 TREND ANALYZER")
    print("================================")
    print()

    print(
        f"📥 Input trends: "
        f"{len(trends)}"
    )

    groups = create_groups(
        trends
    )

    print(
        f"🔗 Topic groups: "
        f"{len(groups)}"
    )

    analyzed = []

    for group in groups:

        result = calculate_score(
            group
        )

        analyzed.append(
            result
        )

    analyzed.sort(
        key=lambda item:
            item["global_score"],
        reverse=True
    )

    top_trends = analyzed[:10]

    print()
    print("🔥 TOP GLOBAL TRENDS")
    print()

    for index, trend in enumerate(
        top_trends,
        start=1
    ):

        print(
            f"#{index} "
            f"{trend['topic']}"
        )

        print(
            f"   Score: "
            f"{trend['global_score']}/100"
        )

        print(
            f"   Countries: "
            f"{trend['country_count']}"
        )

        print(
            f"   Google: "
            f"{trend['google_count']}"
        )

        print(
            f"   YouTube: "
            f"{trend['youtube_count']}"
        )

        print(
            f"   Views: "
            f"{trend['total_views']:,}"
        )

        print()

    return top_trends


def save_top_trends(
    trends
):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            trends,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"💾 Saved: {OUTPUT_FILE}"
    )
