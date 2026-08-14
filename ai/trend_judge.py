import os
import json
import re
import time

from google import genai
from google.genai import types


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

MAX_RETRIES = 2

RETRY_DELAY = 2


# =========================================================
# APPROVAL SETTINGS
# =========================================================
#
# V8 is intentionally more flexible than V6/V7.
#
# Short trend titles do NOT need to contain the complete story.
#
# Example:
#
# Google Pixel
# NASA
# Apple
# Tesla
# Home Alone
#
# can potentially become research-based Shorts.
#
# But clearly bad content is still hard blocked.
#


MIN_SCORE = 58

MIN_STORY_POTENTIAL = 5

MIN_FACTUAL_CONFIDENCE = 5

MIN_SPECIFICITY = 3


# =========================================================
# HARD BLOCK KEYWORDS
# =========================================================

HARD_BLOCK_PATTERNS = [

    # =====================================================
    # GAMING
    # =====================================================

    r"\bminecraft\b",
    r"\broblox\b",
    r"\bfortnite\b",
    r"\bgta\b",
    r"\bgta\s*5\b",
    r"\bgta\s*v\b",
    r"\bgrand theft auto\b",

    r"\bgameplay\b",
    r"\blets play\b",
    r"\blet's play\b",
    r"\bgaming\b",
    r"\bvideo game\b",
    r"\bgame video\b",

    r"\bserver\b.*\bgame\b",
    r"\bgame\b.*\bserver\b",

    r"\besports\b",

    r"\bbrawl stars\b",
    r"\bclash royale\b",
    r"\bcall of duty\b",
    r"\bvalorant\b",
    r"\bpubg\b",
    r"\bfree fire\b",
    r"\bleague of legends\b",
    r"\bdota\b",

    # =====================================================
    # MUSIC
    # =====================================================

    r"\bdance practice\b",
    r"\bmusic video\b",
    r"\bofficial music video\b",
    r"\blyric video\b",
    r"\blyrics\b",
    r"\bdance video\b",
    r"\bdance performance\b",

    r"\bmv\b",

    r"\bsong\b",
    r"\bsingle\b",
    r"\balbum\b",

    # Korean / Japanese common music markers

    r"댄스\s*프랙티스",
    r"댄스\s*비디오",
    r"뮤직\s*비디오",
    r"歌詞",
    r"ダンス",
    r"ミュージックビデオ",

    # =====================================================
    # FICTION / ANIME
    # =====================================================

    r"\banime\b",
    r"\bmanga\b",
    r"\bcartoon\b",

    r"\bfictional\b",
    r"\bfiction\b",

    r"\bspiderman\b",
    r"\bspider-man\b",
    r"\bbatman\b",
    r"\bsuperman\b",

    r"\bshinchan\b",
    r"\bdoraemon\b",

    # =====================================================
    # TRAILERS
    # =====================================================

    r"\btrailer\b",
    r"\bofficial trailer\b",
    r"\bteaser\b",

    # =====================================================
    # FAN CONTENT
    # =====================================================

    r"\bfan edit\b",
    r"\bfan made\b",
    r"\bfanmade\b",
    r"\breaction video\b",
    r"\blivestream\b",
    r"\blive stream\b",
    r"\bstreamer\b",

    # =====================================================
    # SPORTS MATCHES
    # =====================================================

    r"\bvs\b",
    r"\bversus\b",

    r"\bmatch\b",
    r"\bgame\s+\d+\b",

    r"\bfinal\b.*\bmatch\b",
    r"\bmatch\b.*\bfinal\b",

    r"\bhighlights\b",

    r"\bworld cup\b.*\bmatch\b",

    # =====================================================
    # ENTERTAINMENT
    # =====================================================

    r"\bprank\b",
    r"\bchallenge\b",
    r"\breaction\b",
    r"\bfunny\b",
    r"\bcompilation\b",

]


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = r"""
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate TRENDING TOPICS for an automated
English YouTube Shorts channel.

The channel creates ORIGINAL informational, educational,
explanatory or factual story-based Shorts.

The input is usually a SHORT TREND TITLE extracted from
Google Trends or YouTube Trends.

IMPORTANT:

The title is NOT necessarily the final story.

A short keyword can still be valuable.

Examples:

"Google Pixel"
"NASA"
"Tesla"
"Apple"
"Home Alone"
"SpaceX"
"ChatGPT"
"Bitcoin"

These can potentially lead to strong Shorts because the
next pipeline stage can research the current story.

Do NOT require the exact event to already appear in the title.

However:

DO NOT invent a specific event.

You are evaluating whether the topic has a realistic
research path.

=========================================================
CORE OBJECTIVE
=========================================================

Find topics that can become original English Shorts with:

HOOK
→ surprising fact
→ explanation
→ escalation
→ payoff

The goal is NOT to reproduce the trending video.

The goal is to use the trend as a starting point for an
original factual story.

=========================================================
GOOD TOPIC TYPES
=========================================================

Prefer:

technology
AI
science
space
discoveries
psychology
human behavior
engineering
inventions
business
economics
history
future technology
major world events
unusual real-world events
factual mysteries
strange places
important human stories
technology products
major companies

=========================================================
SHORT TITLES ARE ALLOWED
=========================================================

Do NOT automatically reject a short title.

For example:

"Google Pixel"

could receive:

global_interest: 8
viral_potential: 7
english_audience: 9
story_potential: 6
specificity: 4
factual_confidence: 8
originality: 8

This is potentially useful.

The exact story should be researched later.

=========================================================
VERY IMPORTANT
=========================================================

Do NOT invent a current event.

Bad:

"Google Pixel launched satellite messaging."

if that event is not contained in the topic.

Good:

"Major global technology product with multiple
researchable story angles. Exact current angle requires
research."

=========================================================
GLOBAL AUDIENCE
=========================================================

The final video is English.

Prefer globally recognizable subjects.

Strong:

AI
NASA
Apple
Google
Tesla
SpaceX
Bitcoin
Microsoft
Amazon
OpenAI
Samsung
Google Pixel
scientific discoveries
space
technology
psychology
business
economics

Lower value:

local influencers
local entertainment
local fandom
local-language celebrity content

=========================================================
HARD REJECTIONS
=========================================================

Reject:

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
lyrics
dance practice
dance videos

anime
fiction
fictional characters
cartoons

movie trailers
TV trailers
teasers

fan edits
reaction videos
livestreams
pranks
generic challenges

sports matches
match highlights
simple team-vs-team titles

celebrity gossip

generic entertainment

=========================================================
SPORTS EXCEPTION
=========================================================

Sports are normally rejected.

But a real-world factual sports story can be useful.

Examples:

"athlete breaks world record"

"historic Olympic controversy"

"football club financial scandal"

These can be accepted.

But:

"T1 vs DK"

"Real Madrid vs Barcelona"

must be rejected.

=========================================================
MUSIC EXCEPTION
=========================================================

Music content is normally rejected.

But a real-world industry story can be accepted.

Example:

"Spotify changes royalty system"

Potentially GOOD.

But:

"Spotify"

is only a company keyword and should have moderate
specificity.

=========================================================
MOVIE / ENTERTAINMENT EXCEPTION
=========================================================

Movie trailers and fictional content are rejected.

But real-world stories can be accepted.

Example:

"Hollywood actors strike"

Potentially GOOD.

"Avengers trailer"

BAD.

=========================================================
SCORING
=========================================================

Give each score from 0 to 10.

global_interest
How interesting is this to a global audience?

viral_potential
How likely is this to generate curiosity?

english_audience
How suitable is it for English-speaking viewers?

story_potential
Can this become a factual story?

specificity
How clearly does the topic identify a subject?

IMPORTANT:

A short title can still receive specificity 3-5.

Do NOT give specificity 0 merely because the title is short.

factual_confidence
How confident are you that the subject is real and
researchable without inventing facts?

originality
Can we create an original Short rather than copying
the source content?

=========================================================
CATEGORY
=========================================================

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

=========================================================
APPROVAL PHILOSOPHY
=========================================================

The following can be APPROVED if the scores justify it:

major companies
major products
major technology
AI
science
space
history
psychology
business
major world events

The following should normally be REJECTED:

gaming
music performance
anime
fiction
movie trailers
fan content
livestreams
generic entertainment
sports matches

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Return an array.

Exactly one object per input topic.

Preserve topic EXACTLY.

Do not rewrite the topic.

Do not add markdown.

Do not use code fences.

Each object:

{
    "topic": "original topic",
    "is_good_for_shorts": true,
    "category": "technology",

    "global_interest": 8,
    "viral_potential": 8,
    "english_audience": 9,
    "story_potential": 7,
    "specificity": 5,
    "factual_confidence": 8,
    "originality": 8,

    "reason": "Short explanation."
}

Remember:

Evaluate the TOPIC.

Do not invent the STORY.
"""


