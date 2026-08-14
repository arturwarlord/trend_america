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


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "gemini-3.5-flash-lite"


# =========================================================
# SETTINGS
# =========================================================

BATCH_SIZE = 10

TARGET_APPROVED = 10

MAX_RETRIES = 3

RETRY_DELAY = 3

MIN_SCORE = 60

MIN_SPECIFICITY = 5

MIN_FACTUAL_CONFIDENCE = 5

MIN_STORY_POTENTIAL = 5


# =========================================================
# HARD BLOCK KEYWORDS
# =========================================================

HARD_BLOCK_PATTERNS = [

    # ==============================================
    # GAMING
    # ==============================================

    r"\bminecraft\b",
    r"\broblox\b",
    r"\bfortnite\b",
    r"\bgta\b",
    r"\bgta v\b",
    r"\bgta 5\b",
    r"\bgrand theft auto\b",
    r"\bbrawl stars\b",
    r"\bclash royale\b",
    r"\bleague of legends\b",
    r"\bvalorant\b",
    r"\bcall of duty\b",
    r"\bpubg\b",
    r"\bfree fire\b",
    r"\bgameplay\b",
    r"\bgame play\b",
    r"\bgaming\b",
    r"\besports\b",
    r"\bgame server\b",
    r"\bserver\b.*\bgame\b",
    r"\bgame\b.*\bserver\b",

    # ==============================================
    # MUSIC
    # ==============================================

    r"\bdance practice\b",
    r"\bmusic video\b",
    r"\bofficial mv\b",
    r"\bofficial music video\b",
    r"\blyric video\b",
    r"\blyrics\b",
    r"\bdance video\b",
    r"\bsong\b",
    r"\bsingle\b",
    r"\balbum\b",
    r"\bremix\b",
    r"\bkaraoke\b",
    r"\bconcert\b",
    r"\bperformance video\b",
    r"\bmusic battle\b",

    # ==============================================
    # ANIME / FICTION
    # ==============================================

    r"\banime\b",
    r"\bmanga\b",
    r"\bcartoon\b",
    r"\bfictional character\b",
    r"\bsuperhero\b",
    r"\bspiderman\b",
    r"\bbatman\b",
    r"\bsuperman\b",
    r"\bmarvel\b",
    r"\bdc comics\b",

    # ==============================================
    # TRAILERS
    # ==============================================

    r"\btrailer\b",
    r"\bteaser\b",
    r"\bteaser trailer\b",
    r"\bofficial trailer\b",

    # ==============================================
    # LIVESTREAM / REACTION / FAN
    # ==============================================

    r"\blive stream\b",
    r"\blivestream\b",
    r"\blive video\b",
    r"\breaction\b",
    r"\breacts\b",
    r"\breacting\b",
    r"\bfan video\b",
    r"\bfan edit\b",
    r"\bfan content\b",

    # ==============================================
    # SPORTS MATCHES
    # ==============================================

    r"\bvs\b",
    r"\bversus\b",
    r"\bmatch\b",
    r"\bgame today\b",
    r"\bhighlights\b",
    r"\bfinal score\b",
    r"\bscorecard\b",
    r"\btournament\b",

]


# =========================================================
# ENTERTAINMENT BLOCK
# =========================================================

ENTERTAINMENT_PATTERNS = [

    r"\bseason \d+\b",
    r"\bepisode \d+\b",
    r"\bep \d+\b",
    r"\bcast\b",
    r"\bcharacter\b",
    r"\bmovie\b",
    r"\bfilm\b",
    r"\btv show\b",
    r"\bseries\b",
    r"\banimation\b",
    r"\bnetflix series\b",
    r"\bdisney\b",
    r"\bdisney plus\b",
    r"\bprime video\b",

]


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate TRENDING TOPICS for an automated
English YouTube Shorts channel.

The final Shorts are ORIGINAL informational videos.

They may explain:

