import json
import os
import re
from difflib import SequenceMatcher

from trends.content_filter import (
    calculate_relevance,
    is_relevant
)


INPUT_FILE = "data/trend_candidates.json"

ANALYZED_FILE = "data/analyzed_trends.json"

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


# ==========================================
# HARD EXCLUDE
# ==========================================

HARD_EXCLUDE_PATTERNS = [

    # MUSIC
    r"\bofficial music video\b",
    r"\bmusic video\b",
    r"\bofficial video\b",
    r"\blyric video\b",
    r"\bofficial lyric\b",
    r"\bdance practice\b",
    r"\bofficial audio\b",
    r"\bmv\b",
    r"\bnew song\b",
    r"\blatest song\b",
    r"\bhit song\b",
    r"\balbum\b",

    # GAMING
    r"\bminecraft\b",
    r"\broblox\b",
    r"\bfortnite\b",
    r"\bgta 5\b",
    r"\bgta 6\b",
    r"\bcall of duty\b",
    r"\bblack ops\b",
    r"\bwarhammer\b",
    r"\bbrawl stars\b",
    r"\brainbow six\b",
    r"\bplaystation\b",
    r"\bxbox\b",
    r"\besports\b",
    r"\bgameplay\b",
    r"\bgame trailer\b",

    # SPORTS
    r"\bvs\b",
    r"\bmatch\b",
    r"\bhighlights\b",
    r"\bfootball\b",
    r"\bsoccer\b",
    r"\bbasketball\b",
    r"\btennis\b",
    r"\bbaseball\b",
    r"\bcricket\b",
    r"\blck\b",
    r"\bnba\b",
    r"\bnfl\b",
    r"\bfifa\b",

    # MOVIES / TV
    r"\bofficial trailer\b",
    r"\btrailer\b",
    r"\bteaser\b",
    r"\bseason \d+\b",
    r"\bepisode\b",
    r"\bnetflix\b",
    r"\bmarvel\b",
    r"\bdisney\b",
    r"\banime\b",

    # DANCE
    r"\bdance\b",
    r"\bchoreography\b",

    # LIVE
    r"🔴\s*live",
    r"\blive stream\b",

]


# ==========================================
# NORMALIZE
# ==========================================

def normalize_title(title):

    if not title:
        return ""

    title = str(title).lower()

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

def get_keywords(title):

    normalized = normalize_title(title)

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

    if not union:
        return 0

    keyword_similarity = (
        len(intersection)
        /
        len(union)
    )

    text_similarity = SequenceMatcher(
        None,
        normalize_title(title_a),
        normalize_title(title_b)
    ).ratio()

    return (
        keyword_similarity * 0.7
        +
        text_similarity * 0.3
    )


# ==========================================
# HARD FILTER
# ==========================================

def hard_filter_topic(title):

    if not title:
        return False

    text = str(title).lower()

    for pattern in HARD_EXCLUDE_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            return False

    return True


# ==========================================
# FIND GROUP
# ==========================================

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


# ==========================================
# CREATE GROUPS
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
                "representative": title,
                "items": []
            }

            groups.append(
                group
            )

        group["items"].append(
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
    # METRICS
    # ======================================

    for item in items:

        if not isinstance(
            item,
            dict
        ):
            continue

        country = item.get(
            "country"
        )

        if country:
            countries.add(
                country
            )

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
    # GLOBAL METRICS
    # ======================================

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
    # RELEVANCE
    # ======================================

    relevance_score = calculate_relevance(
        group["representative"]
    )

    # ======================================
    # FINAL SCORE
    #
    # QUALITY > POPULARITY
    # ======================================

    final_score = (

        relevance_score * 0.60

        +

        global_score * 0.40

    )

    return {

        "topic":
            group["representative"],

        "normalized_topic":
            normalize_title(
                group["representative"]
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
# ANALYZE
# ==========================================

def analyze_trends(
    trends
):

    print()
    print("================================")
    print("🧠 TREND ANALYZER V2")
    print("================================")
    print()

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

    relevant_trends = []

    filtered_count = 0

    # ======================================
    # FILTER
    # ======================================

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

        # HARD FILTER
        if not hard_filter_topic(topic):

            filtered_count += 1

            print(
                f"🚫 Hard filtered: "
                f"{topic}"
            )

            continue

        # CONTENT FILTER
        if not is_relevant(topic):

            filtered_count += 1

            print(
                f"🚫 Filtered: "
                f"{topic}"
            )

            continue

        relevant_trends.append(
            trend
        )

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
    # SCORE
    # ======================================

    analyzed = []

    for group in groups:

        result = calculate_score(
            group
        )

        # Don't send weak topics to AI
        if result["relevance_score"] < 45:

            print(
                f"🚫 Low relevance: "
                f"{result['topic']} "
                f"({result['relevance_score']}/100)"
            )

            continue

        analyzed.append(
            result
        )

    # ======================================
    # SORT
    # ======================================

    analyzed.sort(
        key=lambda item:
            item["final_score"],
        reverse=True
    )

    # ======================================
    # TOP 40
    # ======================================

    top_trends = analyzed[:40]

    print()
    print("================================")
    print("🔥 TOP 40 GLOBAL CANDIDATES")
    print("================================")
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
            f"   Final: "
            f"{trend['final_score']}/100"
        )

        print(
            f"   Global: "
            f"{trend['global_score']}/100"
        )

        print(
            f"   Relevance: "
            f"{trend['relevance_score']}/100"
        )

        print(
            f"   Countries: "
            f"{trend['country_count']}"
        )

        print(
            f"   Views: "
            f"{trend['total_views']:,}"
        )

        print()

    return top_trends


# ==========================================
# SAVE ANALYZED
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

    print(
        f"💾 Saved: {ANALYZED_FILE}"
    )


# ==========================================
# SAVE AI RESULTS
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

    print(
        f"💾 Saved: {OUTPUT_FILE}"
    )