# =========================================================
# NORMALIZE TOPIC
# =========================================================

def normalize_topic(topic):

    if topic is None:
        return ""

    return str(topic).strip()


# =========================================================
# HARD BLOCK CHECK
# =========================================================

def hard_block_reason(topic):

    normalized = normalize_topic(
        topic
    ).lower()

    if not normalized:
        return "Empty topic."

    for pattern in HARD_BLOCK_PATTERNS:

        try:

            if re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE
            ):

                return (
                    "Rejected by hard content filter: "
                    "gaming, music, entertainment, "
                    "sports match, trailer, or fan content."
                )

        except re.error:

            continue

    return None


# =========================================================
# FAILED RESULT
# =========================================================

def failed_result(
    topic,
    reason="AI Judge failed"
):

    return {

        "topic":
            topic,

        "is_good_for_shorts":
            False,

        "category":
            "other",

        "global_interest":
            0,

        "viral_potential":
            0,

        "english_audience":
            0,

        "story_potential":
            0,

        "specificity":
            0,

        "factual_confidence":
            0,

        "originality":
            0,

        "score":
            0,

        "reason":
            reason

    }


# =========================================================
# HARD BLOCK RESULT
# =========================================================

def hard_block_result(
    topic,
    reason
):

    return {

        "topic":
            topic,

        "is_good_for_shorts":
            False,

        "category":
            "other",

        "global_interest":
            0,

        "viral_potential":
            0,

        "english_audience":
            0,

        "story_potential":
            0,

        "specificity":
            0,

        "factual_confidence":
            0,

        "originality":
            0,

        "score":
            0,

        "reason":
            reason

    }


