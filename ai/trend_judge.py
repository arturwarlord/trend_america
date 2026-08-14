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

# Минимальный score
MIN_SCORE = 60

# Минимальные требования
MIN_SPECIFICITY = 5
MIN_FACTUAL_CONFIDENCE = 5
MIN_STORY_POTENTIAL = 5


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate whether a TRENDING TOPIC can be
turned into an ORIGINAL English YouTube Short for a global audience.

IMPORTANT:

The input is usually a SHORT TREND TITLE extracted from
Google Trends or YouTube Trends.

Therefore, do NOT require the entire story to be written
inside the title.

You must evaluate the topic based on what the title
reasonably indicates.

However, you MUST NOT invent a specific fact that is not
reasonably suggested by the topic.

The next stage of the pipeline may research the topic
before writing the final Short.

==================================================
CORE OBJECTIVE
==================================================

We are NOT trying to reproduce the original trending video.

We are trying to identify a trend that can lead to an
original informational, educational, explanatory or
story-based English Short.

A good trend can be:

- a current technology development
- an AI development
- a scientific discovery
- a space event
- an unusual real-world event
- a business development
- an important historical story
- a psychological phenomenon
- an unusual invention
- a strange place
- a factual mystery
- a major world event
- a surprising human behavior
- a technology/product development with a clear angle

==================================================
VERY IMPORTANT:
TREND TITLE VS FINAL STORY
==================================================

Do NOT reject a topic ONLY because the title is short.

Examples:

"Google Pixel"

This is potentially useful because it is a major
technology/product trend.

But it should receive LOWER specificity because
the exact story is not known yet.

"Google Pixel satellite messaging"

This is stronger because the angle is clearer.

"Ticketmaster"

This is potentially useful as a business trend,
but the exact story is unknown.

Therefore:

- global_interest can be high
- viral_potential can be high
- story_potential can be moderate
- specificity can be moderate or low
- factual_confidence can be moderate

Do NOT invent a pricing change or other event.

==================================================
GOOD TOPIC TYPES
==================================================

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
unusual real-world events
major world events
factual mysteries
strange places

==================================================
BAD TOPIC TYPES
==================================================

Strongly reject:

- gaming
- video games
- gameplay
- Minecraft
- Roblox
- Fortnite
- GTA
- Brawl Stars
- esports
- gaming tournaments

- music videos
- songs
- albums
- lyric videos
- dance practice
- dance videos
- music battles

- movie trailers
- TV trailers
- anime
- fictional characters
- fictional stories

- celebrity gossip
- fan content
- reaction videos
- livestreams

- sports matches
- sports highlights
- sports tournaments

- memes with no factual story

==================================================
SPORTS EXCEPTION
==================================================

A random athlete name is NOT a good topic.

However, a major REAL-WORLD sports story can sometimes
be useful if the title clearly indicates a factual event
such as:

"athlete breaks world record"

"historic Olympic controversy"

"football club financial scandal"

Do not approve simple match titles such as:

"T1 vs DK"

"Real Madrid vs Barcelona"

==================================================
MUSIC EXCEPTION
==================================================

Music-related topics should normally be rejected.

Do not approve:

"Artist - Song"

"Official Music Video"

"Dance Practice"

"Lyric Video"

However, a genuine real-world story ABOUT the music industry
could potentially be useful if the title clearly indicates
the story.

Example:

"Spotify changes royalty system"

Potentially GOOD.

But:

"Spotify"

is only a company keyword and should have lower specificity.

==================================================
MOVIE / ENTERTAINMENT EXCEPTION
==================================================

Movie trailers, anime and fictional characters should be rejected.

However, a real-world industry story can be useful.

Example:

"Hollywood actors strike"

Potentially GOOD.

But:

"Avengers Doomday trailer"

BAD.

==================================================
GLOBAL AUDIENCE
==================================================

The final Short will be in English.

Prefer topics that can interest people across multiple countries.

High-value signals:

- technology
- AI
- science
- space
- money
- business
- human psychology
- surprising discoveries
- major global events

Lower-value signals:

- local influencers
- local TV personalities
- local fandom
- local-language entertainment
- obscure local events

==================================================
STORY POTENTIAL
==================================================

Ask:

Can this trend lead to a Short with:

HOOK
→ surprising information
→ explanation
→ escalation
→ payoff

Good story potential means that there is a plausible
question behind the trend:

Why is this trending?

What happened?

Why does it matter?

How does it work?

What changed?

What surprising fact is connected to it?

==================================================
IMPORTANT:
DO NOT INVENT FACTS
==================================================

You are evaluating the TREND, not writing the final story.

You may recognize that a topic has strong potential
without inventing the exact event.

For example:

"Google Pixel"

Do NOT say:

"Google Pixel launched satellite messaging."

unless that is actually present in the topic.

Instead:

"Major technology/product trend with strong global
interest, but the exact current story angle requires research."

==================================================
SCORING
==================================================

Give each value from 0 to 10.

global_interest
How interesting is this to a global audience?

viral_potential
How likely is the topic to attract curiosity and views?

english_audience
How suitable is it for an English-speaking global audience?

story_potential
Can this trend reasonably lead to an interesting factual story?

specificity
How clearly does the trend indicate a usable topic?

factual_confidence
How confident are you that the topic represents a real-world
subject that can be researched without inventing facts?

originality
Can we create an original informational Short rather than
copying the source content?

==================================================
SCORING GUIDELINES
==================================================

Do NOT make every score low just because the title is short.

A short trend can still have:

global_interest: 8
viral_potential: 8
english_audience: 9
story_potential: 7
specificity: 5
factual_confidence: 7
originality: 8

That is a potentially useful trend.

Generic entertainment should still score low.

Example:

"google pixel"

Possible:

global_interest: 8
viral_potential: 7
english_audience: 9
story_potential: 6
specificity: 4
factual_confidence: 8
originality: 7

It may still be rejected by the hard specificity rule,
but it should NOT receive score 3/100.

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
DECISION
==================================================

Set is_good_for_shorts to TRUE when the topic has a realistic
path toward an original informational Short.

Do NOT require the exact final story to already be visible
in the title.

But reject clearly unsuitable content:

gaming
music
movie trailers
anime
fiction
sports matches
livestreams
random names
vague entertainment
fan content

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return an array.

The array MUST contain exactly one object per input topic.

Do not use markdown.

Do not use ```.

Do not add explanations outside JSON.

Each object must contain:

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

Remember:

The topic itself must NOT be rewritten.

Preserve the original topic exactly.
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

    # Extract JSON array if Gemini added text
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

    # Specificity
    if (
        result["specificity"]
        < MIN_SPECIFICITY
    ):

        approved = False

    # Facts
    if (
        result["factual_confidence"]
        < MIN_FACTUAL_CONFIDENCE
    ):

        approved = False

    # Story
    if (
        result["story_potential"]
        < MIN_STORY_POTENTIAL
    ):

        approved = False

    # Final score
    if (
        result["score"]
        < MIN_SCORE
    ):

        approved = False

    # =====================================================
    # DO NOT TRUST GEMINI BOOLEAN
    # =====================================================
    #
    # The final decision is controlled by our program.
    #

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
# JUDGE MULTIPLE TOPICS
# =========================================================

def judge_topics(topics):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE V6")
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
            f"   Reason: "
            f"{result.get('reason', '')}"
        )

        print()

    print(
        f"✅ AI approved: "
        f"{approved_count}/{len(results)}"
    )

    return results
