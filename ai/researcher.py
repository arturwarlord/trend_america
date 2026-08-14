import os
import json
import time
import re

from google import genai

from research.search import (
    search_topic,
    format_sources
)


# =========================================================
# GEMINI
# =========================================================

API_KEY = os.getenv(
    "GEMINI_KEY"
)

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

MODEL_NAME = (
    "gemini-3.5-flash-lite"
)


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = (
    "data/top_trends.json"
)

OUTPUT_FILE = (
    "data/researched_topics.json"
)

MAX_TOPICS = 10

MAX_SOURCES_PER_TOPIC = 8

MAX_RETRIES = 3

RETRY_DELAY = 3


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a professional research analyst for an
automated English YouTube Shorts channel.

Your job is to research a trending topic using the
provided search results.

The final video will be an ORIGINAL informational
YouTube Short.

==================================================
CRITICAL RULE
==================================================

DO NOT INVENT FACTS.

Only use information reasonably supported by the
provided sources.

If the sources do not provide enough evidence,
say so.

Do not invent:

- numbers
- dates
- prices
- names
- statistics
- discoveries
- product specifications
- quotes
- events
- causes
- locations

==================================================
RESEARCH GOAL
==================================================

Find useful factual information that can later be
used to create a 30-60 second YouTube Short.

Look for:

- what happened
- what the topic means
- why it matters
- important facts
- surprising details
- historical context
- technological explanation
- business implications
- scientific explanation
- consequences
- dates
- numbers
- organizations
- people involved

==================================================
SOURCE QUALITY
==================================================

Prefer information from:

- major news organizations
- government sources
- scientific organizations
- universities
- official company sources
- established publications

Be careful with:

- social media
- blogs
- unknown websites
- sensational headlines

==================================================
IMPORTANT
==================================================

The trend title itself may be vague.

Do NOT turn a vague title into an invented story.

If the topic is:

"NASA"

do not invent a specific NASA discovery.

Instead explain what the sources actually show.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return exactly one object.

Format:

{
    "topic": "original topic",
    "research_quality": 0,
    "summary": "Short factual summary.",
    "key_facts": [
        "Fact 1",
        "Fact 2",
        "Fact 3"
    ],
    "important_numbers": [
        "Number or statistic if supported"
    ],
    "important_dates": [
        "Date if supported"
    ],
    "people": [
        "Person if relevant"
    ],
    "organizations": [
        "Organization if relevant"
    ],
    "story_angles": [
        "Possible story angle 1",
        "Possible story angle 2"
    ],
    "source_count": 0,
    "confidence": 0,
    "reason": "Why this research is or is not strong enough."
}

All information must be supported by the provided
sources.