# =========================================================
# NORMALIZE NUMBER
# =========================================================

def normalize_number(value):

    try:

        value = float(
            value
        )

    except Exception:

        return 0

    if value < 0:
        return 0

    if value > 10:
        return 10

    return value


# =========================================================
# SCORE
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

    score = (

        global_interest * 0.15

        +

        viral_potential * 0.15

        +

        english_audience * 0.10

        +

        story_potential * 0.20

        +

        specificity * 0.10

        +

        factual_confidence * 0.15

        +

        originality * 0.15

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
            "Invalid AI result."
        )

    # =====================================================
    # ALWAYS PRESERVE ORIGINAL TOPIC
    # =====================================================

    result["topic"] = original_topic

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
    # CATEGORY
    # =====================================================

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

    category = str(

        result.get(
            "category",
            "other"
        )

    ).strip().lower()

    if category not in allowed_categories:

        category = "other"

    result["category"] = category

    # =====================================================
    # SCORE
    # =====================================================

    result["score"] = calculate_score(
        result
    )

    # =====================================================
    # HARD BLOCK
    # =====================================================

    blocked = hard_block_reason(
        original_topic
    )

    if blocked:

        result["is_good_for_shorts"] = False

        result["reason"] = blocked

        return result

    # =====================================================
    # APPROVAL
    # =====================================================

    approved = True

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    if result["score"] < MIN_SCORE:

        approved = False

    # -----------------------------------------------------
    # STORY
    # -----------------------------------------------------

    if (
        result["story_potential"]
        < MIN_STORY_POTENTIAL
    ):

        approved = False

    # -----------------------------------------------------
    # FACTS
    # -----------------------------------------------------

    if (
        result["factual_confidence"]
        < MIN_FACTUAL_CONFIDENCE
    ):

        approved = False

    # -----------------------------------------------------
    # SPECIFICITY
    #
    # V8 allows short trend titles.
    #
    # -----------------------------------------------------

    if (
        result["specificity"]
        < MIN_SPECIFICITY
    ):

        approved = False

    # =====================================================
    # ADDITIONAL QUALITY RULE
    # =====================================================
    #
    # A topic with very low global relevance should not
    # pass merely because other values are high.
    #

    if (
        result["global_interest"] < 4
        and
        result["english_audience"] < 5
    ):

        approved = False

    # =====================================================
    # FINAL BOOLEAN
    # =====================================================

    result["is_good_for_shorts"] = approved

    return result


