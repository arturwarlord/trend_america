import os
import json
import re
import time

from google import genai


# =========================================================
# GEMINI
# =========================================================

API_KEY = os.getenv("GEMINI_KEY")

if not API_KEY:
    raise RuntimeError(
        "❌ GEMINI_KEY is not configured"
    )

client = genai.Client(
    api_key=API_KEY
)

MODEL_NAME = "gemini-3.5-flash-lite"


# =========================================================
# SETTINGS
# =========================================================

BATCH_SIZE = 10

# Минимальный AI score
MIN_SCORE = 60

# Минимальные требования
MIN_SPECIFICITY = 4
MIN_FACTUAL_CONFIDENCE = 5
MIN_STORY_POTENTIAL = 5

# Минимальные глобальные показатели
MIN_GLOBAL_INTEREST = 5
MIN_ENGLISH_AUDIENCE = 5
MIN_ORIGINALITY = 5


# =========================================================
# HARD BLOCK KEYWORDS
# =========================================================
#
# Эти категории AI не должен пропускать даже если
# они имеют высокий viral potential.
#

HARD_BLOCK_KEYWORDS = {

    # -------------------------
    # GAMING
    # -------------------------

    "minecraft",
    "roblox",
    "fortnite",
    "gta",
    "grand theft auto",
    "valorant",
    "league of legends",
    "lol esports",
    "dota",
    "dota 2",
    "counter strike",
    "counter-strike",
    "cs2",
    "call of duty",
    "warzone",
    "brawl stars",
    "clash royale",
    "pokemon go",
    "gameplay",
    "walkthrough",
    "lets play",
    "let's play",
    "gaming",
    "esports",
    "speedrun",
    "game trailer",
    "gameplay trailer",

    # -------------------------
    # MUSIC
    # -------------------------

    "official music video",
    "music video",
    "lyric video",
    "lyrics",
    "dance practice",
    "official audio",
    "song",
    "new song",
    "album",
    "new album",
    "single",
    "remix",
    "live performance",
    "music battle",

    # -------------------------
    # ENTERTAINMENT
    # -------------------------

    "movie trailer",
    "official trailer",
    "teaser trailer",
    "anime",
    "episode",
    "season trailer",
    "tv trailer",
    "reaction",
    "reaction video",
    "livestream",
    "live stream",
    "fan edit",
    "fan content",

    # -------------------------
    # SPORTS MATCHES
    # -------------------------

    "vs",
    " v ",
    "match",
    "game highlights",
    "match highlights",
    "highlights",
    "quarterfinal",
    "semifinal",
    "final match",
    "tournament",

}


# =========================================================
# HARD BLOCK PHRASES
# =========================================================

