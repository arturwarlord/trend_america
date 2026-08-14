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

# Минимальный итоговый score для допуска
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

We are building ORIGINAL English YouTube Shorts for a global audience.

Your task is to evaluate trending topics.

IMPORTANT:

You must judge ONLY what is actually supported by the topic text.

DO NOT invent:
- events
- facts
- people
- dates
- locations
- statistics
- announcements
- product launches
- news

If a topic is vague, generic, or only a keyword,
give it LOW specificity and LOW story potential.

==================================================
GOOD TOPICS
==================================================

Prefer:

- artificial intelligence
- technology
- science
- space
- discoveries
- psychology
- human behavior
- engineering
- inventions
- business stories
- economic stories
- historical events
- unusual real-world events
- major world events
- strange places
- factual mysteries
- future technology

==================================================
BAD TOPICS
==================================================

Reject:

- gaming
- video games
- esports
- gameplay
- gaming tournaments
- music videos
- songs
- albums
- dance videos
- movie trailers
- TV shows
- anime
- celebrity gossip
- sports matches
- sports highlights
- livestreams
- reaction videos
- fan content
- fictional characters
- memes without a factual story
- generic product searches
- generic company searches
- random people's names
- vague search queries

==================================================
IMPORTANT DISTINCTION
==================================================

A popular topic is NOT automatically a good Shorts topic.

For example:

"google pixel"

BAD.

It is only a generic product/search term.

"Google Pixel introduces satellite messaging"

GOOD.

It describes a specific technological development.

Another example:

"ticketmaster"

BAD.

It is only a company name.

"Ticketmaster changes its ticket pricing system"

Potentially GOOD because it describes a specific business development.

But if the supplied topic is only:

"ticketmaster"

DO NOT invent the pricing story.

==================================================
GLOBAL AUDIENCE
==================================================

Prefer topics understandable to an English-speaking global audience.

Avoid topics requiring knowledge of:

- a specific local influencer
- a local TV show
- a local game
- a local music artist
- local fandom
- local language
- local sports culture

==================================================
ORIGINAL SHORT POTENTIAL
==================================================

A good topic should naturally allow:

HOOK
→ surprising fact
→ explanation
→ escalation
→ payoff

The viewer should naturally ask:

Why?
How?
What happened?
What does this mean?

==================================================
SCORING
==================================================

Give every category a number from 0 to 10.

global_interest
viral_potential
english_audience
story_potential
specificity
factual_confidence
originality

Do NOT calculate "score".

The program will calculate score itself.

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

Set is_good_for_shorts to TRUE only if:

- topic is suitable for global English audience
- topic contains a potentially factual story
- topic is sufficiently specific
- topic can become an original Short
- topic is not gaming/music/movie/celebrity/sports/etc.
- factual confidence is reasonably high

If topic is only a generic keyword:
FALSE.

If topic is interesting but vague:
FALSE.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return an array.

Do not use markdown.

Do not use ```.

Example:

[
  {
    "topic": "example",
    "is_good_for_shorts": true,
    "category": "technology",
    "global_interest": 8,
    "viral_potential": 8,
    "english_audience": 9,
    "story_potential": 8,
    "specificity": 9,
    "factual_confidence": 8,
    "originality": 8,
    "reason": "Specific technology development with clear story potential."
  }
]
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

    # Sometimes Gemini adds text before JSON.
    # Try to extract array.
    start = text.find("[")

    end = text.rfind("]")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text.strip()


# =========================================================
# FAILED RESULT
# =========================================================

def failed_result(topic, reason="AI Judge failed"):

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

    # =====================================================
    # WEIGHTED SCORE
    #
    # Everything is 0-10.
    #
    # Weighted average is therefore 0-10.
    #
    # Multiply by 10 => 0-100.
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

    return round(score, 2)


# =========================================================
# VALIDATE RESULT
# =========================================================

def validate_result(result, original_topic):

    if not isinstance(result, dict):

        return failed_result(
            original_topic,
            "Invalid AI result"
        )

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

    # =====================================================
    # CALCULATE SCORE OURSELVES
    # =====================================================

    result["score"] = calculate_score(
        result
    )

    # =====================================================
    # HARD RULES
    # =====================================================

    approved = True

    if result["specificity"] < MIN_SPECIFICITY:
        approved = False

    if result["factual_confidence"] < MIN_FACTUAL_CONFIDENCE:
        approved = False

    if result["story_potential"] < MIN_STORY_POTENTIAL:
        approved = False

    if result["score"] < MIN_SCORE:
        approved = False

    if not result.get(
        "is_good_for_shorts",
        False
    ):
        approved = False

    result["is_good_for_shorts"] = approved

    return result


# =========================================================
# GEMINI BATCH
# =========================================================

def judge_batch(topics, batch_number, total_batches):

    print(
        f"🚀 Gemini batch request "
        f"{batch_number}/{total_batches}"
    )

    topics_text = "\n".join(

        f"{index + 1}. {topic}"

        for index, topic in enumerate(topics)

    )

    prompt = f"""
{SYSTEM_PROMPT}

Analyze ALL topics below.

TOPICS:

{topics_text}

Return exactly one JSON object for every topic.

The returned array MUST contain exactly {len(topics)} objects.

Preserve the original topic text exactly.
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

        for index, topic in enumerate(topics):

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

        error_text = str(error)

        print()
        print(
            f"⚠️ Gemini batch error:"
        )
        print(
            error_text
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
    print("🤖 AI TREND JUDGE V5")
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

        topics[index:index + BATCH_SIZE]

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

        # =================================================
        # SMALL DELAY BETWEEN REQUESTS
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
            else "❌ REJECTED"
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
