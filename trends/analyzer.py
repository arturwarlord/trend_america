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

INPUT_FILE = "data/trend_candidates.json"

ANALYZED_FILE = "data/analyzed_trends.json"

OUTPUT_FILE = "data/top_trends.json"


# ==========================================
# CONFIG
# ==========================================

TOP_ANALYZED_TRENDS = 60

MAX_PER_CATEGORY = 8


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
# CATEGORY KEYWORDS
# ==========================================

CATEGORY_KEYWORDS = {

    "ai": {
        "ai",
        "artificial intelligence",
        "openai",
        "chatgpt",
        "gemini",
        "claude",
        "anthropic",
        "deepmind",
        "copilot",
        "machine learning",
        "neural network",
        "robot",
        "robotics",
        "generative ai",
        "llm"
    },

    "technology": {
        "technology",
        "tech",
        "google",
        "apple",
        "microsoft",
        "meta",
        "amazon",
        "iphone",
        "android",
        "pixel",
        "software",
        "hardware",
        "computer",
        "smartphone",
        "chip",
        "semiconductor",
        "internet",
        "cyber",
        "quantum"
    },

    "science": {
        "science",
        "scientist",
        "research",
        "study",
        "experiment",
        "discovery",
        "physics",
        "chemistry",
        "biology",
        "genetics",
        "dna",
        "evolution",
        "climate",
        "energy",
        "quantum"
    },

    "space": {
        "nasa",
        "space",
        "spacex",
        "rocket",
        "mars",
        "moon",
        "lunar",
        "solar",
        "eclipse",
        "asteroid",
        "comet",
        "satellite",
        "astronomy",
        "telescope",
        "galaxy",
        "universe",
        "black hole"
    },

    "business": {
        "business",
        "economy",
        "economic",
        "market",
        "markets",
        "stock",
        "stocks",
        "company",
        "companies",
        "startup",
        "startups",
        "finance",
        "financial",
        "bank",
        "banks",
        "money",
        "investment",
        "investor",
        "bitcoin",
        "crypto",
        "cryptocurrency",
        "trade"
    },

    "psychology": {
        "psychology",
        "psychological",
        "brain",
        "memory",
        "behavior",
        "behaviour",
        "human behavior",
        "human behaviour",
        "dopamine",
        "attention",
        "sleep",
        "stress",
        "emotion",
        "emotions",
        "mind"
    },

    "health": {
        "health",
        "medicine",
        "medical",
        "doctor",
        "disease",
        "cancer",
        "virus",
        "vaccine",
        "nutrition",
        "fitness",
        "body",
        "diet",
        "aging",
        "longevity"
    },

    "history": {
        "history",
        "historical",
        "ancient",
        "empire",
        "civilization",
        "war",
        "wwii",
        "ww2",
        "world war",
        "archaeology",
        "archaeological",
        "artifact",
        "king",
        "queen"
    },

    "engineering": {
        "engineering",
        "engineer",
        "engineering",
        "architecture",
        "bridge",
        "building",
        "construction",
        "invention",
        "inventor",
        "machine",
        "aircraft",
        "aviation",
        "train",
        "automotive",
        "car",
        "electric vehicle",
        "ev"
    },

    "future": {
        "future",
        "2030",
        "2040",
        "2050",
        "next generation",
        "next-gen",
        "innovation",
        "innovative",
        "future technology",
        "tomorrow"
    },

    "world": {
        "world",
        "global",
        "international",
        "country",
        "countries",
        "government",
        "population",
        "geopolitics",
        "earth",
        "environment",
        "disaster",
        "record"
    }

}


# ==========================================
# HARD NEGATIVE KEYWORDS
# ==========================================

