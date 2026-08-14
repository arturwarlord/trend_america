import re


# ==========================================
# HARD EXCLUSIONS
# ==========================================

EXCLUDED_KEYWORDS = {

    # ==========================
    # GAMING
    # ==========================

    "minecraft",
    "fortnite",
    "roblox",
    "gta",
    "gta 5",
    "gta 6",
    "gaming",
    "gameplay",
    "gamer",
    "game",
    "xbox",
    "playstation",
    "nintendo",
    "steam",
    "esports",
    "pvp",
    "npc",
    "simulator",
    "rainbow six",
    "call of duty",
    "black ops",
    "efootball",
    "battlefield",
    "total war",

    # ==========================
    # MUSIC
    # ==========================

    "official music video",
    "official lyric video",
    "music video",
    "lyrics",
    "song",
    "album",
    "concert",
    "singer",
    "rapper",
    "remix",
    "single",
    "official video",

    # ==========================
    # MOVIES / TV
    # ==========================

    "official trailer",
    "official teaser",
    "movie trailer",
    "film trailer",
    "trailer",
    "teaser",
    "episode",
    "season",
    "netflix",
    "paramount",
    "hbo",
    "disney",

    # ==========================
    # SPORTS
    # ==========================

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
    "goals",
    "highlights",
    "championship",
    "league",

    # ==========================
    # ENTERTAINMENT
    # ==========================

    "celebrity",
    "red carpet",
    "paparazzi",
    "gossip",
    "reality show",
    "reality tv",

    # ==========================
    # LOCAL / LANGUAGE CONTENT
    # ==========================

    "bollywood",
    "tollywood",
    "kollywood",
    "kpop",
    "anime",
    "punjabi",
    "telugu",
    "tamil",
    "hindi song",
    "hindi movie",
    "bhojpuri",

}


# ==========================================
# POSITIVE TOPICS
# ==========================================

POSITIVE_KEYWORDS = {

    # ==========================
    # AI
    # ==========================

    "artificial intelligence",
    "ai",
    "chatgpt",
    "openai",
    "gemini",
    "claude",
    "anthropic",
    "machine learning",
    "deep learning",
    "neural network",
    "robotics",
    "robot",

    # ==========================
    # TECHNOLOGY
    # ==========================

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
    "cybersecurity",
    "quantum",

    # ==========================
    # SCIENCE
    # ==========================

    "science",
    "scientist",
    "scientists",
    "research",
    "researcher",
    "researchers",
    "discovery",
    "discovered",
    "experiment",
    "study",
    "breakthrough",
    "laboratory",
    "physics",
    "biology",
    "chemistry",
    "medicine",

    # ==========================
    # SPACE
    # ==========================

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
    "solar eclipse",
    "eclipse",

    # ==========================
    # BUSINESS
    # ==========================

    "business",
    "economy",
    "market",
    "startup",
    "investment",
    "stocks",
    "finance",
    "financial",
    "money",

    # ==========================
    # WORLD / DISCOVERY
    # ==========================

    "world",
    "discovery",
    "archaeology",
    "archaeologist",
    "ancient",
    "historical",
    "history",
    "mystery",
    "rare discovery",
    "unknown",
    "unexplained",

    # ==========================
    # FUTURE
    # ==========================

    "future",
    "innovation",
    "invention",
    "invention",
}


# ==========================================
# NORMALIZE
# ==========================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower()

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


# ==========================================
# EXCLUSION CHECK
# ==========================================

def contains_excluded_keyword(
    text
):

    text = normalize_text(
        text
    )

    for keyword in EXCLUDED_KEYWORDS:

        keyword = normalize_text(
            keyword
        )

        if keyword in text:

            return True

    return False


# ==========================================
# RELEVANCE
# ==========================================

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

    matches = []

    for keyword in POSITIVE_KEYWORDS:

        normalized_keyword = normalize_text(
            keyword
        )

        if normalized_keyword in text:

            matches.append(
                normalized_keyword
            )

    # ======================================
    # NO MATCH
    # ======================================

    if not matches:

        return 35

    # ======================================
    # STRONG TOPIC
    # ======================================

    if len(matches) >= 3:

        return 100

    if len(matches) == 2:

        return 90

    return 75


# ==========================================
# RELEVANCE CHECK
# ==========================================

def is_relevant(
    topic
):

    return (
        calculate_relevance(
            topic
        )
        > 0
    )