- technology
- AI
- science
- space
- psychology
- business
- economics
- history
- engineering
- discoveries
- unusual real-world events
- strange places
- factual mysteries
- major world events
- surprising human behavior
- future technology

==================================================
CRITICAL RULE
==================================================

The input is a TREND TITLE.

It may be short.

Do NOT require the entire story to be contained in the title.

However:

DO NOT INVENT a specific event, product update, statistic,
price, launch, discovery or claim that is not reasonably
indicated by the topic.

You are evaluating whether the topic is worth researching.

==================================================
GOOD EXAMPLES
==================================================

"NASA"

Potentially useful.

"NASA discovers water on Mars"

Much stronger.

"Google Pixel"

Potentially useful.

"Google Pixel satellite messaging"

Much stronger.

"OpenAI"

Potentially useful.

"OpenAI new AI model"

Stronger.

"Ticketmaster"

Potentially useful as a business subject,
but the exact story needs research.

==================================================
IMPORTANT
==================================================

A famous keyword does NOT automatically mean that the topic
is good.

For example:

"HOME ALONE"

Although famous, this is primarily entertainment/movie
content.

It should normally be rejected unless the title itself
clearly indicates a real-world historical, production,
business or cultural story.

Do NOT automatically invent:

"behind the scenes facts"

"filming locations"

"production history"

just because a movie is famous.

==================================================
REJECT
==================================================

Strongly reject:

gaming
video games
gameplay
Minecraft
Roblox
Fortnite
GTA
esports
music videos
songs
albums
dance practice
lyrics
anime
fictional characters
movie trailers
TV trailers
fan content
reaction content
livestreams
sports matches
sports highlights
generic celebrity content
vague entertainment
fiction

==================================================
SPORTS
==================================================

Reject ordinary sports matches.

Potentially accept REAL-WORLD sports stories such as:

"athlete breaks world record"

"historic Olympic controversy"

"football club financial scandal"

The title must indicate an actual story.

==================================================
MUSIC
==================================================

Reject songs, music videos, dance practices and performances.

Potentially accept real-world music industry stories such as:

"Spotify changes royalty system"

"music streaming revenue falls"

==================================================
ENTERTAINMENT
==================================================

Reject generic movie/show titles.

Potentially accept real-world industry stories such as:

"Hollywood actors strike"

"Netflix changes subscription policy"

But only when the title itself indicates the real-world story.

==================================================
GLOBAL AUDIENCE
==================================================

Prefer topics understandable and interesting to an English-speaking
global audience.

High value:

technology
AI
science
space
business
money
psychology
discoveries
major world events

Lower value:

local influencers
local entertainment
local fandom
local-language entertainment
obscure local personalities

==================================================
STORY POTENTIAL
==================================================

Ask:

Can this trend lead to:

HOOK
→ surprising information
→ explanation
→ escalation
→ payoff

Useful questions:

Why is this trending?

What happened?

Why does it matter?

How does it work?

What changed?

What surprising fact is connected to it?

==================================================
SCORING
==================================================

Give each value from 0 to 10.

global_interest
viral_potential
english_audience
story_potential
specificity
factual_confidence
originality

Do NOT make every short title low.

Example:

"Google Pixel"

global_interest: 8
viral_potential: 7
english_audience: 9
story_potential: 6
specificity: 4
factual_confidence: 8
originality: 7

However, specificity below the required threshold will
cause Python to reject it.

==================================================
CATEGORY
==================================================

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

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return an array.

Exactly one object per input topic.

Preserve the topic EXACTLY.

Do not rewrite the topic.

Do not add markdown.

Do not add explanations outside JSON.

Each object:

{
    "topic": "original topic",
    "is_good_for_shorts": false,
    "category": "other",
    "global_interest": 0,
    "viral_potential": 0,
    "english_audience": 0,
    "story_potential": 0,
    "specificity": 0,
    "factual_confidence": 0,
    "originality": 0,
    "reason": "Short explanation."
}