HARD_NEGATIVE_KEYWORDS = {

    "gaming": {
        "minecraft",
        "fortnite",
        "roblox",
        "brawl stars",
        "among us",
        "league of legends",
        "valorant",
        "counter strike",
        "cs2",
        "call of duty",
        "gta",
        "grand theft auto",
        "playstation",
        "xbox",
        "nintendo",
        "maplestory",
        "honkai",
        "genshin",
        "pokemon",
        "gameplay",
        "gaming",
        "esports",
        "fncs",
        "lck",
        "streamer",
        "server"
    },

    "music": {
        "official music video",
        "music video",
        "official video",
        "lyrics",
        "lyric video",
        "dance practice",
        "dance performance",
        "official audio",
        "song",
        "album",
        "single",
        "mv"
    },

    "entertainment": {
        "trailer",
        "teaser",
        "official trailer",
        "movie",
        "netflix",
        "marvel",
        "avengers",
        "celebrity",
        "fan meeting",
        "reality show",
        "live stream",
        "live映像"
    },

    "sports": {
        "football",
        "soccer",
        "basketball",
        "baseball",
        "tennis",
        "boxing",
        "ufc",
        "championship",
        "league",
        "match",
        "vs",
        "final",
        "tournament",
        "lck",
        "fncs"
    },

    "fiction": {
        "skibidi",
        "spiderman",
        "spider-man",
        "shinchan",
        "anime",
        "cartoon",
        "fictional",
        "superhero"
    }

}


# ==========================================
# TEXT NORMALIZATION
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

def similarity(title_a, title_b):

    keywords_a = get_keywords(title_a)

    keywords_b = get_keywords(title_b)

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
        normalize_title(title_a),
        normalize_title(title_b)
    ).ratio()

    return (
        keyword_similarity * 0.7
        +
        text_similarity * 0.3
    )


# ==========================================
# FIND EXISTING GROUP
# ==========================================

def find_group(groups, title):

    for group in groups:

        score = similarity(
            title,
            group["representative"]
        )

        if score >= 0.55:
            return group

    return None


# ==========================================
# CREATE TOPIC GROUPS
# ==========================================

def create_groups(trends):

    groups = []

    for trend in trends:

        if not isinstance(trend, dict):
            continue

        title = trend.get(
            "title",
            ""
        )

        if not isinstance(title, str):
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

            groups.append(group)

        group["items"].append(
            trend
        )

    return groups


# ==========================================
# CATEGORY DETECTION
# ==========================================

def detect_categories(title):

    normalized = normalize_title(title)

    categories = []

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword in normalized:

                categories.append(category)

                break

    return categories


# ==========================================
# NEGATIVE CONTENT DETECTION
# ==========================================

def detect_negative_categories(title):

    normalized = normalize_title(title)

    categories = []

    for category, keywords in HARD_NEGATIVE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in normalized:

                categories.append(category)

                break

    return categories


# ==========================================
# TOPIC POTENTIAL
# ==========================================

def calculate_topic_potential(title):

    positive_categories = detect_categories(title)

    negative_categories = detect_negative_categories(title)

    score = 50

    # --------------------------------------
    # POSITIVE
    # --------------------------------------

    score += min(
        len(positive_categories) * 12,
        36
    )

    # --------------------------------------
    # NEGATIVE
    # --------------------------------------

    score -= min(
        len(negative_categories) * 30,
        70
    )

    # --------------------------------------
    # VERY SHORT TITLES
    # --------------------------------------

    words = normalize_title(title).split()

    if len(words) == 1:

        if positive_categories:
            score += 5
        else:
            score -= 15

    # --------------------------------------
    # QUESTION / DISCOVERY SIGNALS
    # --------------------------------------

    discovery_words = {
        "why",
        "how",
        "what",
        "could",
        "future",
        "discovered",
        "discovery",
        "scientists",
        "study",
        "research",
        "reveals",
        "explained"
    }

    if any(
        word in words
        for word in discovery_words
    ):

        score += 8

    return max(
        0,
        min(
            score,
            100
        )
    )


# ==========================================
# CALCULATE SCORE
# ==========================================

