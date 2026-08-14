import os
import json
import re
import time

from google import genai


# ==========================================
# GEMINI CLIENT
# ==========================================

client = genai.Client(
    api_key=os.getenv("GEMINI_KEY")
)

MODEL_NAME = "gemini-flash-lite-latest"


# ==========================================
# SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate trending topics for ORIGINAL
English YouTube Shorts for a GLOBAL audience.

We are NOT making videos about the original content.

We are looking for an underlying REAL story, fact,
event, discovery, technology, history, science,
business story or unusual real-world phenomenon.

==========================================
APPROVE
==========================================

Good categories:

- artificial intelligence
- technology
- science
- space
- discoveries
- psychology
- human behavior
- surprising facts
- future technology
- inventions
- engineering
- business stories
- economic stories
- historical events
- unusual real-world stories
- major world events
- strange places
- mysteries with factual basis

==========================================
REJECT
==========================================

Reject:

- video games
- gaming
- esports
- gaming tournaments
- gameplay
- Minecraft
- Roblox
- GTA
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
- random people's names
- generic product searches
- local events
- fan content
- reaction videos
- livestreams
- fictional characters
- memes without a real-world story

==========================================
IMPORTANT
==========================================

Do NOT invent facts.

Judge ONLY what the topic itself reasonably supports.

A vague keyword must be rejected.

Examples:

"google pixel"
BAD

"Google Pixel introduces satellite messaging"
GOOD

"ticketmaster"
BAD

"Ticketmaster changes its pricing system"
GOOD

"avgo stock"
BAD

"Broadcom's AI chip business drives unexpected growth"
GOOD

==========================================
GLOBAL AUDIENCE
==========================================

The topic should work for an English-speaking global audience.

Prefer topics that do not require:

- local political knowledge
- local language
- knowledge of influencers
- knowledge of a specific game
- knowledge of a TV show
- knowledge of a music artist

==========================================
SHORTS STORY
==========================================

A good topic should naturally support:

HOOK
→ surprising fact
→ explanation
→ escalation
→ payoff

The viewer should naturally ask:

"What happened?"
"Why?"
"How?"
"What does this mean?"

==========================================
SCORING
==========================================

global_interest: 0-10
viral_potential: 0-10
english_audience: 0-10
story_potential: 0-10
specificity: 0-10
factual_confidence: 0-10
originality: 0-10

Calculate score from these factors.

Approximate weighting:

global_interest       15%
viral_potential       15%
english_audience      10%
story_potential       20%
specificity           15%
factual_confidence    15%
originality           10%

==========================================
STRICT APPROVAL
==========================================

is_good_for_shorts = true ONLY when:

- clear real-world story or fact exists
- topic is specific enough
- global English audience can understand it
- original educational Short is possible
- factual confidence is reasonably high
- topic is not in the rejected categories

If the topic is vague, reject it.

If the topic is only a keyword, reject it.

If the topic is interesting but lacks factual specificity,
reject it.

==========================================
CATEGORY
==========================================

Use one:

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

==========================================
OUTPUT
==========================================

Return ONLY valid JSON.

Return an ARRAY.

No markdown.

