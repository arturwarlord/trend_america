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

# Общий минимальный score
MIN_SCORE = 55

# Минимальные требования
MIN_SPECIFICITY = 4
MIN_FACTUAL_CONFIDENCE = 5
MIN_STORY_POTENTIAL = 5

# Сколько тем хотим получить дальше
TARGET_APPROVED = 8


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate trending topics from Google Trends
and YouTube Trends and determine whether they can become
ORIGINAL English informational YouTube Shorts.

==================================================
CORE OBJECTIVE
==================================================

We are NOT reproducing the original trending video.

We are using the trend as a signal and creating a NEW
informational, educational, explanatory or story-based Short.

The trend itself does NOT need to contain the complete story.

A short keyword can be valuable if it represents a major
real-world subject.

Examples:

"MSCI World"
"Google Pixel"
"OpenAI"
"NASA"
"Tesla"
"Bitcoin"
"quantum computing"

These should NOT automatically be rejected because they
are short.

Instead, evaluate whether there is a realistic path to
researching a current, factual and interesting story.

==================================================
IMPORTANT:
TREND TITLE ≠ FINAL STORY
==================================================

The input is often only a keyword or short trend title.

Do NOT demand that the exact event is visible in the title.

For example:

"Google Pixel"

Potentially useful.

Do NOT invent:

"Google Pixel launched satellite messaging."

Instead recognize:

"Major technology/product trend. Exact current story angle
requires research."

Likewise:

"MSCI World"

Potentially useful because it is a major global financial
index.

==================================================
GOOD TOPIC TYPES
==================================================

Strongly prefer:

technology
AI
science
space
business
economics
psychology
human behavior
engineering
inventions
future technology
discoveries
history
world events
unusual real-world events
factual mysteries
strange places
major companies
important products
important technologies

==================================================
BAD TOPIC TYPES
==================================================

Reject:

gaming
video games
gameplay
Minecraft
Roblox
Fortnite
GTA
Brawl Stars
esports
gaming tournaments

music videos
songs
albums
lyrics
dance practice
dance videos
music battles

movie trailers
TV trailers
anime
fictional characters
fictional stories

celebrity gossip
fan content
reaction videos
livestreams

sports matches
sports highlights
sports tournaments

memes with no factual story

random influencer content

vague entertainment titles

==================================================
SPORTS
==================================================

Random athlete names are NOT enough.

Match titles are NOT enough.

However, a major real-world factual sports story can be
useful if the trend clearly indicates a significant event.

Example:

"athlete breaks world record"

Potentially GOOD.

Example:

"T1 vs DK"

BAD.

==================================================
MUSIC
==================================================

Music content should normally be rejected.

Examples:

"Artist - Song"
"Official Music Video"
"Dance Practice"

BAD.

However, real-world music industry stories can be useful.

Example:

"Spotify royalty changes"

Potentially GOOD.

==================================================
MOVIES / ENTERTAINMENT
==================================================

Movie trailers, fictional characters and entertainment
content should normally be rejected.

But real-world industry stories may be useful.

Example:

"Hollywood actors strike"

Potentially GOOD.

==================================================
GLOBAL AUDIENCE
==================================================

The final video will be in English.

Prefer subjects understandable to a global audience.

High-value:

AI
technology
science
space
money
business
psychology
human behavior
major discoveries
major companies
important global events

Lower-value:

local influencers
local celebrities
local fandom
local entertainment
obscure local events

==================================================
STORY POTENTIAL
==================================================

Ask:

Can we reasonably turn this trend into:

HOOK
→ surprising fact
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

What does this mean for ordinary people?

==================================================
RESEARCHABILITY
==================================================

A topic does NOT need to contain the exact story.

If the topic is a major real-world subject that can be
researched using reliable sources, give it reasonable
factual confidence.

Examples:

"NASA"
"Tesla"
"Google Pixel"
"Bitcoin"
"MSCI World"
"OpenAI"

These are researchable subjects.

Do NOT invent specific events.

==================================================
SCORING
==================================================

Give every score from 0 to 10.

global_interest:
How interesting is this globally?

viral_potential:
How much curiosity can this generate?

english_audience:
How suitable is it for an English audience?

story_potential:
Can we build an interesting factual story?

specificity:
How clearly does the trend identify a subject?

IMPORTANT:

Short titles may receive specificity 4-6.

Do NOT automatically give short keywords specificity 1-3.

factual_confidence:
How confident are you that this is a real-world
researchable subject?

originality:
Can we create original informational content?

==================================================
SCORING EXAMPLES
==================================================

"Google Pixel"

Possible:

global_interest: 8
viral_potential: 7
english_audience: 9
story_potential: 7
specificity: 5
factual_confidence: 9
originality: 8

This is potentially GOOD.

"MSCI World"

Possible:

global_interest: 8
viral_potential: 7
english_audience: 9
story_potential: 7
specificity: 5
factual_confidence: 9
originality: 8

Potentially GOOD.

"OpenAI"

Potentially GOOD.

"NASA"

Potentially GOOD.

"Bitcoin"

Potentially GOOD.

"SKIBIDI TOILET"

BAD.

"Fortnite"

BAD.

"Artist - Song"

BAD.

"Avengers trailer"

BAD.

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
ANGLE
==================================================