def calculate_score(group):

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

        if not isinstance(item, dict):
            continue

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

    # ======================================
    # COUNTRY SCORE
    # ======================================

    country_score = min(
        len(countries) / 10,
        1
    )

    # ======================================
    # GOOGLE SCORE
    # ======================================

    google_score = min(
        google_count / 10,
        1
    )

    # ======================================
    # YOUTUBE SCORE
    # ======================================

    youtube_score = min(
        youtube_count / 10,
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

        google_score * 30

        +

        youtube_score * 10

        +

        views_score * 20

    )

    # ======================================
    # CONTENT RELEVANCE
    # ======================================

    relevance_score = calculate_relevance(
        group["representative"]
    )

    # ======================================
    # TOPIC POTENTIAL
    # ======================================

    topic_potential = calculate_topic_potential(
        group["representative"]
    )

    categories = detect_categories(
        group["representative"]
    )

    negative_categories = detect_negative_categories(
        group["representative"]
    )

    # ======================================
    # FINAL SCORE
    # ======================================

    final_score = (

        global_score * 0.40

        +

        relevance_score * 0.25

        +

        topic_potential * 0.35

    )

    # ======================================
    # HARD PENALTY
    # ======================================

    if negative_categories:

        final_score *= 0.25

    # ======================================
    # RESULT
    # ======================================

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

        "topic_potential":
            topic_potential,

        "final_score":
            round(
                final_score,
                2
            ),

        "categories":
            categories,

        "negative_categories":
            negative_categories,

        "countries":
            sorted(countries),

        "country_count":
            len(countries),

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
                    if item.get("source")
                )
            )

    }


# ==========================================
# DIVERSIFIED TOP SELECTION
# ==========================================

def select_diversified_top(analyzed):

    selected = []

    category_counts = {}

    # ======================================
    # FIRST PASS
    # ======================================

    for trend in analyzed:

        if len(selected) >= TOP_ANALYZED_TRENDS:
            break

        categories = trend.get(
            "categories",
            []
        )

        negative = trend.get(
            "negative_categories",
            []
        )

        # ----------------------------------
        # Skip obvious entertainment
        # ----------------------------------

        if negative:
            continue

        # ----------------------------------
        # Category balancing
        # ----------------------------------

        if categories:

            allowed = False

            for category in categories:

                count = category_counts.get(
                    category,
                    0
                )

                if count < MAX_PER_CATEGORY:

                    allowed = True
                    break

            if not allowed:
                continue

        # ----------------------------------
        # Select
        # ----------------------------------

        selected.append(
            trend
        )

        for category in categories:

            category_counts[category] = (
                category_counts.get(
                    category,
                    0
                )
                + 1
            )

    # ======================================
    # SECOND PASS
    # ======================================

    if len(selected) < TOP_ANALYZED_TRENDS:

        selected_topics = {
            item["normalized_topic"]
            for item in selected
        }

        for trend in analyzed:

            if len(selected) >= TOP_ANALYZED_TRENDS:
                break

            if trend["normalized_topic"] in selected_topics:
                continue

            selected.append(
                trend
            )

            selected_topics.add(
                trend["normalized_topic"]
            )

    return selected


# ==========================================
# ANALYZE TRENDS
# ==========================================

def analyze_trends(trends):

    print()

    print(
        "================================"
    )

    print(
        "🧠 TREND ANALYZER V8.2"
    )

    print(
        "================================"
    )

    print()

    # ======================================
    # VALIDATE
    # ======================================

    if not isinstance(trends, list):

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

        if is_relevant(topic):

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
    # DIVERSIFIED TOP
    # ======================================

    top_trends = select_diversified_top(
        analyzed
    )

    # ======================================
    # PRINT
    # ======================================

    print()

    print(
        "================================"
    )

    print(
        "🔥 TOP 60 GLOBAL INFORMATION TRENDS"
    )

    print(
        "================================"
    )

    print()

    for index, trend in enumerate(

        top_trends,

        start=1

    ):

        categories = ", ".join(
            trend.get(
                "categories",
                []
            )
        )

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
            f"   Potential: "
            f"{trend.get('topic_potential', 0)}/100"
        )

        print(
            f"   Category: "
            f"{categories or 'general'}"
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

    return top_trends


# ==========================================
# SAVE ANALYZED TRENDS
# ==========================================

def save_analyzed_trends(trends):

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

def save_top_trends(trends):

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