IMPORTANT:

Python will make the final approval decision.

Do not try to manipulate the final boolean.
"""


# =========================================================
# NORMALIZE TOPIC
# =========================================================

def normalize_topic(topic):

    if not topic:
        return ""

    return str(topic).strip()


# =========================================================
# HARD BLOCK CHECK
# =========================================================

def is_hard_blocked(topic):

    if not topic:
        return True

    text = topic.lower().strip()

    for pattern in HARD_BLOCK_PATTERNS:

        try:

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            ):

                return True

        except re.error:

            continue

    return False


# =========================================================
# ENTERTAINMENT CHECK
# =========================================================

def is_entertainment(topic):

    if not topic:
        return False

    text = topic.lower().strip()

    for pattern in ENTERTAINMENT_PATTERNS:

        try:

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE
            ):

                return True

        except re.error:

            continue

    return False


# =========================================================
# PRE-FILTER
# =========================================================

def pre_filter_topics(topics):

    allowed = []

    blocked = []

    for topic in topics:

        topic = normalize_topic(topic)

        if not topic:

            continue

        if is_hard_blocked(topic):

            blocked.append(topic)

            continue

        # ----------------------------------------------
        # Known entertainment-only names
        # ----------------------------------------------

        lower = topic.lower()

        entertainment_names = [

            "home alone",
            "stranger things",
            "avengers",
            "spiderman",
            "batman",
            "superman",
            "pokemon",
            "shinchan",
            "one piece",
            "naruto",
            "dragon ball",

        ]

        if lower in entertainment_names:

            blocked.append(topic)

            continue

        if is_entertainment(topic):

            blocked.append(topic)

            continue

        allowed.append(topic)

    return allowed, blocked


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

    # ----------------------------------------------
    # Find array
    # ----------------------------------------------

    start = text.find("[")

    end = text.rfind("]")

    if start != -1 and end != -1:

        text = text[
            start:end + 1
        ]

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
# CALCULATE SCORE
# =========================================================

def calculate_score(result):

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

    # ----------------------------------------------
    # ALWAYS preserve original topic
    # ----------------------------------------------

    result["topic"] = original_topic

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

    # ----------------------------------------------
    # Category
    # ----------------------------------------------

    allowed_categories = {

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

    category = result.get(
        "category",
        "other"
    )

    if category not in allowed_categories:

        category = "other"

    result["category"] = category

    # ----------------------------------------------
    # SCORE
    # ----------------------------------------------

    result["score"] = calculate_score(
        result
    )

    # ----------------------------------------------
    # HARD APPROVAL
    # ----------------------------------------------

    approved = True

    if result["specificity"] < MIN_SPECIFICITY:

        approved = False

    if result["factual_confidence"] < MIN_FACTUAL_CONFIDENCE:

        approved = False

    if result["story_potential"] < MIN_STORY_POTENTIAL:

        approved = False

    if result["score"] < MIN_SCORE:

        approved = False

    # ----------------------------------------------
    # FINAL DECISION
    # ----------------------------------------------

    result["is_good_for_shorts"] = approved

    return result


# =========================================================
# GEMINI REQUEST
# =========================================================

def request_gemini(
    prompt
):

    response = client.models.generate_content(

        model=MODEL_NAME,

        contents=prompt,

        config={

            "response_mime_type":
                "application/json"

        }

    )

    return response.text


# =========================================================
# PARSE RESPONSE
# =========================================================

def parse_response(
    text,
    topics
):

    cleaned = clean_json(
        text
    )

    if not cleaned:

        raise ValueError(
            "Gemini returned empty JSON"
        )

    try:

        data = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        print()
        print(
            "⚠️ JSON decode error:"
        )

        print(
            str(error)
        )

        print()
        print(
            "Gemini raw response:"
        )

        print(
            text[:8000]
        )

        print()

        raise

    if not isinstance(
        data,
        list
    ):

        raise ValueError(
            "Gemini response is not a list"
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


# =========================================================
# BUILD PROMPT
# =========================================================

def build_prompt(
    topics
):

    topics_text = "\n".join(

        f"{index + 1}. {topic}"

        for index, topic
        in enumerate(topics)

    )

    return f"""
{SYSTEM_PROMPT}

