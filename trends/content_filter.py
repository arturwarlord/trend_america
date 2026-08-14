import re


# ==========================================
# HARD EXCLUSIONS
# ==========================================

EXCLUDED_KEYWORDS = {

    # Gaming
    "minecraft",
    "fortnite",
    "roblox",
    "gaming",
    "gameplay",
    "gamer",
    "xbox",
    "playstation",
    "nintendo",

    # Music
    "official music video",
    "music video",
    "lyrics",
    "song",
    "album",
    "concert",
    "singer",

    # Movie / TV trailers
    "official trailer",
    "official teaser",
    "movie trailer",
    "film trailer",
    "trailer",
    "teaser",
    "episode",
    "season",

    # Sports
    "football",
    "soccer",
    "basketball",
    "baseball",
    "cricket",
    "hockey",
    "tennis",
    "ufc",
    "boxing",
    "wrestling",
    "match",
    "goal",
    "highlights",

    # Local entertainment
    "bollywood",
    "tollywood",
    "kollywood",
    "anime",
    "kpop",
    "tamil",
    "telugu",
    "hindi trailer",

    # Low-value celebrity content
    "celebrity",
    "red carpet",
    "paparazzi",
    "gossip",
}


# ==========================================
# POSITIVE TOPICS
# ==========================================

POSITIVE_KEYWORDS = {

    # AI
    "ai",
    "artificial intelligence",
    "chatgpt",
    "openai",
    "gemini",
    "claude",
    "anthropic",
    "machine learning",
    "robot",
    "robotics",

    # Technology
    "technology",
    "tech",
    "iphone",
    "android",
    "apple",
    "google",
    "microsoft",
    "meta",
    "tesla",
    "chip",
    "processor",
    "computer",
    "smartphone",
    "internet",

    # Science
    "science",
    "scientist",
    "scientists",
    "research",
    "researchers",
    "discovery",
    "experiment",
    "study",
    "quantum",

    # Space
    "nasa",
    "space",
    "spacex",
    "rocket",
    "moon",
    "mars",
    "planet",
    "asteroid",
    "galaxy",
    "universe",
    "black hole",
    "telescope",

    # Business / Economy
    "business",
    "economy",
    "market",
    "startup",
    "company",
    "investment",
    "stocks",
    "finance",
    "money",

    # Future
    "future",
    "innovation",
    "invention",
    "breakthrough",
    "technology",

    # World discoveries / events
    "discovered",
    "discovered",
    "breakthrough",
    "mystery",
    "ancient",
    "archaeology",
    "archaeologist",
    "history",
    "historical",
}


def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_excluded_keyword(
    text
):

    text = normalize_text(
        text
    )

    for keyword in EXCLUDED_KEYWORDS:

        if keyword in text:

            return True

    return False


def calculate_relevance(
    topic
):

    text = normalize_text(
        topic
    )

    # Hard exclusion
    if contains_excluded_keyword(
        text
    ):

        return 0

    positive_matches = 0

    for keyword in POSITIVE_KEYWORDS:

        if keyword in text:

            positive_matches += 1

    # No obvious niche
    if positive_matches == 0:

        return 35

    # Strong topical relevance
    if positive_matches >= 3:

        return 100

    if positive_matches == 2:

        return 90

    return 75


def is_relevant(topic):

    return (
        calculate_relevance(topic)
        > 0
    )