HARD_BLOCK_PHRASES = [

    "official music video",
    "music video",
    "lyric video",
    "dance practice",

    "gameplay",
    "let's play",
    "lets play",
    "game trailer",

    "movie trailer",
    "official trailer",
    "teaser trailer",

    "reaction video",
    "fan edit",
    "livestream",
    "live stream",

]


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = r"""
You are V8 of an expert global YouTube Shorts trend judge.

Your job is to evaluate TRENDING TOPICS and decide whether
they can become ORIGINAL English informational YouTube Shorts.

The input usually comes from Google Trends and YouTube Trends.

IMPORTANT:

You are judging the TREND, not writing the final Short.

The title may be extremely short.

Examples:

"NASA"
"Tesla"
"Google Pixel"
"Home Alone"
"Apple"
"OpenAI"
"Bitcoin"
"SpaceX"

A short title does NOT automatically mean the topic is useless.

However, you must NOT invent a specific event that is not
reasonably indicated by the topic.

========================================================
CORE GOAL
========================================================

We want topics that can eventually become:

HOOK
→ surprising fact
→ explanation
→ escalation
→ payoff

The final video will be researched before the script is written.

Therefore the topic only needs to have a realistic researchable
story path.

We are NOT trying to reproduce the trending video.

We want to create an ORIGINAL informational Short.

========================================================
WHAT MAKES A GOOD TOPIC
========================================================

Strong categories include:

- technology
- AI
- science
- space
- discoveries
- psychology
- human behavior
- engineering
- inventions
- business
- economics
- history
- future technology
- unusual real-world events
- major world events
- factual mysteries
- strange places
- surprising human behavior
- important companies/products when there is realistic
  research potential

========================================================
SHORT TITLES
========================================================

DO NOT punish a topic simply because the title is short.

For example:

"Google Pixel"

This is a recognizable global technology/product topic.

It does NOT tell us the exact current story.

Therefore:

global_interest can be high
viral_potential can be high
english_audience can be high
originality can be high
specificity can be moderate
story_potential can be moderate/high
factual_confidence can still be high

But do NOT invent:

"Google Pixel launched satellite messaging"

unless the title itself actually indicates that.

Instead, evaluate:

"Major global technology/product topic with many
researchable current-story possibilities."

========================================================
ENTITY VS VAGUE ENTERTAINMENT
========================================================

A famous company, technology product, scientific organization,
space organization, or historical subject is NOT automatically
bad because it is short.

Examples that can be useful:

"NASA"
"SpaceX"
"Tesla"
"OpenAI"
"Google Pixel"
"Apple"
"Bitcoin"
"James Webb"
"AI"

These can have strong global interest.

However, purely entertainment-oriented entities should be
treated much more carefully.

Examples:

"That Way"
"Pop Off Pop Off"
"Big Walk"

These are too vague and should normally be rejected.

========================================================
HOME ALONE EXAMPLE
========================================================

"HOME ALONE" is a famous movie.

A movie title alone should NOT automatically receive a high
score merely because the movie is popular.

However, it can potentially lead to an ORIGINAL factual Short
if there is a real-world angle such as:

- production history
- unusual filming facts
- historical context
- real locations
- business impact
- cultural phenomenon

Therefore it may receive moderate scores.

But because the title itself does not indicate which factual
story is trending, specificity should remain moderate.

Do NOT invent a specific fact.

========================================================
COMPANIES AND PRODUCTS
========================================================

A company/product keyword can be useful.

Examples:

"Tesla"
"Apple"
"Google Pixel"
"OpenAI"
"Microsoft"
"Samsung"

Do NOT assume a specific announcement.

Evaluate the general research potential.

If it is a major global entity:

global_interest may be 7-10
english_audience may be 7-10

Specificity depends on how much the title tells us.

========================================================
AI TOPICS
========================================================

AI is a high-value category.

Examples:

"OpenAI"
"Gemini"
"Claude"
"ChatGPT"
"AI agents"

These can be strong because the subject has high global
interest and many factual story opportunities.

Again:

DO NOT invent a specific announcement.

========================================================
SCIENCE / SPACE
========================================================

Science and space are high-value categories.

Examples:

"NASA"
"James Webb"
"Black hole"
"Mars"
"solar storm"

These can be strong because they naturally create curiosity.

========================================================
BUSINESS
========================================================

Business topics can be good when they have a real-world
researchable angle.

Examples:

"Tesla"
"Bitcoin"
"Amazon"
"Spotify"
"Ticketmaster"

A company name alone is less specific than:

"Spotify changes royalty system"

But the company name can still have significant global interest.

========================================================
HISTORY
========================================================

Historical subjects can be useful if they have a clear
researchable story.

Examples:

"Titanic"
"Roman Empire"
"Cold War"
"Pompeii"

However, generic entertainment content should not be confused
with historical content.

========================================================
BAD CONTENT
========================================================

Strongly reject:

- gaming
- gameplay
- Minecraft
- Roblox
- Fortnite
- GTA
- esports
- gaming tournaments
- music videos
- songs
- albums
- lyric videos
- dance practice
- movie trailers
- TV trailers
- anime
- fictional characters
- fictional stories
- reaction videos
- livestreams
- fan content
- sports matches
- sports highlights
- random celebrity gossip
- vague memes
- meaningless entertainment titles

========================================================
SPORTS EXCEPTION
========================================================

Sports are normally rejected.

But a real-world factual sports story can sometimes be useful.

Examples:

"athlete breaks world record"

"historic Olympic controversy"

"football club financial scandal"

These can be useful.

But:

"T1 vs DK"

"Real Madrid vs Barcelona"

must be rejected.

========================================================
MUSIC EXCEPTION
========================================================

Music content is normally rejected.

But real-world music industry stories can be useful.

Example:

"Spotify changes royalty system"

Potentially GOOD.

But:

"Spotify"

is only a company/entity keyword and should have lower
specificity than a clearly defined event.

========================================================
MOVIE / ENTERTAINMENT EXCEPTION
========================================================

Reject:

movie trailers
anime
fictional characters
fictional stories

But real-world entertainment industry events may be useful.

Example:

"Hollywood actors strike"

Potentially GOOD.

========================================================
GLOBAL AUDIENCE
========================================================

The final Short is English.

Prefer subjects that can interest viewers in multiple countries.

High value:

technology
AI
science
space
money
business
psychology
history
engineering
major global events
surprising discoveries

Lower value:

local influencers
local TV personalities
local fandom
local-language entertainment
obscure local events

========================================================
STORY POTENTIAL
========================================================

Ask:

Can this topic reasonably lead to:

Why is this trending?

What happened?

Why does it matter?

How does it work?

What changed?

What surprising fact is connected to it?

If YES, story_potential should generally be 5 or higher.

A short entity name can still have story potential.

========================================================
SPECIFICITY
========================================================

Specificity does NOT mean:

"Is the entire story already contained in the title?"

Instead:

"Does the title identify a recognizable subject that can
reasonably be researched?"

Examples:

"Google Pixel"

specificity: 4-6

"Google Pixel satellite messaging"

specificity: 7-9

"Something happened"

specificity: 1-2

"That Way"

specificity: 1-3

========================================================
FACTUAL CONFIDENCE
========================================================

This measures whether the topic represents a real-world
researchable subject.

A famous company can have high factual confidence.

A vague meme can have low factual confidence.

Do NOT confuse factual confidence with knowing the exact
current event.

========================================================
ORIGINALITY
========================================================

Ask:

Can we create an original informational Short from this topic?

High-quality informational subjects should usually score 6-10.

Gaming/music/fan content should be low.

========================================================
SCORING
========================================================

Give each value from 0 to 10.

global_interest
viral_potential
english_audience
story_potential
specificity
factual_confidence
originality

Do NOT make all scores low merely because a topic is short.

========================================================
SCORE EXAMPLES
========================================================

"Google Pixel"

Possible:

global_interest: 8
viral_potential: 7
english_audience: 9
story_potential: 6
specificity: 5
factual_confidence: 8
originality: 8

This can be approved if the total score passes the threshold.

"NASA"

Possible:

global_interest: 9
viral_potential: 8
english_audience: 10
story_potential: 7
specificity: 5
factual_confidence: 10
originality: 8

Potentially approved.

"That Way"

Possible:

global_interest: 2
viral_potential: 5
english_audience: 4
story_potential: 1
specificity: 1
factual_confidence: 2
originality: 2

Reject.

"Minecraft gameplay"

Reject.

"Spotify changes royalty system"

Potentially strong.

========================================================
CATEGORY
========================================================

Use exactly one:

technology
ai
science
space
psychology
business
history
engineering
future
discovery
world
mystery
other

========================================================
DECISION
========================================================

Set is_good_for_shorts to TRUE when the topic has a realistic
path toward an original informational Short.

Do not require the exact final story to already be visible
in the title.

But reject clearly unsuitable content.

========================================================
IMPORTANT
========================================================

Do not invent facts.

Do not rewrite the topic.

Do not merge topics.

Preserve the original topic exactly.

========================================================
OUTPUT
========================================================

Return ONLY valid JSON.

Return an array.

The array MUST contain exactly one object per input topic.

No markdown.

No code fences.

No explanations outside JSON.

Each object:

{
    "topic": "original topic",
    "is_good_for_shorts": true,
    "category": "technology",

    "global_interest": 8,
    "viral_potential": 8,
    "english_audience": 9,
    "story_potential": 7,
    "specificity": 6,
    "factual_confidence": 8,
    "originality": 8,

    "reason": "Short explanation."
}

========================================================
FINAL RULE
========================================================

The program will calculate the final score itself.

Your boolean decision is advisory only.

Be balanced.

Do NOT reject a globally important entity merely because
the trend title is short.

Do NOT approve meaningless entertainment merely because
it is trending.
"""