==================================================
TOPICS TO ANALYZE
==================================================

{topics_text}

==================================================
STRICT REQUIREMENTS
==================================================

There are exactly {len(topics)} topics.

Return exactly {len(topics)} objects.

The order MUST be identical.

Do not remove topics.

Do not merge topics.

Do not rewrite topics.

Preserve every topic EXACTLY.

Return valid JSON only.
"""


# =========================================================
# JUDGE BATCH
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

    prompt = build_prompt(
        topics
    )

    # ----------------------------------------------
    # RETRIES
    # ----------------------------------------------

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            text = request_gemini(
                prompt
            )

            results = parse_response(
                text,
                topics
            )

            return results

        except Exception as error:

            print()

            print(
                f"⚠️ Gemini attempt "
                f"{attempt}/{MAX_RETRIES} failed"
            )

            print(
                str(error)
            )

            print()

            if attempt < MAX_RETRIES:

                print(
                    f"🔄 Retrying in "
                    f"{RETRY_DELAY}s..."
                )

                time.sleep(
                    RETRY_DELAY
                )

    # ----------------------------------------------
    # FINAL FAILURE
    # ----------------------------------------------

    print(
        "❌ Gemini batch permanently failed"
    )

    return [

        failed_result(
            topic,
            "Gemini batch failed after retries"
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
        "🤖 AI TREND JUDGE V8.1"
    )

    print(
        "================================"
    )

    print()

    if not topics:

        print(
            "❌ No topics received"
        )

        return []

    # ----------------------------------------------
    # Remove duplicates
    # ----------------------------------------------

    unique_topics = []

    seen = set()

    for topic in topics:

        topic = normalize_topic(
            topic
        )

        key = topic.lower()

        if not topic:

            continue

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

    # ----------------------------------------------
    # PRE-FILTER
    # ----------------------------------------------

    allowed_topics, blocked_topics = (
        pre_filter_topics(
            topics
        )
    )

    print(
        f"🚫 Hard-block candidates: "
        f"{len(blocked_topics)}"
    )

    print(
        f"🧠 Topics sent to Gemini: "
        f"{len(allowed_topics)}"
    )

    # ----------------------------------------------
    # Results
    # ----------------------------------------------

    results = []

    # ----------------------------------------------
    # Add hard-block results
    # ----------------------------------------------

    for topic in blocked_topics:

        results.append(

            failed_result(

                topic,

                "Rejected by hard content filter: "
                "gaming, music, entertainment, sports match, "
                "trailer, or fan content."

            )

        )

    if not allowed_topics:

        results.sort(

            key=lambda item:
                item.get(
                    "score",
                    0
                ),

            reverse=True

        )

        return results

    # ----------------------------------------------
    # BATCHES
    # ----------------------------------------------

    batches = [

        allowed_topics[
            index:index + BATCH_SIZE
        ]

        for index in range(
            0,
            len(allowed_topics),
            BATCH_SIZE
        )

    ]

    total_batches = len(
        batches
    )

    # ----------------------------------------------
    # PROCESS
    # ----------------------------------------------

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

        if batch_index < total_batches:

            time.sleep(
                2
            )

    # ----------------------------------------------
    # SORT
    # ----------------------------------------------

    results.sort(

        key=lambda item:
            item.get(
                "score",
                0
            ),

        reverse=True

    )

    # ----------------------------------------------
    # PRINT
    # ----------------------------------------------

    print()

    print(
        "================================"
    )

    print(
        "🤖 AI JUDGE RESULTS"
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

    return results
