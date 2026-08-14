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

# Soft minimum score.
# We intentionally keep this lower than V6/V7.
MIN_SCORE = 45

# Target number of candidates for the next stage.
TARGET_APPROVED = 10

# Maximum candidates returned by this stage.
MAX_APPROVED = 15


# =========================================================
# ALLOWED CATEGORIES
# =========================================================

ALLOWED_CATEGORIES = {

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
    "mystery"

}


# =========================================================
# HARD REJECT CATEGORIES
# =========================================================

HARD_REJECT_CATEGORIES = {

    "gaming",
    "music",
    "anime",
    "fiction",
    "entertainment",
    "sports"

}


# =========================================================
# HARD REJECT KEYWORDS
# =========================================================

HARD_REJECT_PATTERNS = [

    # -----------------------------------------------------
    # GAMING
    # -----------------------------------------------------

    r"\bminecraft\b",
    r"\broblox\b",
    r"\bfortnite\b",
    r"\bgta\b",
    r"\bgta 5\b",
    r"\bgta 6\b",
    r"\bbrawl stars\b",
    r"\bvalorant\b",
    r"\bcall of duty\b",
    r"\bblack ops\b",
    r"\bwarhammer\b",
    r"\bplaystation\b",
    r"\bxbox\b",
    r"\bnintendo\b",
    r"\bgameplay\b",
    r"\bgame\b",
    r"\besports\b",
    r"\blck\b",
    r"\bcs2\b",
    r"\bcounter[- ]strike\b",
    r"\bfortnite\b",

    # -----------------------------------------------------
    # MUSIC
    # -----------------------------------------------------

    r"\bofficial music video\b",
    r"\bmusic video\b",
    r"\blyric video\b",
    r"\bdance practice\b",
    r"\bofficial video\b",
    r"\bmv\b",
    r"\bnew song\b",
    r"\bfull album\b",
    r"\bofficial audio\b",

    # -----------------------------------------------------
    # MOVIES / TRAILERS
    # -----------------------------------------------------

    r"\bofficial trailer\b",
    r"\bofficial teaser\b",
    r"\btrailer\b",
    r"\bteaser\b",
    r"\bfirst look\b",
    r"\bin theaters\b",

    # -----------------------------------------------------
    # LIVESTREAMS
    # -----------------------------------------------------

    r"\blive\b",
    r"\blivestream\b",
    r"\blive stream\b",

    # -----------------------------------------------------
    # DANCE
    # -----------------------------------------------------

    r"\bdance\b",
    r"\bchoreography\b",

]


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are an expert GLOBAL YouTube Shorts trend analyst.

Your job is NOT to decide whether a trend is already a
complete story.

Your job is to identify whether a trending subject can
reasonably become an ORIGINAL English informational,
educational, explanatory or factual YouTube Short.

==================================================
CORE PRINCIPLE
==================================================

TREND ≠ FINAL STORY.

A trend title may be:

- a keyword
- a company
- a product
- a technology
- a person
- a scientific subject
- a financial concept
- a place
- a current event
- a short phrase

The title does NOT need to contain the complete story.

For example:

"NASA"

can be a useful research topic.

"Google Pixel"

can be a useful technology topic.

"MSCI World"

can be a useful financial topic.

"OpenAI"

can be a useful AI topic.

"Tesla"

can be a useful business/technology topic.

Do NOT reject these simply because the title is short.

==================================================
WHAT WE WANT
==================================================

Prefer topics that can lead to:

HOOK
→ surprising fact
→ explanation
→ escalation
→ payoff

Strong categories:

technology
AI
science
space
psychology
business
economics
engineering
future technology
discoveries
history
world events
human behavior
unusual real-world events
factual mysteries
major companies
important products
important inventions

==================================================
WHAT WE DO NOT WANT
==================================================

Strongly reject:

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
fictional stories
fictional characters

celebrity gossip
fan content
reaction content
livestreams

sports matches
sports highlights
sports tournaments