# =========================================================
# CLEAN JSON
# =========================================================

def clean_json(text):

    if not text:
        return ""

    text = text.strip()

    # Remove markdown fences
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # Find JSON array
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text.strip()


# =========================================================
# FAILED RESULT
# =========================================================

def failed_result(
    topic,
    reason="AI Judge failed"
):

    return {

        "topic": topic,

        "is_good_for_shorts": False,

        "category": "other",

        "global_interest": 0,
        "viral_potential": 0,
        "english_audience": 0,
        "story_potential": 0,
        "specificity": 0,
        "factual_confidence": 0,
        "originality": 0,

        "score": 0,

        "reason": reason

    }


# =========================================================
# NORMALIZE NUMBER
# =========================================================

def normalize_number(value):

    try:

        value = float(value)

    except Exception:

        return 0

    if value < 0:

        return 0

    if value > 10:

        return 10

    return value


# =========================================================
# NORMALIZE CATEGORY
# =========================================================

VALID_CATEGORIES = {

    "technology",
    "ai",
    "science",
    "space",
    "psychology",
    "business",
    "history",
    "engineering",
    "future",
    "discovery",
    "world",
    "mystery",
    "other"

}


def normalize_category(
    value
):

    if not isinstance(
        value,
        str
    ):

        return "other"

    value = value.strip().lower()

    if value in VALID_CATEGORIES:

        return value

    return "other"


