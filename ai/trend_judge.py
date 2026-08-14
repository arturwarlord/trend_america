import os
import json
import re

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

Your job is to analyze trending topics and determine
which ones are suitable for creating ORIGINAL English
YouTube Shorts for a GLOBAL audience.

The goal is NOT to reproduce the original content.

The goal is to find a topic that can become an original
educational, factual, surprising or story-driven Short.

GOOD TOPICS:

- artificial intelligence
- technology
- science
- space
- astronomy
- interesting discoveries
- psychology
- human behavior
- surprising facts
- future technology
- inventions
- engineering
- business
- major world events
- unusual real-world stories
- mysterious phenomena
- historical discoveries
- medical/scientific discoveries
- important companies or technologies IF there is a strong story

BAD TOPICS:

- video games
- gaming
- esports
- sports matches
- sports highlights
- music videos
- songs
- dance videos
- movie trailers
- TV shows
- anime
- celebrity gossip
- random celebrity names
- random people's names
- local events
- local personalities
- generic product searches
- product names without a strong story
- search queries without a clear story
- content that only makes sense to one local audience
- gameplay
- reaction videos
- livestreams
- official music videos
- lyric videos
- dance practices

IMPORTANT:

Judge the ACTUAL MEANING of the topic.

Do NOT simply look for keywords like:
AI, technology, science, space.

For example:

"NASA discovers unexpected object near Jupiter"
= GOOD

"Scientists discover mysterious signal from deep space"
= GOOD

"Google Pixel"
= potentially GOOD if it represents a major technology story,
but should receive a lower score if there is no clear story.

"pixel 11 pro"
= usually BAD or LOW unless there is a major technological story.

"HOME ALONE"
= BAD

"Stray Kids Dance Practice"
= BAD

"Fortnite Chapter 7 Trailer"
= BAD

"Tesla announces revolutionary battery technology"
= GOOD

"Scientists discover a new species living deep underwater"
= GOOD

"Ismael Saibari"
= BAD

A topic can be popular and still be BAD for our channel.

We want topics with:

1. Global interest
2. Viral potential
3. English-speaking audience potential
4. Strong storytelling potential
5. Ability to create an ORIGINAL Short
6. Educational, surprising or informational value

Do not reward a topic simply because it has many views.

Music, gaming and entertainment trends should generally score low
unless the topic itself contains a strong real-world story.

Return ONLY valid JSON.

Do not use Markdown.

