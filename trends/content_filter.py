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
    # LOCAL / ENTERTAINMENT
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

}


# ==========================================
# NORMALIZE TEXT
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

def contains_excluded_keyword(text):

    text = normalize_text(
        text
    )

    if not text:
        return False

    words = set(
        text.split()
    )

    for keyword in EXCLUDED_KEYWORDS:

        normalized_keyword = normalize_text(
            keyword
        )

        if not normalized_keyword:
            continue

        # Multi-word keyword
        if " " in normalized_keyword:

            if normalized_keyword in text:

                return True

        # Single-word keyword
        else:

            if normalized_keyword in words:

                return True

    return False


# ==========================================
# RELEVANCE SCORE
# ==========================================

def calculate_relevance(topic):

    text = normalize_text(
        topic
    )

    if not text:
        return 0

    # ======================================
    # HARD EXCLUSION
    # ======================================

    if contains_excluded_keyword(
        text
    ):

        return 0

    words = set(
        text.split()
    )

    matches = []

    # ======================================
    # FIND POSITIVE KEYWORDS
    # ======================================

    for keyword in POSITIVE_KEYWORDS:

        normalized_keyword = normalize_text(
            keyword
        )

        if not normalized_keyword:
            continue

        # ----------------------------------
        # Multi-word keyword
        # ----------------------------------

        if " " in normalized_keyword:

            if normalized_keyword in text:

                matches.append(
                    normalized_keyword
                )

        # ----------------------------------
        # Single-word keyword
        # ----------------------------------

        else:

            if normalized_keyword in words:

                matches.append(
                    normalized_keyword
                )

    # ======================================
    # NO MATCH
    # ======================================

    if not matches:

        return 35

    # ======================================
    # STRONG KEYWORDS
    # ======================================

    strong_keywords = {

        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",

        "chatgpt",
        "openai",
        "gemini",
        "claude",
        "anthropic",

        "nasa",
        "spacex",
        "black hole",
        "asteroid",

        "scientist",
        "scientists",
        "discovery",
        "breakthrough",

        "robotics",
        "robot",

        "quantum",

        "innovation",
        "invention",

    }

    strong_matches = [

        match

        for match in matches

        if match in strong_keywords

    ]

    # ======================================
    # VERY STRONG TOPIC
    # ======================================

    if len(strong_matches) >= 2:

        return 100

    if len(strong_matches) == 1:

        return 90

    # ======================================
    # MULTIPLE GENERAL SIGNALS
    # ======================================

    if len(matches) >= 2:

        return 80

    # ======================================
    # ONE GENERAL SIGNAL
    # ======================================

    return 55


# ==========================================
# RELEVANCE CHECK
# ==========================================

def is_relevant(topic):

    return (
        calculate_relevance(
            topic
        ) > 0
    )