# =========================================================
# TEXT BLOCK CHECK
# =========================================================

def contains_blocked_content(
    topic
):

    if not topic:

        return False

    normalized = str(
        topic
    ).lower()

    # Exact phrase checks
    for phrase in HARD_BLOCK_PHRASES:

        if phrase in normalized:

            return True

    # Keyword checks
    words = re.findall(
        r"\b[\w'-]+\b",
        normalized
    )

    word_set = set(
        words
    )

    for keyword in HARD_BLOCK_KEYWORDS:

        if " " in keyword:

            if keyword in normalized:

                return True

        else:

            if keyword in word_set:

                return True

    return False


# =========================================================
# ENTITY QUALITY BOOST
# =========================================================

#
# These are globally recognizable subjects.
#
# We do NOT use these to invent facts.
# They only help prevent short global entities from being
# unfairly scored as useless.
#

GLOBAL_ENTITIES = {

    "nasa",
    "spacex",
    "tesla",
    "apple",
    "google",
    "microsoft",
    "amazon",
    "openai",
    "chatgpt",
    "gemini",
    "claude",
    "meta",
    "samsung",
    "iphone",
    "google pixel",
    "bitcoin",
    "ethereum",
    "paypal",
    "netflix",
    "spotify",
    "tiktok",
    "instagram",
    "youtube",
    "mars",
    "moon",
    "james webb",
    "james webb telescope",
    "black hole",
    "ai",
    "artificial intelligence",
    "climate change",
    "titanic",
    "roman empire",
    "cold war",
    "pompeii"

}


def is_global_entity(
    topic
):

    normalized = re.sub(
        r"\s+",
        " ",
        str(topic).strip().lower()
    )

    return normalized in GLOBAL_ENTITIES


# =========================================================
# CALCULATE SCORE
# =========================================================

def calculate_score(
    result
):

    global_interest = normalize_number(
        result.get(
            "global_interest",
            0
        )
    )

    viral_potential = normalize_number(
        result.get(
            "viral_potential",
            0
        )
    )

    english_audience = normalize_number(
        result.get(
            "english_audience",
            0
        )
    )

    story_potential = normalize_number(
        result.get(
            "story_potential",
            0
        )
    )

    specificity = normalize_number(
        result.get(
            "specificity",
            0
        )
    )

    factual_confidence = normalize_number(
        result.get(
            "factual_confidence",
            0
        )
    )

    originality = normalize_number(
        result.get(
            "originality",
            0
        )
    )

    # =====================================================
    # WEIGHTS
    # =====================================================

    score = (

        global_interest * 0.15

        +

        viral_potential * 0.15

        +

        english_audience * 0.10

        +

        story_potential * 0.20

        +

        specificity * 0.15

        +

        factual_confidence * 0.15

        +

        originality * 0.10

    ) * 10

    return round(
        score,
        2
    )