Do not use ```json.

Do not add explanations outside the JSON.
"""


# ==========================================
# BATCH JUDGE PROMPT
# ==========================================

def build_batch_prompt(topics):

    topic_lines = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        topic_lines.append(
            f'{index}. "{topic}"'
        )

    topics_text = "\n".join(
        topic_lines
    )

    return f"""
{SYSTEM_PROMPT}

Analyze ALL of the following trending topics.

TOPICS:

{topics_text}

Return exactly ONE JSON object with this structure:

{{
    "results": [
        {{
            "index": 1,
            "topic": "original topic",
            "is_good_for_shorts": true,
            "category": "technology",
            "global_interest": 0,
            "viral_potential": 0,
            "english_audience": 0,
            "story_potential": 0,
            "score": 0,
            "reason": "short explanation"
        }}
    ]
}}

IMPORTANT:

You MUST return exactly one result for EVERY topic.

The "index" must match the original topic number.

Do not skip topics.

Do not merge topics.

Do not invent topics.

Scores:

global_interest: 0-10
viral_potential: 0-10
english_audience: 0-10
story_potential: 0-10

score: 0-100

Use this general scoring logic:

- 80-100 = excellent topic for our Shorts channel
- 65-79 = potentially good
- 50-64 = weak / needs a stronger angle
- 30-49 = poor
- 0-29 = unsuitable

is_good_for_shorts should normally be true only when
the score is approximately 65 or higher.

The reason must be concise.

category must be a short English category such as:

technology
science
space
psychology
business
world events
history
inventions
AI
health
environment
other

Remember:

POPULAR ≠ GOOD.

We are specifically looking for topics that can become
original English informational Shorts.
"""


# ==========================================
# EXTRACT JSON
# ==========================================

def extract_json(text):

    if not text:
        raise ValueError(
            "Empty Gemini response"
        )

    text = text.strip()

    # --------------------------------------
    # Remove Markdown code blocks
    # --------------------------------------

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

        text = text.strip()

    # --------------------------------------
    # Find JSON object
    # --------------------------------------

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "Gemini did not return valid JSON"
        )

    text = text[
        start:
        end + 1
    ]

    return json.loads(
        text
    )


# ==========================================
# FALLBACK RESULT
# ==========================================

def create_fallback(
    topic
):

    return {

        "topic":
            topic,

        "is_good_for_shorts":
            False,

        "category":
            "unknown",

        "global_interest":
            0,

        "viral_potential":
            0,

        "english_audience":
            0,

        "story_potential":
            0,

        "score":
            0,

        "reason":
            "AI Judge failed"

    }


# ==========================================
# VALIDATE RESULT
# ==========================================

def normalize_result(
    result,
    topic
):

    if not isinstance(
        result,
        dict
    ):

        return create_fallback(
            topic
        )

    result["topic"] = topic

    # --------------------------------------
    # Numeric fields
    # --------------------------------------

    numeric_fields = [

        "global_interest",
        "viral_potential",
        "english_audience",
        "story_potential",
        "score"

    ]

    for field in numeric_fields:

        try:

            value = int(
                result.get(
                    field,
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            value = 0

        if field == "score":

            value = max(
                0,
                min(
                    value,
                    100
                )
            )

        else:

            value = max(
                0,
                min(
                    value,
                    10
                )
            )

        result[field] = value

    # --------------------------------------
    # Boolean
    # --------------------------------------

    result["is_good_for_shorts"] = bool(
        result.get(
            "is_good_for_shorts",
            False
        )
    )

    # --------------------------------------
    # Category
    # --------------------------------------

    category = result.get(
        "category",
        "unknown"
    )

    if not isinstance(
        category,
        str
    ):

        category = "unknown"

    result["category"] = (
        category.strip()
        or "unknown"
    )

    # --------------------------------------
    # Reason
    # --------------------------------------

    reason = result.get(
        "reason",
        ""
    )

    if not isinstance(
        reason,
        str
    ):

        reason = ""

    result["reason"] = (
        reason.strip()
        or "No reason provided"
    )

    return result


# ==========================================
# JUDGE TOPICS IN ONE BATCH
# ==========================================

def judge_topics(
    topics
):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE")
    print("================================")
    print()

    if not topics:

        print(
            "⚠️ No topics to analyze"
        )

        return []

    # ======================================
    # CLEAN TOPICS
    # ======================================

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

    if not clean_topics:

        return []

    print(
        f"📊 Topics for AI Judge: "
        f"{len(clean_topics)}"
    )

    print(
        "🚀 Sending all topics in ONE Gemini request..."
    )

    print()

    # ======================================
    # BUILD PROMPT
    # ======================================

    prompt = build_batch_prompt(
        clean_topics
    )

    try:

        # ==================================
        # ONE API REQUEST
        # ==================================

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text.strip()

        # ==================================
        # PARSE JSON
        # ==================================

        data = extract_json(
            text
        )

        raw_results = data.get(
            "results",
            []
        )

        if not isinstance(
            raw_results,
            list
        ):

            raise ValueError(
                "Invalid results format"
            )

        # ==================================
        # MAP BY INDEX
        # ==================================

        indexed_results = {}

        for result in raw_results:

            if not isinstance(
                result,
                dict
            ):

                continue

            index = result.get(
                "index"
            )

            try:

                index = int(
                    index
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            indexed_results[
                index
            ] = result

        # ==================================
        # BUILD FINAL RESULTS
        # ==================================

        results = []

        for index, topic in enumerate(
            clean_topics,
            start=1
        ):

            result = indexed_results.get(
                index
            )

            if result is None:

                result = create_fallback(
                    topic
                )

            else:

                result = normalize_result(
                    result,
                    topic
                )

            results.append(
                result
            )

            # ==================================
            # PRINT
            # ==================================

            print(
                f"🤖 [{index}/{len(clean_topics)}] "
                f"{topic}"
            )

            print(
                f"   Score: "
                f"{result['score']}/100"
            )

            print(
                f"   Category: "
                f"{result['category']}"
            )

            print(
                f"   Good: "
                f"{result['is_good_for_shorts']}"
            )

            print()

        # ==================================
        # SORT
        # ==================================

        results.sort(
            key=lambda item:
                item.get(
                    "score",
                    0
                ),
            reverse=True
        )

        # ==================================
        # STATISTICS
        # ==================================

        approved = [

            item

            for item in results

            if item.get(
                "is_good_for_shorts",
                False
            )

        ]

        print(
            "================================"
        )

        print(
            "📊 AI JUDGE COMPLETE"
        )

        print(
            "================================"
        )

        print()

        print(
            f"📥 Analyzed: "
            f"{len(results)}"
        )

        print(
            f"✅ Approved: "
            f"{len(approved)}"
        )

        print(
            f"❌ Rejected: "
            f"{len(results) - len(approved)}"
        )

        print()

        return results

    except Exception as error:

        print(
            f"⚠️ AI Judge error: "
            f"{error}"
        )

        # ==================================
        # FALLBACK
        # ==================================

        results = []

        for topic in clean_topics:

            results.append(
                create_fallback(
                    topic
                )
            )

        return results
