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
# JUDGE PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to decide whether a trending topic is suitable
for creating an ORIGINAL English YouTube Short for a global audience.

GOOD TOPICS:

- artificial intelligence
- technology
- science
- space
- interesting discoveries
- psychology
- human behavior
- surprising facts
- future technology
- inventions
- business
- major world events
- unusual real-world stories

BAD TOPICS:

- video games
- gaming
- esports
- music videos
- songs
- dance videos
- movie trailers
- TV shows
- anime
- celebrity gossip
- sports matches
- sports highlights
- local events
- random people's names
- random search queries
- product searches without a strong story
- topics that only make sense to a local audience

IMPORTANT:

A topic does NOT need to contain keywords such as
AI, science, space, technology, etc.

Judge the actual meaning of the topic.

For example:

"NASA discovers unexpected object near Jupiter"
= GOOD

"HOME ALONE"
= BAD

"Stray Kids Dance Practice"
= BAD

"Scientists discover mysterious signal from deep space"
= GOOD

"ismael saibari"
= BAD

Return ONLY valid JSON.
"""


# ==========================================
# JUDGE ONE TOPIC
# ==========================================

def judge_topic(topic):

    prompt = f"""
{SYSTEM_PROMPT}

Analyze this trending topic:

"{topic}"

Return exactly this JSON structure:

{{
    "topic": "{topic}",
    "is_good_for_shorts": true,
    "category": "science",
    "global_interest": 0,
    "viral_potential": 0,
    "english_audience": 0,
    "story_potential": 0,
    "score": 0,
    "reason": "short explanation"
}}

Rules:

global_interest: 0-10
viral_potential: 0-10
english_audience: 0-10
story_potential: 0-10

score must be 0-100.

is_good_for_shorts must be true or false.

category must be a short English category.

reason must be concise.
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text.strip()

        # ==================================
        # REMOVE MARKDOWN JSON BLOCK
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

        result = json.loads(
            text
        )

        return result

    except Exception as error:

        print(
            f"⚠️ AI Judge error: {error}"
        )

        return {
            "topic": topic,
            "is_good_for_shorts": False,
            "category": "unknown",
            "global_interest": 0,
            "viral_potential": 0,
            "english_audience": 0,
            "story_potential": 0,
            "score": 0,
            "reason": "AI Judge failed"
        }


# ==========================================
# JUDGE MULTIPLE TOPICS
# ==========================================

def judge_topics(
    topics
):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE")
    print("================================")
    print()

    results = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"🤖 [{index}/{len(topics)}] "
            f"Analyzing: {topic}"
        )

        result = judge_topic(
            topic
        )

        results.append(
            result
        )

        print(
            f"   Score: "
            f"{result.get('score', 0)}/100"
        )

        print(
            f"   Category: "
            f"{result.get('category', 'unknown')}"
        )

        print(
            f"   Good: "
            f"{result.get('is_good_for_shorts', False)}"
        )

        print()

    results.sort(
        key=lambda item:
            item.get(
                "score",
                0
            ),
        reverse=True
    )

    return results