# =========================================================
# VALIDATE RESULT
# =========================================================

def validate_result(
    result,
    original_topic
):

    if not isinstance(
        result,
        dict
    ):

        return failed_result(
            original_topic,
            "Invalid AI result"
        )

    # =====================================================
    # ALWAYS PRESERVE ORIGINAL TOPIC
    # =====================================================

    result["topic"] = original_topic

    # =====================================================
    # CATEGORY
    # =====================================================

    result["category"] = normalize_category(
        result.get(
            "category",
            "other"
        )
    )

    # =====================================================
    # NUMERIC FIELDS
    # =====================================================

    numeric_fields = [

        "global_interest",
        "viral_potential",
        "english_audience",
        "story_potential",
        "specificity",
        "factual_confidence",
        "originality"

    ]

    for field in numeric_fields:

        result[field] = normalize_number(
            result.get(
                field,
                0
            )
        )

    # =====================================================
    # CALCULATE SCORE
    # =====================================================

    result["score"] = calculate_score(
        result
    )

    # =====================================================
    # HARD RULES
    # =====================================================

    approved = True

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    if result["score"] < MIN_SCORE:

        approved = False

    # -----------------------------------------------------
    # SPECIFICITY
    # -----------------------------------------------------

    if result["specificity"] < MIN_SPECIFICITY:

        approved = False

    # -----------------------------------------------------
    # FACTUAL CONFIDENCE
    # -----------------------------------------------------

    if result["factual_confidence"] < MIN_FACTUAL_CONFIDENCE:

        approved = False

    # -----------------------------------------------------
    # STORY POTENTIAL
    # -----------------------------------------------------

    if result["story_potential"] < MIN_STORY_POTENTIAL:

        approved = False

    # -----------------------------------------------------
    # GLOBAL INTEREST
    # -----------------------------------------------------

    if result["global_interest"] < MIN_GLOBAL_INTEREST:

        approved = False

    # -----------------------------------------------------
    # ENGLISH AUDIENCE
    # -----------------------------------------------------

    if result["english_audience"] < MIN_ENGLISH_AUDIENCE:

        approved = False

    # -----------------------------------------------------
    # ORIGINALITY
    # -----------------------------------------------------

    if result["originality"] < MIN_ORIGINALITY:

        approved = False

    # =====================================================
    # HARD CONTENT BLOCK
    # =====================================================

    if contains_blocked_content(
        original_topic
    ):

        approved = False

        result["reason"] = (
            "Rejected by hard content filter: "
            "gaming, music, entertainment, "
            "sports match, trailer, or fan content."
        )

    # =====================================================
    # GLOBAL ENTITY SAFETY NET
    # =====================================================

    #
    # Important:
    #
    # If Gemini gives a globally important entity reasonable
    # scores, do not artificially reject it merely because
    # the title is short.
    #
    # We still respect the factual/story requirements.
    #

    if is_global_entity(
        original_topic
    ):

        if (
            result["global_interest"] >= 7
            and
            result["english_audience"] >= 7
            and
            result["factual_confidence"] >= 6
            and
            result["story_potential"] >= 5
            and
            result["originality"] >= 5
        ):

            # Specificity floor for recognized entities
            if result["specificity"] >= 4:

                if result["score"] >= 55:

                    approved = True

    # =====================================================
    # DO NOT TRUST GEMINI BOOLEAN
    # =====================================================

    result["is_good_for_shorts"] = approved

    return result


# =========================================================
# MATCH RESULTS TO TOPICS
# =========================================================