research_quality and confidence must be values from
0 to 10.
"""


# =========================================================
# LOAD TOP TRENDS
# =========================================================

def load_top_trends():

    if not os.path.exists(
        INPUT_FILE
    ):

        print(
            f"❌ File not found: "
            f"{INPUT_FILE}"
        )

        return []

    try:

        with open(
            INPUT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

    except Exception as error:

        print(
            f"❌ Failed to load "
            f"{INPUT_FILE}"
        )

        print(
            str(error)
        )

        return []

    if not isinstance(
        data,
        list
    ):

        print(
            "❌ top_trends.json "
            "must contain an array"
        )

        return []

    return data


# =========================================================
# CLEAN JSON
# =========================================================

def clean_json(
    text
):

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

    # ---------------------------------------------
    # Find JSON object
    # ---------------------------------------------

    start = text.find(
        "{"
    )

    end = text.rfind(
        "}"
    )

    if start != -1 and end != -1:

        text = text[
            start:end + 1
        ]

    return text.strip()


# =========================================================
# NORMALIZE NUMBER
# =========================================================

def normalize_number(
    value
):

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

    return round(
        value,
        2
    )


# =========================================================
# NORMALIZE LIST
# =========================================================

def normalize_list(
    value
):

    if not isinstance(
        value,
        list
    ):

        return []

    result = []

    for item in value:

        if item is None:

            continue

        item = str(
            item
        ).strip()

        if not item:

            continue

        result.append(
            item
        )

    return result


# =========================================================
# VALIDATE RESEARCH
# =========================================================

def validate_research(
    data,
    original_topic,
    source_count
):

    if not isinstance(
        data,
        dict
    ):

        return {

            "topic": original_topic,

            "research_quality": 0,

            "summary": "",

            "key_facts": [],

            "important_numbers": [],

            "important_dates": [],

            "people": [],

            "organizations": [],

            "story_angles": [],

            "source_count": source_count,

            "confidence": 0,

            "reason": "Invalid AI research result."

        }

    # ---------------------------------------------
    # ALWAYS preserve topic
    # ---------------------------------------------

    data["topic"] = (
        original_topic
    )

    # ---------------------------------------------
    # Numeric values
    # ---------------------------------------------

    data[
        "research_quality"
    ] = normalize_number(
        data.get(
            "research_quality",
            0
        )
    )

    data[
        "confidence"
    ] = normalize_number(
        data.get(
            "confidence",
            0
        )
    )

    # ---------------------------------------------
    # Text
    # ---------------------------------------------

    data[
        "summary"
    ] = str(
        data.get(
            "summary",
            ""
        )
    ).strip()

    data[
        "reason"
    ] = str(
        data.get(
            "reason",
            ""
        )
    ).strip()

    # ---------------------------------------------
    # Lists
    # ---------------------------------------------

    data[
        "key_facts"
    ] = normalize_list(
        data.get(
            "key_facts",
            []
        )
    )

    data[
        "important_numbers"
    ] = normalize_list(
        data.get(
            "important_numbers",
            []
        )
    )

    data[
        "important_dates"
    ] = normalize_list(
        data.get(
            "important_dates",
            []
        )
    )

    data[
        "people"
    ] = normalize_list(
        data.get(
            "people",
            []
        )
    )

    data[
        "organizations"
    ] = normalize_list(
        data.get(
            "organizations",
            []
        )
    )

    data[
        "story_angles"
    ] = normalize_list(
        data.get(
            "story_angles",
            []
        )
    )

    data[
        "source_count"
    ] = source_count

    return data


# =========================================================
# FAILED RESULT
# =========================================================

def failed_result(
    topic,
    source_count=0,
    reason="Research failed"
):

    return {

        "topic": topic,

        "research_quality": 0,

        "summary": "",

        "key_facts": [],

        "important_numbers": [],

        "important_dates": [],

        "people": [],

        "organizations": [],

        "story_angles": [],

        "source_count": source_count,

        "confidence": 0,

        "reason": reason

    }


# =========================================================
# BUILD PROMPT
# =========================================================

def build_prompt(
    topic,
    sources
):

    sources_text = format_sources(
        sources
    )

    return f"""
{SYSTEM_PROMPT}

==================================================
TOPIC
==================================================

{topic}

==================================================
SEARCH RESULTS
==================================================

{sources_text}

==================================================
FINAL INSTRUCTIONS
==================================================

Research ONLY the topic above.

Use only the provided search results.

Cross-check information when possible.

Do not invent facts.

Return exactly one JSON object.