# =========================================================
# EXTRACT JSON ARRAY
# =========================================================

def extract_json_array(
    text
):

    if not text:

        return None

    text = text.strip()

    # -----------------------------------------------------
    # Remove code fences
    # -----------------------------------------------------

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # -----------------------------------------------------
    # Direct parse
    # -----------------------------------------------------

    try:

        data = json.loads(
            text
        )

        if isinstance(
            data,
            list
        ):

            return data

    except Exception:

        pass

    # -----------------------------------------------------
    # Find array boundaries
    # -----------------------------------------------------

    start = text.find(
        "["
    )

    end = text.rfind(
        "]"
    )

    if (
        start == -1
        or
        end == -1
        or
        end <= start
    ):

        return None

    candidate = text[
        start:end + 1
    ]

    # -----------------------------------------------------
    # Try direct candidate
    # -----------------------------------------------------

    try:

        data = json.loads(
            candidate
        )

        if isinstance(
            data,
            list
        ):

            return data

    except Exception:

        pass

    # -----------------------------------------------------
    # Common Gemini JSON repairs
    # -----------------------------------------------------

    repaired = candidate

    # Remove trailing commas
    repaired = re.sub(
        r",\s*([}\]])",
        r"\1",
        repaired
    )

    # Replace Python booleans
    repaired = re.sub(
        r"\bTrue\b",
        "true",
        repaired
    )

    repaired = re.sub(
        r"\bFalse\b",
        "false",
        repaired
    )

    repaired = re.sub(
        r"\bNone\b",
        "null",
        repaired
    )

    try:

        data = json.loads(
            repaired
        )

        if isinstance(
            data,
            list
        ):

            return data

    except Exception:

        pass

    return None


# =========================================================
# GEMINI REQUEST
# =========================================================

def request_gemini(
    prompt
):

    response = client.models.generate_content(

        model=MODEL_NAME,

        contents=prompt,

        config=types.GenerateContentConfig(

            temperature=0.15,

            response_mime_type="application/json"

        )

    )

    if not response:

        return ""

    text = getattr(
        response,
        "text",
        None
    )

    if not text:

        return ""

    return text.strip()


# =========================================================
# PREPARE TOPICS
# =========================================================

def prepare_topics(
    topics
):

    cleaned = []

    seen = set()

    for topic in topics:

        topic = normalize_topic(
            topic
        )

        if not topic:

            continue

        key = topic.lower()

        if key in seen:

            continue

        seen.add(
            key
        )

        cleaned.append(
            topic
        )

    return cleaned


# =========================================================
# BUILD PROMPT
# =========================================================

