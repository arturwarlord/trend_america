import json
import os
import re

from difflib import SequenceMatcher

from trends.content_filter import (
    calculate_relevance,
    is_relevant
)


# ==========================================
# FILES
# ==========================================

INPUT_FILE = (
    "data/trend_candidates.json"
)

ANALYZED_FILE = (
    "data/analyzed_trends.json"
)

OUTPUT_FILE = (
    "data/top_trends.json"
)


# ==========================================
# CONFIG
# ==========================================

TOP_ANALYZED_TRENDS = 60


# ==========================================
# STOP WORDS
# ==========================================

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


# ==========================================
# TEXT NORMALIZATION
# ==========================================

def normalize_title(
    title
):

    if not title:

        return ""

    title = str(
        title
    ).lower()

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


# ==========================================
# KEYWORDS
# ==========================================

def get_keywords(
    title
):

    normalized = normalize_title(
        title
    )

    words = normalized.split()

    return {

        word

        for word in words

        if len(word) >= 3

        and word not in STOP_WORDS

    }


# ==========================================
# SIMILARITY
# ==========================================

def similarity(
    title_a,
    title_b
):

    keywords_a = get_keywords(
        title_a
    )

    keywords_b = get_keywords(
        title_b
    )

    if not keywords_a or not keywords_b:

        return 0

    intersection = (
        keywords_a
        &
        keywords_b
    )

    union = (
        keywords_a
        |
        keywords_b
    )

    if not union:

        return 0

    keyword_similarity = (

        len(intersection)

        /

        len(union)

    )

    text_similarity = SequenceMatcher(

        None,

        normalize_title(
            title_a
        ),

        normalize_title(
            title_b
        )

    ).ratio()

    return (

        keyword_similarity * 0.7

        +

        text_similarity * 0.3

    )


# ==========================================
# FIND EXISTING GROUP
# ==========================================

def find_group(
    groups,
    title
):

    for group in groups:

        score = similarity(

            title,

            group[
                "representative"
            ]

        )

        if score >= 0.55:

            return group

    return None


# ==========================================
# CREATE TOPIC GROUPS
# ==========================================

def create_groups(
    trends
):

    groups = []

    for trend in trends:

        if not isinstance(
            trend,
            dict
        ):

            continue

        title = trend.get(
            "title",
            ""
        )

        if not isinstance(
            title,
            str
        ):

            continue

        title = title.strip()

        if not title:

            continue

        group = find_group(

            groups,

            title

        )

        if group is None:

            group = {

                "representative":
                    title,

                "items":
                    []

            }

            groups.append(
                group
            )

        group[
            "items"
        ].append(
            trend
        )

    return groups


# ==========================================
# CALCULATE SCORE
# ==========================================

def calculate_score(
    group
):

    items = group.get(
        "items",
        []
    )

    countries = set()

    google_count = 0

    youtube_count = 0

    total_views = 0

    # ======================================
    # COLLECT METRICS
    # ======================================

    for item in items:

        if not isinstance(
            item,
            dict
        ):

            continue

        # ----------------------------------
        # COUNTRY
        # ----------------------------------

        country = item.get(
            "country"
        )

        if country:

            countries.add(
                country
            )

        # ----------------------------------
        # SOURCE
        # ----------------------------------

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

    # ======================================
    # COUNTRY SCORE
    # ======================================

    country_score = min(

        len(countries)
        /
        10,

        1

    )

    # ======================================
    # GOOGLE SCORE
    # ======================================

    google_score = min(

        google_count
        /
        10,

        1

    )

    # ======================================
    # YOUTUBE SCORE
    # ======================================

    youtube_score = min(

        youtube_count
        /
        10,

        1

    )

    # ======================================
    # VIEWS SCORE
    # ======================================

    if total_views <= 0:

        views_score = 0

    else:

        views_score = min(

            (

                total_views
                /
                10_000_000

            ) ** 0.5,

            1

        )

    # ======================================
    # GLOBAL SCORE
    # ======================================

    global_score = (

        country_score * 40

        +

        google_score * 20

        +

        youtube_score * 20

        +

        views_score * 20

    )

    # ======================================
    # CONTENT RELEVANCE
    # ======================================

    relevance_score = calculate_relevance(

        group[
            "representative"
        ]

    )

    # ======================================
    # FINAL SCORE
    # ======================================

    final_score = (

        global_score * 0.60

        +

        relevance_score * 0.40

    )

    # ======================================
    # RESULT
    # ======================================

    return {

        "topic":
            group[
                "representative"
            ],

        "normalized_topic":
            normalize_title(
                group[
                    "representative"
                ]
            ),

        "global_score":
            round(
                global_score,
                2
            ),

        "relevance_score":
            relevance_score,

        "final_score":
            round(
                final_score,
                2
            ),

        "countries":
            sorted(
                countries
            ),

        "country_count":
            len(
                countries
            ),

        "google_count":
            google_count,

        "youtube_count":
            youtube_count,

        "total_views":
            total_views,

        "sources":
            sorted(

                set(

                    item.get(
                        "source",
                        ""
                    )

                    for item in items

                    if item.get(
                        "source"
                    )

                )

            )

    }