memes with no factual story

vague entertainment

==================================================
IMPORTANT
==================================================

Do NOT reject a topic just because the exact current event
is unknown.

For example:

"Google Pixel"

Good reasoning:

"Major technology/product subject with strong global
interest. Exact current story angle requires research."

Bad reasoning:

"Rejected because the title does not contain a story."

==================================================
DO NOT INVENT FACTS
==================================================

You are NOT researching the actual event.

Do not invent:

- launch dates
- prices
- product features
- scandals
- statistics
- company announcements
- scientific discoveries
- historical events

You are only evaluating the topic's potential.

==================================================
STORY ANGLE
==================================================

For every potentially useful topic, create a POSSIBLE
CONTENT ANGLE.

The angle must be a research direction, NOT an invented
fact.

Bad:

"Google Pixel just launched satellite messaging."

Good:

"Why Google Pixel is suddenly attracting attention and
what technology developments may be behind it."

Bad:

"Tesla just lost 20% of its value."

Good:

"Why Tesla remains one of the most watched companies in
the world."

For:

"MSCI World"

Good:

"How MSCI World works and why millions of investors follow it."

==================================================
GLOBAL AUDIENCE
==================================================

The final Short will be in English.

Prefer subjects with broad international relevance.

High value:

AI
technology
science
space
money
business
psychology
human behavior
major discoveries
global companies
important technologies

Lower value:

local influencers
local entertainment
local fandom
obscure local events

==================================================
SCORING
==================================================

Give each score from 0 to 10.

global_interest:
How interesting is this globally?

viral_potential:
How much curiosity could this topic create?

english_audience:
How suitable is this for English-speaking viewers?

story_potential:
Can a strong factual story reasonably be built around it?

specificity:
How clearly does the trend identify a real subject?

IMPORTANT:

Short keywords can still receive:

specificity 4
specificity 5
specificity 6

Do NOT automatically give them 1 or 2.

factual_confidence:
How confident are you that this represents a real,
researchable subject?

originality:
Can we make original informational content instead of
copying the trending source?

==================================================
SCORING PHILOSOPHY
==================================================

We prefer to KEEP potentially useful research candidates.

Do not be overly conservative.

A topic can be approved even when:

specificity = 4

if:

global_interest is high
AND
story potential is reasonable
AND
factual confidence is reasonable.

This stage is a candidate generator.

The next stage will research the topic and reject it if
reliable facts cannot be found.

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

Set is_good_for_shorts to TRUE when:

1. The topic represents a real-world subject.

2. It can reasonably become informational content.

3. It has global or strong curiosity potential.

4. It is researchable.

5. It is NOT clearly gaming/music/fiction/trailer/etc.

Do not require a complete story.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return exactly one object per input topic.

Each object MUST contain:

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
    "research_needed": true,

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

        "research_needed": True,

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

def normalize_category(value):

    if not value:

        return "other"

    value = str(
        value
    ).lower().strip()

    aliases = {

        "tech": "technology",

        "technology/product":
            "technology",

        "artificial intelligence":
            "ai",

        "finance":
            "business",

        "economics":
            "business",

        "scientific":
            "science",

        "scientific discovery":
            "discovery",

        "space science":
            "space",

        "future technology":
            "future",

        "current events":
            "world"

    }

    value = aliases.get(
        value,
        value
    )

    if value not in ALLOWED_CATEGORIES:

        return "other"

    return value


# =========================================================
# TEXT HARD REJECT
# =========================================================

def hard_reject_topic(topic):

    if not topic:

        return True

    text = str(
        topic
    ).lower().strip()

    for pattern in HARD_REJECT_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            return True

    return False


