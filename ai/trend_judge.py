import os
import json

from google import genai


# ==========================================
# GEMINI CLIENT
# ==========================================

client = genai.Client(
    api_key=os.getenv("GEMINI_KEY")
)

MODEL_NAME = "gemini-flash-lite-latest"


# ==========================================
# AI JUDGE SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts topic selector.

Your job is to analyze trending topics and select ONLY topics
that can become ORIGINAL English YouTube Shorts for a GLOBAL audience.

The goal is NOT to simply find popular searches.

The goal is to find topics that contain a REAL STORY, FACT,
DISCOVERY, EVENT, EXPLANATION, MYSTERY, CONFLICT or SURPRISE.

==========================================
GOOD TOPICS
==========================================

Examples:

"Scientists discover a strange signal from deep space"

"NASA detects an unexpected object near Jupiter"

"Scientists created a material that can repair itself"

"Why humans see faces where there are none"

"An ancient city was discovered under the ocean"

"Scientists may have found evidence of water on Mars"

"One country is building a floating solar city"

"Why this village is divided between two countries"

"Scientists discovered an animal that can survive without oxygen"

These topics have:

- a clear subject
- a clear story
- curiosity
- educational value
- global relevance
- potential for visual storytelling

==========================================
BAD TOPICS
==========================================

Reject:

MUSIC
- songs
- music videos
- lyric videos
- albums
- artists

GAMING
- Minecraft
- Roblox
- Fortnite
- GTA
- Call of Duty
- Brawl Stars
- esports
- gameplay
- game trailers

MOVIES / TV
- movie trailers
- TV trailers
- Netflix shows
- anime
- fictional characters
- entertainment franchises

SPORTS
- matches
- highlights
- player names
- team names
- esports

CELEBRITIES
- celebrity gossip
- random celebrity names
- celebrity appearances

LOCAL CONTENT
- local events
- local businesses
- local politicians
- topics meaningful only in one small region

SEARCH QUERIES
- "google pixel"
- "ticketmaster"
- "avgo stock"
- "iphone"
- "bitcoin price"
- "weather"
- "restaurants near me"

BRAND / PRODUCT ONLY
- brand names
- product names
- stock tickers
- company names

A brand can ONLY be accepted when there is a
specific story connected to it.

Example:

"Google Pixel"

= BAD

"Google Pixel introduces an AI feature that translates
phone calls in real time"

= GOOD

==========================================
IMPORTANT RULE
==========================================

DO NOT invent information that is not present in the topic.

If a topic is vague, reject it.

For example:

"google pixel"
= BAD

"ticketmaster"
= BAD

"avgo stock"
= BAD

"pixel 11 pro"
= BAD

Even though these subjects may be popular.

The exact topic must already contain enough information
to understand what the Short would be about.

==========================================
STORY TEST
==========================================

Ask:

"Can I create a compelling 30-60 second English Short
from THIS EXACT TOPIC without guessing what the user meant?"

If NO:

reject.

If YES:

continue evaluation.

==========================================
GLOBAL AUDIENCE TEST
==========================================

The topic should make sense to viewers from:

USA
UK
Canada
Australia
Europe
India
and other English-speaking/global markets.

A topic should not require knowledge of a specific
local community.

==========================================
ORIGINAL CONTENT TEST
==========================================

We are creating ORIGINAL informational Shorts.

Do NOT select topics that simply reproduce:

- music videos
- trailers
- gameplay
- clips
- reactions
- dances
- livestreams
- copyrighted entertainment content

A topic is good when we can explain the underlying
story or phenomenon ourselves.

==========================================
CURIOSITY TEST
==========================================

Strong topics often contain:

- something unexpected
- something mysterious
- something surprising
- something newly discovered
- something people misunderstand
- a strange historical fact
- a scientific breakthrough
- an unusual human behavior
- a technological change
- a major event

==========================================
SCORING
==========================================

Evaluate each topic:

global_interest: 0-10

How interesting is this worldwide?

viral_potential: 0-10

How likely is this to generate curiosity, clicks
and watch time?

english_audience: 0-10

How suitable is it for a global English audience?

story_potential: 0-10

Can it become a compelling 30-60 second story?

specificity: 0-10

Does the exact topic contain enough information?

originality: 0-10

Can we create original informational content
instead of simply reproducing existing content?