# ==========================================
# ANALYZE TRENDS
# ==========================================

def analyze_trends(
    trends
):

    print()

    print(
        "================================"
    )

    print(
        "🧠 TREND ANALYZER"
    )

    print(
        "================================"
    )

    print()

    # ======================================
    # VALIDATE
    # ======================================

    if not isinstance(
        trends,
        list
    ):

        print(
            "❌ Invalid trends data"
        )

        return []

    print(
        f"📥 Input trends: "
        f"{len(trends)}"
    )

    # ======================================
    # FILTER
    # ======================================

    relevant_trends = []

    filtered_count = 0

    for trend in trends:

        if not isinstance(
            trend,
            dict
        ):

            continue

        topic = trend.get(
            "title",
            ""
        )

        if not topic:

            continue

        if is_relevant(
            topic
        ):

            relevant_trends.append(
                trend
            )

        else:

            filtered_count += 1

            print(
                f"🚫 Filtered: "
                f"{topic}"
            )

    # ======================================
    # FILTER STATS
    # ======================================

    print()

    print(
        f"🚫 Filtered trends: "
        f"{filtered_count}"
    )

    print(
        f"✅ Relevant trends: "
        f"{len(relevant_trends)}"
    )

    # ======================================
    # GROUP
    # ======================================

    groups = create_groups(
        relevant_trends
    )

    print(
        f"🔗 Topic groups: "
        f"{len(groups)}"
    )

    # ======================================
    # CALCULATE
    # ======================================

    analyzed = []

    for group in groups:

        result = calculate_score(
            group
        )

        analyzed.append(
            result
        )

    # ======================================
    # SORT
    # ======================================

    analyzed.sort(

        key=lambda item:
            item.get(
                "final_score",
                0
            ),

        reverse=True

    )

    # ======================================
    # TOP 30
    # ======================================

    top_trends = analyzed[
        :TOP_ANALYZED_TRENDS
    ]

    # ======================================
    # PRINT
    # ======================================

    print()

    print(
        "================================"
    )

    print(
        "🔥 TOP 30 GLOBAL TRENDS"
    )

    print(
        "================================"
    )

    print()

    for index, trend in enumerate(

        top_trends,

        start=1

    ):

        print(

            f"#{index} "
            f"{trend.get('topic', '')}"

        )

        print(

            f"   Final Score: "
            f"{trend.get('final_score', 0)}/100"

        )

        print(

            f"   Global Score: "
            f"{trend.get('global_score', 0)}/100"

        )

        print(

            f"   Relevance: "
            f"{trend.get('relevance_score', 0)}/100"

        )

        print(

            f"   Countries: "
            f"{trend.get('country_count', 0)}"

        )

        print(

            f"   Google: "
            f"{trend.get('google_count', 0)}"

        )

        print(

            f"   YouTube: "
            f"{trend.get('youtube_count', 0)}"

        )

        print(

            f"   Views: "
            f"{trend.get('total_views', 0):,}"

        )

        print()

    # ======================================
    # IMPORTANT
    # ======================================
    #
    # analyze_trends() ALWAYS returns TOP 30.
    #
    # main.py does NOT need:
    #
    # return_all=True
    #
    # ======================================

    return top_trends


# ==========================================
# SAVE ANALYZED TRENDS
# ==========================================

def save_analyzed_trends(
    trends
):

    os.makedirs(

        "data",

        exist_ok=True

    )

    with open(

        ANALYZED_FILE,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            trends,

            file,

            ensure_ascii=False,

            indent=2

        )

    print()

    print(

        f"💾 Saved: "
        f"{ANALYZED_FILE}"

    )


# ==========================================
# SAVE AI APPROVED TRENDS
# ==========================================

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

    print()

    print(

        f"💾 Saved: "
        f"{OUTPUT_FILE}"

    )