# =========================================================
# SCORE
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

    # =====================================================
    # WEIGHTS
    # =====================================================

    score = (

        global_interest * 0.20

        +

        viral_potential * 0.18

        +

        english_audience * 0.10

        +

        story_potential * 0.20

        +

        specificity * 0.07

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

    result["category"] = normalize_category(
        result.get(
            "category",
            "other"
        )
    )

    # =====================================================
    # ANGLE
    # =====================================================

    angle = result.get(
        "angle",
        ""
    )

    if angle is None:

        angle = ""

    result["angle"] = str(
        angle
    ).strip()

    # =====================================================
    # RESEARCH FLAG
    # =====================================================

    result["research_needed"] = True

    # =====================================================
    # SCORE
    # =====================================================

    result["score"] = calculate_score(
        result
    )

    # =====================================================
    # FINAL DECISION
    # =====================================================

    approved = True

    # -----------------------------------------------------
    # HARD CATEGORY REJECT
    # -----------------------------------------------------

    if result["category"] in HARD_REJECT_CATEGORIES:

        approved = False

    # -----------------------------------------------------
    # HARD TEXT REJECT
    # -----------------------------------------------------

    if hard_reject_topic(
        original_topic
    ):

        approved = False

    # -----------------------------------------------------
    # VERY LOW FACTUAL CONFIDENCE
    # -----------------------------------------------------

    if (
        result["factual_confidence"]
        < 4
    ):

        approved = False

    # -----------------------------------------------------
    # VERY LOW STORY POTENTIAL
    # -----------------------------------------------------

    if (
        result["story_potential"]
        < 4
    ):

        approved = False

    # -----------------------------------------------------
    # VERY LOW GLOBAL INTEREST
    # -----------------------------------------------------

    if (
        result["global_interest"]
        < 4
    ):

        approved = False

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    if (
        result["score"]
        < MIN_SCORE
    ):

        approved = False

    # =====================================================
    # IMPORTANT:
    # SPECIFICITY IS NO LONGER A HARD REJECT
    # =====================================================

    # A topic such as:
    #
    # "NASA"
    # "Tesla"
    # "OpenAI"
    # "MSCI World"
    #
    # may have specificity 4-5 but still be valuable.

    # =====================================================
    # FINAL BOOLEAN
    # =====================================================

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
        in enumerate(
            topics
        )

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
    print(
        "================================"
    )

    print(
        "🤖 AI TREND JUDGE V8"
    )

    print(
        "================================"
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
    # SORT BY SCORE
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
    # PRINT ALL RESULTS
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

    approved_results = []

    for index, result in enumerate(

        results,

        start=1

    ):

        approved = result.get(

            "is_good_for_shorts",

            False

        )

        status = (

            "✅ APPROVED"

            if approved

            else

            "❌ REJECTED"

        )

        if approved:

            approved_results.append(
                result
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

    # =====================================================
    # LIMIT APPROVED RESULTS
    # =====================================================

    approved_results = approved_results[
        :MAX_APPROVED
    ]

    approved_count = len(
        approved_results
    )

    print(
        f"✅ AI approved: "
        f"{approved_count}/{len(results)}"
    )

    # =====================================================
    # APPROVED SUMMARY
    # =====================================================

    print()

    print(
        "================================"
    )

    print(
        "🔥 AI APPROVED TRENDS"
    )

    print(
        "================================"
    )

    print()

    if not approved_results:

        print(
            "❌ AI did not approve any topics"
        )

    else:

        for index, result in enumerate(

            approved_results,

            start=1

        ):

            print(

                f"#{index} "
                f"{result.get('topic', '')}"

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

                f"   Angle: "
                f"{result.get('angle', '')}"

            )

            print()

    # =====================================================
    # TARGET INFORMATION
    # =====================================================

    if approved_count < TARGET_APPROVED:

        print(
            f"⚠️ Approved topics: "
            f"{approved_count}"
        )

        print(
            f"🎯 Target: "
            f"{TARGET_APPROVED}"
        )

        print(
            "💡 Consider increasing the "
            "number of input trends."
        )

    else:

        print(

            f"🔥 Target reached: "
            f"{approved_count} candidates"

        )

    # =====================================================
    # RETURN ONLY APPROVED
    # =====================================================

    return approved_results