def build_prompt(
    topics
):

    topics_text = "\n".join(

        f"{index + 1}. {topic}"

        for index, topic
        in enumerate(
            topics
        )

    )

    prompt = f"""
{SYSTEM_PROMPT}

=========================================================
CURRENT BATCH
=========================================================

There are EXACTLY {len(topics)} input topics.

Analyze EVERY topic.

Return EXACTLY {len(topics)} objects.

The order MUST remain identical.

Do NOT remove topics.

Do NOT merge topics.

Do NOT rewrite topics.

Preserve every topic exactly.

=========================================================
TOPICS
=========================================================

{topics_text}

=========================================================
FINAL REMINDER
=========================================================

Return ONLY a valid JSON array.

No markdown.

No explanation outside JSON.

Exactly one object per topic.
"""

    return prompt


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

    # =====================================================
    # HARD BLOCK BEFORE GEMINI
    # =====================================================

    hard_blocked = {}

    ai_topics = []

    for topic in topics:

        reason = hard_block_reason(
            topic
        )

        if reason:

            hard_blocked[
                topic
            ] = hard_block_result(
                topic,
                reason
            )

        else:

            ai_topics.append(
                topic
            )

    print(
        f"🚫 Hard-block candidates: "
        f"{len(hard_blocked)}"
    )

    results_map = {}

    # =====================================================
    # HARD BLOCK ONLY BATCH
    # =====================================================

    if not ai_topics:

        return [

            hard_blocked.get(
                topic,
                failed_result(
                    topic
                )
            )

            for topic in topics

        ]

    # =====================================================
    # GEMINI RETRIES
    # =====================================================

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            prompt = build_prompt(
                ai_topics
            )

            raw_text = request_gemini(
                prompt
            )

            if not raw_text:

                raise ValueError(
                    "Empty Gemini response"
                )

            data = extract_json_array(
                raw_text
            )

            if data is None:

                print(
                    "⚠️ JSON decode error:"
                )

                print(
                    "Gemini raw response:"
                )

                print(
                    raw_text
                )

                raise ValueError(
                    "Could not parse Gemini JSON"
                )

            # =================================================
            # MAP RESULTS
            # =================================================

            for index, topic in enumerate(
                ai_topics
            ):

                if index >= len(data):

                    continue

                result = data[index]

                if not isinstance(
                    result,
                    dict
                ):

                    continue

                validated = validate_result(
                    result,
                    topic
                )

                results_map[
                    topic
                ] = validated

            # =================================================
            # SUCCESS
            # =================================================

            missing = [

                topic

                for topic in ai_topics

                if topic
                not in results_map

            ]

            if missing:

                print(
                    f"⚠️ Gemini returned "
                    f"{len(missing)} missing results"
                )

                if attempt < MAX_RETRIES:

                    time.sleep(
                        RETRY_DELAY
                    )

                    continue

                for topic in missing:

                    results_map[
                        topic
                    ] = failed_result(
                        topic,
                        "Missing AI result"
                    )

            break

        except Exception as error:

            print()

            print(
                f"⚠️ Gemini V8 attempt "
                f"{attempt}/{MAX_RETRIES} failed:"
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

            else:

                print(
                    "❌ Gemini batch permanently failed"
                )

                for topic in ai_topics:

                    if topic not in results_map:

                        results_map[
                            topic
                        ] = failed_result(
                            topic,
                            "Gemini request failed"
                        )

    # =====================================================
    # FINAL ORDER
    # =====================================================

    results = []

    for topic in topics:

        if topic in hard_blocked:

            results.append(
                hard_blocked[
                    topic
                ]
            )

        elif topic in results_map:

            results.append(
                results_map[
                    topic
                ]
            )

        else:

            results.append(
                failed_result(
                    topic,
                    "No result generated"
                )
            )

    return results


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

    topics = prepare_topics(
        topics
    )

    if not topics:

        print(
            "❌ No topics received"
        )

        return []

    print(
        f"📊 Topics for AI Judge: "
        f"{len(topics)}"
    )

    print(
        f"🎯 Target approved topics: "
        f"{TARGET_APPROVED}"
    )

    print()

    # =====================================================
    # SPLIT BATCHES
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

    results = []

    # =====================================================
    # PROCESS
    # =====================================================

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
                3
            )

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
    # DISPLAY
    # =====================================================

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

    # =====================================================
    # APPROVED
    # =====================================================

    approved = [

        result

        for result in results

        if result.get(
            "is_good_for_shorts",
            False
        )

    ]

    # =====================================================
    # TOP TARGET
    # =====================================================

    approved = approved[
        :TARGET_APPROVED
    ]

    # =====================================================
    # SUMMARY
    # =====================================================

    print(
        f"✅ AI approved: "
        f"{len(approved)}/{len(results)}"
    )

    print(
        f"🎯 Target: "
        f"{TARGET_APPROVED}"
    )

    if len(approved) < TARGET_APPROVED:

        print(
            f"⚠️ Only "
            f"{len(approved)} topics approved."
        )

        print(
            "💡 Consider increasing the number "
            "of input trends."
        )

    else:

        print(
            f"🔥 Target reached: "
            f"{len(approved)} topics"
        )

    return approved