Return valid JSON only.
"""


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
# RESEARCH ONE TOPIC
# =========================================================

def research_topic(
    topic,
    index,
    total
):

    print()
    print(
        "================================"
    )

    print(
        f"🔬 RESEARCH "
        f"{index}/{total}"
    )

    print(
        "================================"
    )

    print(
        f"📌 Topic: {topic}"
    )

    # ---------------------------------------------
    # Search
    # ---------------------------------------------

    sources = search_topic(

        topic,

        max_results=(
            MAX_SOURCES_PER_TOPIC
        )

    )

    source_count = len(
        sources
    )

    if not sources:

        print(
            "❌ No sources found"
        )

        return failed_result(

            topic,

            0,

            "No sources found."

        )

    print(
        f"📰 Sources: "
        f"{source_count}"
    )

    # ---------------------------------------------
    # Prompt
    # ---------------------------------------------

    prompt = build_prompt(

        topic,

        sources

    )

    # ---------------------------------------------
    # Retry
    # ---------------------------------------------

    for attempt in range(

        1,

        MAX_RETRIES + 1

    ):

        try:

            print(
                f"🤖 Gemini research "
                f"attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            text = request_gemini(
                prompt
            )

            cleaned = clean_json(
                text
            )

            if not cleaned:

                raise ValueError(
                    "Gemini returned empty JSON"
                )

            data = json.loads(
                cleaned
            )

            result = validate_research(

                data,

                topic,

                source_count

            )

            print(
                "✅ Research completed"
            )

            print(
                f"   Quality: "
                f"{result['research_quality']:.0f}/10"
            )

            print(
                f"   Confidence: "
                f"{result['confidence']:.0f}/10"
            )

            print(
                f"   Facts: "
                f"{len(result['key_facts'])}"
            )

            return result

        except Exception as error:

            print()

            print(
                f"⚠️ Research attempt "
                f"{attempt} failed"
            )

            print(
                str(error)
            )

            if attempt < MAX_RETRIES:

                print(
                    f"🔄 Retrying in "
                    f"{RETRY_DELAY}s..."
                )

                time.sleep(
                    RETRY_DELAY
                )

    return failed_result(

        topic,

        source_count,

        "Gemini research failed "
        "after retries."

    )


# =========================================================
# SAVE RESULTS
# =========================================================

def save_results(
    results
):

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    with open(

        OUTPUT_FILE,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            results,

            file,

            ensure_ascii=False,

            indent=4

        )

    print()
    print(
        f"💾 Saved: "
        f"{OUTPUT_FILE}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "================================"
    )

    print(
        "🔬 AI RESEARCH ENGINE"
    )

    print(
        "================================"
    )

    print()

    # ---------------------------------------------
    # Load approved trends
    # ---------------------------------------------

    trends = load_top_trends()

    if not trends:

        print(
            "❌ No approved trends found."
        )

        print(
            f"Expected: "
            f"{INPUT_FILE}"
        )

        return

    # ---------------------------------------------
    # Limit
    # ---------------------------------------------

    trends = trends[
        :MAX_TOPICS
    ]

    print(
        f"📥 Topics received: "
        f"{len(trends)}"
    )

    print()

    # ---------------------------------------------
    # Research
    # ---------------------------------------------

    results = []

    total = len(
        trends
    )

    for index, trend in enumerate(

        trends,

        start=1

    ):

        if isinstance(
            trend,
            dict
        ):

            topic = trend.get(
                "topic",
                ""
            )

        else:

            topic = str(
                trend
            )

        topic = str(
            topic
        ).strip()

        if not topic:

            continue

        result = research_topic(

            topic,

            index,

            total

        )

        # -----------------------------------------
        # Preserve original trend information
        # -----------------------------------------

        if isinstance(
            trend,
            dict
        ):

            result[
                "trend_score"
            ] = trend.get(
                "score",
                0
            )

            result[
                "category"
            ] = trend.get(
                "category",
                "other"
            )

            result[
                "viral_potential"
            ] = trend.get(
                "viral_potential",
                0
            )

            result[
                "global_interest"
            ] = trend.get(
                "global_interest",
                0
            )

        results.append(
            result
        )

        # -----------------------------------------
        # Small delay between topics
        # -----------------------------------------

        if index < total:

            time.sleep(
                1
            )

    # ---------------------------------------------
    # Save
    # ---------------------------------------------

    save_results(
        results
    )

    # ---------------------------------------------
    # Summary
    # ---------------------------------------------

    successful = 0

    for result in results:

        if result.get(
            "confidence",
            0
        ) >= 5:

            successful += 1

    print()
    print(
        "================================"
    )

    print(
        "✅ RESEARCH PIPELINE COMPLETED"
    )

    print(
        "================================"
    )

    print()

    print(
        f"📊 Topics researched: "
        f"{len(results)}"
    )

    print(
        f"✅ Research usable: "
        f"{successful}"
    )

    print(
        f"📁 Output: "
        f"{OUTPUT_FILE}"
    )

    print()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()