For every potentially useful topic, create a short
POSSIBLE STORY ANGLE.

The angle must NOT invent a specific fact.

Bad:

"Google Pixel just launched satellite messaging."

This invents a fact.

Good:

"Why Google Pixel is suddenly trending and what new
technology may be behind the attention."

For a generic subject:

"MSCI World"

Good:

"Why millions of investors use MSCI World and how the
index actually works."

The angle is a CONTENT DIRECTION, not a factual claim.

==================================================
DECISION
==================================================

Set is_good_for_shorts to TRUE when:

1. The subject is suitable for original informational
   content.

2. It is globally relevant OR has strong curiosity.

3. It is realistically researchable.

4. It is not prohibited entertainment/gaming/music/etc.

Do NOT reject simply because the title is short.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return exactly one object per input topic.

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

    "angle": "Possible factual story direction.",
    "reason": "Short explanation."
}

IMPORTANT:

Preserve the original topic EXACTLY.

Do not rewrite the topic.

The angle may be generated.

Do not invent specific current events.
"""


# =========================================================
# CLEAN JSON
# =========================================================

def clean_json(text):

    if not text:
        return ""

    text = text.strip()

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

        "angle": "",
        "score": 0,

        "reason": reason
    }


# =========================================================
# NORMALIZE
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
# SCORE
# =========================================================

def calculate_score(result):

    global_interest = normalize_number(
        result.get("global_interest", 0)
    )

    viral_potential = normalize_number(
        result.get("viral_potential", 0)
    )

    english_audience = normalize_number(
        result.get("english_audience", 0)
    )

    story_potential = normalize_number(
        result.get("story_potential", 0)
    )

    specificity = normalize_number(
        result.get("specificity", 0)
    )

    factual_confidence = normalize_number(
        result.get("factual_confidence", 0)
    )

    originality = normalize_number(
        result.get("originality", 0)
    )

    score = (

        global_interest * 0.18

        +

        viral_potential * 0.17

        +

        english_audience * 0.10

        +

        story_potential * 0.20

        +

        specificity * 0.10

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
# HARD REJECT CATEGORIES
# =========================================================

HARD_REJECT_CATEGORIES = {

    "gaming",
    "music",
    "sports",
    "entertainment",
    "anime",
    "fiction"

}


# =========================================================
# VALIDATE
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

    # Always preserve original topic
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
            result.get(field, 0)
        )

    category = str(
        result.get(
            "category",
            "other"
        )
    ).lower().strip()

    result["category"] = category

    # =====================================================
    # SCORE
    # =====================================================

    result["score"] = calculate_score(
        result
    )

    # =====================================================
    # APPROVAL
    # =====================================================

    approved = True

    # Hard category rejection
    if category in HARD_REJECT_CATEGORIES:
        approved = False

    # Minimum factual confidence
    if (
        result["factual_confidence"]
        < MIN_FACTUAL_CONFIDENCE
    ):
        approved = False

    # Minimum story potential
    if (
        result["story_potential"]
        < MIN_STORY_POTENTIAL
    ):
        approved = False

    # Minimum specificity
    if (
        result["specificity"]
        < MIN_SPECIFICITY
    ):
        approved = False

    # Minimum score
    if (
        result["score"]
        < MIN_SCORE
    ):
        approved = False

    result["is_good_for_shorts"] = approved

    return result


# =========================================================
# GEMINI BATCH
# =========================================================

def judge_batch(
    topics,
    batch_number,
    total_batches
):

    print(
        f"🚀 Gemini batch request "
        f"{batch_number}/{total_batches}"
    )

    topics_text = "\n".join(

        f"{index + 1}. {topic}"

        for index, topic
        in enumerate(topics)

    )

    prompt = f"""
{SYSTEM_PROMPT}

Analyze ALL topics below.

TOPICS:

{topics_text}

IMPORTANT:

There are exactly {len(topics)} topics.

Return exactly {len(topics)} JSON objects.

The order MUST be identical to the input order.

Do not remove any topic.

Do not merge topics.

Do not rewrite topics.

Preserve every original topic exactly.
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

        data = json.loads(
            text
        )

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

    except Exception as error:

        print()
        print(
            "⚠️ Gemini batch error:"
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
# JUDGE TOPICS
# =========================================================

def judge_topics(topics):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE V7")
    print("================================")

    if not topics:

        print(
            "❌ No topics received"
        )

        return []

    print(
        f"📊 Topics for AI Judge: "
        f"{len(topics)}"
    )

    print()

    results = []

    # =====================================================
    # BATCHES
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
    # PRINT
    # =====================================================

    print()
    print("================================")
    print("🤖 AI JUDGE RESULTS")
    print("================================")
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
            f"   Angle: "
            f"{result.get('angle', '')}"
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

    # =====================================================
    # TARGET WARNING
    # =====================================================

    if approved_count < TARGET_APPROVED:

        print()
        print(
            f"⚠️ Only {approved_count} topics approved."
        )

        print(
            f"🎯 Target: {TARGET_APPROVED}"
        )

        print(
            "💡 Consider expanding TOP 30 "
            "to TOP 50 if necessary."
        )

    else:

        print()
        print(
            f"🔥 Enough topics for next stage: "
            f"{approved_count}"
        )

    return results