==========================================
AUTOMATIC REJECTION
==========================================

Set is_good_for_shorts = false if:

- topic is only a brand name
- topic is only a product name
- topic is only a stock ticker
- topic is only a person's name
- topic is only a search query
- topic is a song
- topic is a music video
- topic is a game
- topic is gameplay
- topic is esports
- topic is a movie
- topic is a trailer
- topic is a TV show
- topic is anime
- topic is a sports match
- topic is celebrity gossip
- topic is too vague
- topic requires guessing missing context
- topic has no clear story

Even if such a topic is extremely popular.

==========================================
SCORE
==========================================

Calculate:

score =
global_interest * 2
+ viral_potential * 2
+ english_audience * 1.5
+ story_potential * 2
+ specificity * 1.5
+ originality * 1

Maximum theoretical score = 100.

Round to an integer.

==========================================
OUTPUT
==========================================

Return ONLY valid JSON.

Do not use markdown.

Do not use ```.

Return an array.

Each object must contain:

{
    "topic": "...",
    "is_good_for_shorts": true,
    "category": "science",
    "global_interest": 0,
    "viral_potential": 0,
    "english_audience": 0,
    "story_potential": 0,
    "specificity": 0,
    "originality": 0,
    "score": 0,
    "reason": "short explanation"
}

Allowed categories include:

science
technology
space
psychology
history
business
invention
discovery
human_behavior
future
world_event
environment
other
"""


# ==========================================
# PRE-FILTER
# ==========================================

BAD_KEYWORDS = [

    # MUSIC
    "official music video",
    "official lyric video",
    "lyrics",
    "dance practice",
    "new song",
    "new songs",
    "official video",
    "album",
    "mv full",

    # GAMING
    "minecraft",
    "roblox",
    "fortnite",
    "gta 5",
    "gta 6",
    "call of duty",
    "black ops",
    "brawl stars",
    "rainbow six",
    "gameplay",
    "gaming",
    "esports",
    "goty",

    # MOVIES / TV
    "official trailer",
    "official teaser",
    "movie trailer",
    "season 2",
    "season 3",
    "netflix",
    "marvel",
    "anime",

    # SPORTS
    "vs ",
    " vs.",
    "match highlights",
    "highlights",
    "lck",

    # LIVESTREAM
    "#live",
    "🔴live",

]


def hard_filter_topic(topic):

    text = topic.lower().strip()

    for keyword in BAD_KEYWORDS:

        if keyword in text:

            return False

    return True


# ==========================================
# JUDGE ALL TOPICS IN ONE REQUEST
# ==========================================

def judge_topics(topics):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE V2")
    print("================================")
    print()

    # ======================================
    # HARD FILTER
    # ======================================

    clean_topics = []

    for topic in topics:

        if hard_filter_topic(topic):

            clean_topics.append(topic)

        else:

            print(
                f"🚫 Hard filtered: {topic}"
            )

    print()

    print(
        f"📥 Original topics: {len(topics)}"
    )

    print(
        f"🧹 After hard filter: "
        f"{len(clean_topics)}"
    )

    if not clean_topics:

        return []

    # ======================================
    # PREPARE TOPICS
    # ======================================

    numbered_topics = []

    for index, topic in enumerate(
        clean_topics,
        start=1
    ):

        numbered_topics.append(
            f"{index}. {topic}"
        )

    topics_text = "\n".join(
        numbered_topics
    )

    # ======================================
    # GEMINI PROMPT
    # ======================================

    prompt = f"""
{SYSTEM_PROMPT}

Analyze ALL topics below.

IMPORTANT:

Return exactly ONE JSON object for EACH topic.

Keep the original topic text exactly.

Do not invent missing context.

Topics:

{topics_text}
"""

    try:

        print(
            "🚀 Sending all topics "
            "in ONE Gemini request..."
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text.strip()

        # ==================================
        # CLEAN JSON
        # ==================================

        if text.startswith("```"):

            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

        results = json.loads(
            text
        )

        # ==================================
        # VALIDATE
        # ==================================

        if not isinstance(
            results,
            list
        ):

            print(
                "⚠️ Gemini returned "
                "non-list JSON"
            )

            return []

        validated = []

        for result in results:

            if not isinstance(
                result,
                dict
            ):

                continue

            topic = result.get(
                "topic",
                ""
            )

            # --------------------------------
            # REQUIRED FIELDS
            # --------------------------------

            result.setdefault(
                "is_good_for_shorts",
                False
            )

            result.setdefault(
                "category",
                "other"
            )

            result.setdefault(
                "global_interest",
                0
            )

            result.setdefault(
                "viral_potential",
                0
            )

            result.setdefault(
                "english_audience",
                0
            )

            result.setdefault(
                "story_potential",
                0
            )

            result.setdefault(
                "specificity",
                0
            )

            result.setdefault(
                "originality",
                0
            )

            result.setdefault(
                "score",
                0
            )

            result.setdefault(
                "reason",
                ""
            )

            # ==================================
            # FORCE INTEGER SCORES
            # ==================================

            score_fields = [

                "global_interest",
                "viral_potential",
                "english_audience",
                "story_potential",
                "specificity",
                "originality",
                "score"

            ]

            for field in score_fields:

                try:

                    result[field] = int(
                        result[field]
                    )

                except:

                    result[field] = 0

            # ==================================
            # CLAMP SCORES
            # ==================================

            for field in score_fields:

                if field == "score":

                    result[field] = max(
                        0,
                        min(
                            100,
                            result[field]
                        )
                    )

                else:

                    result[field] = max(
                        0,
                        min(
                            10,
                            result[field]
                        )
                    )

            # ==================================
            # FINAL SAFETY FILTER
            # ==================================

            if not topic:

                continue

            if not hard_filter_topic(
                topic
            ):

                result[
                    "is_good_for_shorts"
                ] = False

                result["score"] = 0

            # ==================================
            # REJECT LOW SPECIFICITY
            # ==================================

            if result[
                "specificity"
            ] < 5:

                result[
                    "is_good_for_shorts"
                ] = False

            # ==================================
            # REJECT LOW STORY POTENTIAL
            # ==================================

            if result[
                "story_potential"
            ] < 5:

                result[
                    "is_good_for_shorts"
                ] = False

            # ==================================
            # REJECT LOW ORIGINALITY
            # ==================================

            if result[
                "originality"
            ] < 5:

                result[
                    "is_good_for_shorts"
                ] = False

            # ==================================
            # REJECT LOW SCORE
            # ==================================

            if result[
                "score"
            ] < 60:

                result[
                    "is_good_for_shorts"
                ] = False

            validated.append(
                result
            )

        # ==================================
        # SORT
        # ==================================

        validated.sort(
            key=lambda item:
                item.get(
                    "score",
                    0
                ),
            reverse=True
        )

        # ==================================
        # PRINT RESULTS
        # ==================================

        print()
        print(
            "================================"
        )

        print(
            "📊 AI JUDGE COMPLETE"
        )

        print(
            "================================"
        )

        print(
            f"📥 Analyzed: "
            f"{len(validated)}"
        )

        approved = [

            item
            for item in validated
            if item.get(
                "is_good_for_shorts",
                False
            )

        ]

        print(
            f"✅ Approved: "
            f"{len(approved)}"
        )

        print(
            f"❌ Rejected: "
            f"{len(validated) - len(approved)}"
        )

        print()

        # ==================================
        # TOP APPROVED
        # ==================================

        print(
            "🔥 AI APPROVED TRENDS"
        )

        print(
            "================================"
        )

        for index, item in enumerate(
            approved[:10],
            start=1
        ):

            print(
                f"#{index} "
                f"{item.get('topic')}"
            )

            print(
                f"   Score: "
                f"{item.get('score')}/100"
            )

            print(
                f"   Category: "
                f"{item.get('category')}"
            )

            print(
                f"   Global: "
                f"{item.get('global_interest')}/10"
            )

            print(
                f"   Viral: "
                f"{item.get('viral_potential')}/10"
            )

            print(
                f"   Story: "
                f"{item.get('story_potential')}/10"
            )

            print(
                f"   Specificity: "
                f"{item.get('specificity')}/10"
            )

            print(
                f"   Originality: "
                f"{item.get('originality')}/10"
            )

            print(
                f"   Reason: "
                f"{item.get('reason')}"
            )

            print()

        return approved

    except Exception as error:

        print(
            f"❌ AI Judge error: {error}"
        )

        return []