def match_results_to_topics(
    topics,
    data
):

    if not isinstance(
        data,
        list
    ):

        raise ValueError(
            "Gemini response is not a list"
        )

    # -----------------------------------------------------
    # Normal case
    # -----------------------------------------------------

    if len(data) == len(topics):

        return data

    # -----------------------------------------------------
    # If Gemini accidentally returned fewer items
    # -----------------------------------------------------

    print(
        f"⚠️ Gemini returned "
        f"{len(data)} results for "
        f"{len(topics)} topics"
    )

    results = []

    used_indexes = set()

    # -----------------------------------------------------
    # Try exact topic matching first
    # -----------------------------------------------------

    for topic in topics:

        matched = None

        for index, item in enumerate(
            data
        ):

            if index in used_indexes:

                continue

            if not isinstance(
                item,
                dict
            ):

                continue

            candidate = item.get(
                "topic",
                ""
            )

            if candidate == topic:

                matched = item

                used_indexes.add(
                    index
                )

                break

        if matched is None:

            results.append(
                failed_result(
                    topic,
                    "Missing AI result"
                )
            )

        else:

            results.append(
                matched
            )

    return results


# =========================================================
# GEMINI BATCH
# =========================================================

def judge_batch(
    topics,
    batch_number,
    total_batches
):

    print(
        f"🚀 Gemini V8 batch request "
        f"{batch_number}/{total_batches}"
    )

    topics_text = "\n".join(

        f"{index + 1}. {topic}"

        for index, topic
        in enumerate(topics)

    )

    prompt = f"""
{SYSTEM_PROMPT}

========================================================
INPUT TOPICS
========================================================

Analyze ALL topics below.

There are exactly {len(topics)} topics.

TOPICS:

{topics_text}

========================================================
STRICT OUTPUT REQUIREMENTS
========================================================

Return exactly {len(topics)} JSON objects.

The order MUST be identical to the input order.

Do not remove any topic.

Do not merge topics.

Do not rewrite topics.

Preserve every original topic exactly.

Return ONLY the JSON array.
"""

    try:

        response = client.models.generate_content(

            model=MODEL_NAME,

            contents=prompt

        )

        text = response.text

        if not text:

            print(
                "⚠️ Gemini returned empty response"
            )

            return [

                failed_result(
                    topic,
                    "Empty Gemini response"
                )

                for topic in topics

            ]

        text = clean_json(
            text
        )

        try:

            data = json.loads(
                text
            )

        except json.JSONDecodeError as error:

            print(
                "⚠️ JSON decode error:"
            )

            print(
                str(error)
            )

            print(
                "Gemini raw response:"
            )

            print(
                text[:3000]
            )

            return [

                failed_result(
                    topic,
                    "Invalid Gemini JSON"
                )

                for topic in topics

            ]

        data = match_results_to_topics(
            topics,
            data
        )

        results = []

        for index, topic in enumerate(
            topics
        ):

            if index < len(data):

                result = data[index]

            else:

                result = failed_result(
                    topic,
                    "Missing AI result"
                )

            result = validate_result(
                result,
                topic
            )

            results.append(
                result
            )

        return results

    except Exception as error:

        print()
        print(
            "⚠️ Gemini V8 batch error:"
        )
        print(
            str(error)
        )
        print()

        return [

            failed_result(
                topic,
                "Gemini request failed"
            )

            for topic in topics

        ]


# =========================================================
# JUDGE MULTIPLE TOPICS
# =========================================================