No ```.

No explanation outside JSON.

Each object MUST contain:

{
    "topic": "...",
    "is_good_for_shorts": true,
    "category": "technology",

    "global_interest": 0,
    "viral_potential": 0,
    "english_audience": 0,
    "story_potential": 0,
    "specificity": 0,
    "factual_confidence": 0,
    "originality": 0,

    "score": 0,

    "reason": "short explanation"
}
"""


# ==========================================
# JSON CLEANER
# ==========================================

def clean_json(text):

    if not text:
        return ""

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

    return text.strip()


# ==========================================
# FAILED RESULT
# ==========================================

def failed_result(topic):

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

        "reason": "AI Judge failed"
    }


# ==========================================
# VALIDATE RESULT
# ==========================================

def validate_result(result, topic):

    if not isinstance(result, dict):

        return failed_result(topic)

    result["topic"] = topic

    numeric_fields = [

        "global_interest",
        "viral_potential",
        "english_audience",
        "story_potential",
        "specificity",
        "factual_confidence",
        "originality",
        "score"

    ]

    for field in numeric_fields:

        try:

            value = float(
                result.get(field, 0)
            )

            value = max(
                0,
                min(value, 100 if field == "score" else 10)
            )

            result[field] = value

        except Exception:

            result[field] = 0

    # ======================================
    # HARD RULES
    # ======================================

    if result["specificity"] < 5:

        result["is_good_for_shorts"] = False

    if result["factual_confidence"] < 5:

        result["is_good_for_shorts"] = False

    if result["story_potential"] < 5:

        result["is_good_for_shorts"] = False

    if result["score"] < 60:

        result["is_good_for_shorts"] = False

    return result


# ==========================================
# JUDGE MULTIPLE TOPICS
# ==========================================

def judge_topics(topics):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE V4")
    print("================================")

    if not topics:

        print(
            "❌ No topics for AI Judge"
        )

        return []

    print(
        f"📊 Topics for AI Judge: {len(topics)}"
    )

    print()

    # ======================================
    # BUILD TOPIC LIST
    # ======================================

    numbered_topics = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        numbered_topics.append(
            f"{index}. {topic}"
        )

    topic_text = "\n".join(
        numbered_topics
    )

    prompt = f"""
{SYSTEM_PROMPT}

Analyze ALL of the following topics.

IMPORTANT:

Return exactly ONE JSON ARRAY.

There must be exactly one result for each topic.

Do not omit topics.

Do not invent new topics.

TOPICS:

{topic_text}
"""

    # ======================================
    # RETRY
    # ======================================

    max_attempts = 3

    response = None

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                f"🚀 Gemini batch request "
                f"{attempt}/{max_attempts}"
            )

            response = client.models.generate_content(

                model=MODEL_NAME,

                contents=prompt

            )

            break

        except Exception as error:

            error_text = str(error)

            print(
                f"⚠️ Gemini error: "
                f"{error_text[:500]}"
            )

            if "429" in error_text:

                wait_time = 35 * attempt

                print(
                    f"⏳ Waiting "
                    f"{wait_time}s..."
                )

                time.sleep(
                    wait_time
                )

            else:

                break

    # ======================================
    # COMPLETE FAILURE
    # ======================================

    if response is None:

        print()
        print(
            "❌ Gemini batch request failed"
        )

        print(
            "⚠️ Returning fallback results"
        )

        return [
            failed_result(topic)
            for topic in topics
        ]

    # ======================================
    # READ RESPONSE
    # ======================================

    try:

        text = response.text

        if not text:

            raise ValueError(
                "Empty Gemini response"
            )

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
                "Gemini response is not a JSON array"
            )

    except Exception as error:

        print(
            f"❌ Failed to parse Gemini JSON: "
            f"{error}"
        )

        return [
            failed_result(topic)
            for topic in topics
        ]

    # ======================================
    # MAP RESULTS BY TOPIC
    # ======================================

    result_map = {}

    for item in data:

        if not isinstance(
            item,
            dict
        ):

            continue

        topic = item.get(
            "topic"
        )

        if not topic:

            continue

        result_map[
            str(topic).strip().lower()
        ] = item

    # ======================================
    # FINAL RESULTS
    # ======================================

    results = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"🤖 [{index}/{len(topics)}] "
            f"{topic}"
        )

        item = result_map.get(
            str(topic).strip().lower()
        )

        if item is None:

            # Try fuzzy matching
            item = None

            for key, value in result_map.items():

                if (
                    str(topic).lower() in key
                    or
                    key in str(topic).lower()
                ):

                    item = value

                    break

        if item is None:

            result = failed_result(
                topic
            )

        else:

            result = validate_result(
                item,
                topic
            )

        results.append(
            result
        )

        status = (

            "✅ APPROVED"

            if result.get(
                "is_good_for_shorts",
                False
            )

            else

            "❌ REJECTED"

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

        print()

    # ======================================
    # SORT
    # ======================================

    results.sort(

        key=lambda item:
            item.get(
                "score",
                0
            ),

        reverse=True

    )

    approved_count = sum(

        1

        for item in results

        if item.get(
            "is_good_for_shorts",
            False
        )

    )

    print(
        f"✅ AI approved: "
        f"{approved_count}/{len(results)}"
    )

    return results
