import os
import json
import re

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

MIN_CONFIDENCE = 7


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a factual research analyst for an English YouTube Shorts
channel targeting a global audience.

Your job is NOT to invent a story.

You receive:

1. A trending topic.
2. Search results / source material.

Your task is to determine whether the topic contains a
REAL, SPECIFIC and INTERESTING factual story.

==================================================
CRITICAL RULE
==================================================

NEVER invent:

- dates
- numbers
- people
- companies
- announcements
- events
- statistics
- quotes
- locations
- scientific claims

If the supplied sources do not support a claim,
DO NOT use it.

If there is not enough evidence for a concrete story,
reject the topic.

==================================================
GOOD RESEARCH RESULT
==================================================

A good result should identify:

- WHAT happened
- WHO or WHAT is involved
- WHY it matters
- WHEN it happened
- the surprising or interesting detail
- enough verified facts for a 30-60 second Short

==================================================
BAD RESULT
==================================================

Reject if:

- topic is only a keyword
- sources are weak
- sources are unrelated
- story cannot be established
- information is contradictory
- facts are insufficient
- story requires speculation
- story is gaming/music/movie/celebrity/sports content

==================================================
GLOBAL AUDIENCE
==================================================

The story should be understandable to an English-speaking
global audience.

Prefer:

technology
AI
science
space
business
engineering
discoveries
psychology
history
future technology
major world events
unusual real-world events

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{
    "approved": true,
    "topic": "...",
    "story_title": "...",
    "hook": "...",
    "summary": "...",
    "why_interesting": "...",
    "facts": [
        "...",
        "...",
        "..."
    ],
    "confidence": 8,
    "reason": "...",
    "sources": [
        {
            "title": "...",
            "url": "..."
        }
    ]
}

If rejected:

{
    "approved": false,
    "topic": "...",
    "story_title": "",
    "hook": "",
    "summary": "",
    "why_interesting": "",
    "facts": [],
    "confidence": 0,
    "reason": "...",
    "sources": []
}
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

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text.strip()


# =========================================================
# FAILED RESULT
# =========================================================

def failed_result(topic, reason):

    return {
        "approved": False,
        "topic": topic,
        "story_title": "",
        "hook": "",
        "summary": "",
        "why_interesting": "",
        "facts": [],
        "confidence": 0,
        "reason": reason,
        "sources": []
    }


# =========================================================
# RESEARCH ONE TOPIC
# =========================================================

def research_topic(topic, sources=None):

    if sources is None:
        sources = []

    print()
    print("================================")
    print("🔎 AI RESEARCHER")
    print("================================")

    print(
        f"📌 Topic: {topic}"
    )

    # =====================================================
    # FORMAT SOURCES
    # =====================================================

    if sources:

        sources_text = "\n\n".join(

            f"TITLE: {source.get('title', '')}\n"
            f"URL: {source.get('url', '')}\n"
            f"CONTENT: {source.get('content', '')}"

            for source in sources

        )

    else:

        sources_text = (
            "NO EXTERNAL SOURCES PROVIDED."
        )

    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
{SYSTEM_PROMPT}

TRENDING TOPIC:

{topic}

SOURCE MATERIAL:

{sources_text}

Analyze the topic using ONLY the supplied source material.

If the source material does not establish a specific factual
story, reject the topic.

Return ONLY the JSON object.
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text

        if not text:

            return failed_result(
                topic,
                "Empty Gemini response"
            )

        text = clean_json(text)

        result = json.loads(text)

        # =================================================
        # NORMALIZE
        # =================================================

        result["topic"] = topic

        if not isinstance(
            result.get("facts"),
            list
        ):
            result["facts"] = []

        if not isinstance(
            result.get("sources"),
            list
        ):
            result["sources"] = []

        try:

            confidence = float(
                result.get(
                    "confidence",
                    0
                )
            )

        except Exception:

            confidence = 0

        confidence = max(
            0,
            min(
                10,
                confidence
            )
        )

        result["confidence"] = confidence

        # =================================================
        # HARD RULES
        # =================================================

        if confidence < MIN_CONFIDENCE:

            result["approved"] = False

        if len(result["facts"]) < 2:

            result["approved"] = False

        if not result.get(
            "summary"
        ):

            result["approved"] = False

        if not result.get(
            "hook"
        ):

            result["approved"] = False

        # =================================================
        # PRINT
        # =================================================

        status = (
            "✅ APPROVED"
            if result.get(
                "approved",
                False
            )
            else "❌ REJECTED"
        )

        print(
            f"   {status}"
        )

        print(
            f"   Confidence: "
            f"{confidence:.0f}/10"
        )

        print(
            f"   Story: "
            f"{result.get('story_title', '')}"
        )

        print(
            f"   Reason: "
            f"{result.get('reason', '')}"
        )

        print()

        return result

    except Exception as error:

        print(
            f"⚠️ Researcher error: {error}"
        )

        return failed_result(
            topic,
            "Research failed"
        )


# =========================================================
# RESEARCH MULTIPLE TOPICS
# =========================================================

def research_topics(topics):

    print()
    print("================================")
    print("🔎 AI RESEARCH PHASE")
    print("================================")

    if not topics:

        print(
            "❌ No approved topics"
        )

        return []

    results = []

    for topic_data in topics:

        if isinstance(
            topic_data,
            dict
        ):

            topic = topic_data.get(
                "topic",
                ""
            )

        else:

            topic = str(
                topic_data
            )

        if not topic:
            continue

        result = research_topic(
            topic
        )

        results.append(
            result
        )

    approved = [

        result

        for result in results

        if result.get(
            "approved",
            False
        )

    ]

    print()
    print(
        f"🔎 Research approved: "
        f"{len(approved)}/{len(results)}"
    )

    return approved