def judge_topics(
    topics
):

    print()
    print(
        "================================"
    )
    print(
        "🤖 AI TREND JUDGE V8"
    )
    print(
        "================================"
    )
    print()

    # =====================================================
    # VALIDATE INPUT
    # =====================================================

    if not topics:

        print(
            "❌ No topics received"
        )

        return []

    # -----------------------------------------------------
    # Remove invalid values
    # -----------------------------------------------------

    clean_topics = []

    for topic in topics:

        if not isinstance(
            topic,
            str
        ):

            continue

        topic = topic.strip()

        if not topic:

            continue

        clean_topics.append(
            topic
        )

    # -----------------------------------------------------
    # Remove duplicates while preserving order
    # -----------------------------------------------------

    unique_topics = []

    seen = set()

    for topic in clean_topics:

        key = topic.lower()

        if key in seen:

            continue

        seen.add(
            key
        )

        unique_topics.append(
            topic
        )

    topics = unique_topics

    print(
        f"📊 Topics for AI Judge: "
        f"{len(topics)}"
    )

    print()

    if not topics:

        return []

    # =====================================================
    # LOCAL PRE-FILTER
    # =====================================================

    #
    # We still send blocked topics to Gemini so that the
    # output remains exactly aligned, but they are guaranteed
    # to be rejected afterwards.
    #

    blocked_count = 0

    for topic in topics:

        if contains_blocked_content(
            topic
        ):

            blocked_count += 1

    if blocked_count:

        print(
            f"🚫 Hard-block candidates: "
            f"{blocked_count}"
        )

        print()

    # =====================================================
    # SPLIT INTO BATCHES
    # =====================================================

    batches = [

        topics[
            index:index + BATCH_SIZE
        ]

        for index in range(
            0,
            len(topics),
            BATCH_SIZE
        )

    ]

    total_batches = len(
        batches
    )

    # =====================================================
    # PROCESS BATCHES
    # =====================================================

    results = []

    for batch_index, batch in enumerate(

        batches,

        start=1

    ):

        batch_results = judge_batch(

            batch,

            batch_index,

            total_batches

        )

        results.extend(
            batch_results
        )

        # =================================================
        # DELAY
        # =================================================

        if batch_index < total_batches:

            time.sleep(
                3
            )

    # =====================================================
    # FINAL HARD VALIDATION
    # =====================================================

    final_results = []

    for index, topic in enumerate(
        topics
    ):

        if index < len(results):

            result = results[index]

        else:

            result = failed_result(
                topic,
                "Missing final result"
            )

        result = validate_result(
            result,
            topic
        )

        final_results.append(
            result
        )

    results = final_results

    # =====================================================
    # SORT
    # =====================================================

    results.sort(

        key=lambda item:
            item.get(
                "score",
                0
            ),

        reverse=True

    )

    # =====================================================
    # PRINT RESULTS
    # =====================================================

    print()
    print(
        "================================"
    )
    print(
        "🤖 AI JUDGE V8 RESULTS"
    )
    print(
        "================================"
    )
    print()

    approved_count = 0

    for index, result in enumerate(

        results,

        start=1

    ):

        approved = result.get(

            "is_good_for_shorts",

            False

        )

        if approved:

            approved_count += 1

        status = (

            "✅ APPROVED"

            if approved

            else

            "❌ REJECTED"

        )

        print(
            f"🤖 [{index}/{len(results)}] "
            f"{result.get('topic', '')}"
        )

        print(
            f"   {status}"
        )

        print(
            f"   Score: "
            f"{result.get('score', 0):.0f}/100"
        )

        print(
            f"   Category: "
            f"{result.get('category', 'other')}"
        )

        print(
            f"   Global: "
            f"{result.get('global_interest', 0):.0f}/10"
        )

        print(
            f"   Viral: "
            f"{result.get('viral_potential', 0):.0f}/10"
        )

        print(
            f"   English: "
            f"{result.get('english_audience', 0):.0f}/10"
        )

        print(
            f"   Story: "
            f"{result.get('story_potential', 0):.0f}/10"
        )

        print(
            f"   Specificity: "
            f"{result.get('specificity', 0):.0f}/10"
        )

        print(
            f"   Facts: "
            f"{result.get('factual_confidence', 0):.0f}/10"
        )

        print(
            f"   Originality: "
            f"{result.get('originality', 0):.0f}/10"
        )

        print(
            f"   Reason: "
            f"{result.get('reason', '')}"
        )

        print()

    print(
        f"✅ AI approved: "
        f"{approved_count}/{len(results)}"
    )

    print()

    return results


# =========================================================
# OPTIONAL DIRECT TEST
# =========================================================

if __name__ == "__main__":

    test_topics = [

        "HOME ALONE",
        "Google Pixel",
        "NASA",
        "OpenAI",
        "Tesla",
        "Minecraft gameplay",
        "That Way",
        "Pop Off Pop Off",
        "Big Walk",
        "Spotify changes royalty system"

    ]

    results = judge_topics(
        test_topics
    )

    print()
    print(
        "================================"
    )
    print(
        "🧪 TEST COMPLETE"
    )
    print(
        "================================"
    )

    print(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        )
    )
