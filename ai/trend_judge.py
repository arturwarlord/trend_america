import os
import json

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


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "gemini-3.5-flash-lite"


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = "data/top_trends.json"
OUTPUT_FILE = "data/selected_topic.json"


# =========================================================
# LOAD TOP TRENDS
# =========================================================

def load_topics():

    if not os.path.exists(INPUT_FILE):

        print(
            f"❌ File not found: {INPUT_FILE}"
        )

        return []

    try:

        with open(
            INPUT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except Exception as error:

        print(
            f"❌ Failed to load topics: {error}"
        )

        return []

    if not isinstance(data, list):

        print(
            "❌ top_trends.json must contain a list"
        )

        return []

    return data


# =========================================================
# BUILD PROMPT
# =========================================================

def build_prompt(topics):

    topics_text = "\n".join(

        f"""
#{index}
Topic: {topic.get("topic", "")}
Score: {topic.get("score", 0)}
Category: {topic.get("category", "other")}
Global Interest: {topic.get("global_interest", 0)}
Viral Potential: {topic.get("viral_potential", 0)}
English Audience: {topic.get("english_audience", 0)}
Story Potential: {topic.get("story_potential", 0)}
Specificity: {topic.get("specificity", 0)}
Facts: {topic.get("factual_confidence", 0)}
Originality: {topic.get("originality", 0)}
Reason: {topic.get("reason", "")}
"""
        for index, topic
        in enumerate(topics, start=1)

    )

    return f"""

You are the FINAL TOPIC SELECTOR for a global
English YouTube Shorts channel.

The AI Trend Judge has already approved the topics.

Your job is NOT to judge whether they are allowed.

Your job is to select ONE topic that has the
highest potential for a viral ORIGINAL informational
YouTube Short.

==================================================
PRIORITY
==================================================

Prefer a topic that has:

1. Strong global interest
2. Strong viral potential
3. Strong story potential
4. High English audience potential
5. Clear factual research potential
6. Strong hook potential
7. Enough specificity to build a real story
8. Interesting information that can surprise viewers

==================================================
IMPORTANT
==================================================

Do NOT simply select the topic with the highest score.

Think about which topic can become the strongest
30-60 second informational Short.

The final video must be based on REAL information.

Do not invent facts.

==================================================
TOPICS
==================================================

{topics_text}

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Return exactly:

{{
    "topic": "EXACT ORIGINAL TOPIC",
    "reason": "Why this is the strongest topic",
    "score": 0
}}

The topic MUST be copied exactly from the input.

Do not rewrite it.

Do not add markdown.

"""


# =========================================================
# SELECT TOPIC
# =========================================================

def select_topic(topics):

    if not topics:

        print(
            "❌ No approved topics available"
        )

        return None

    print()
    print("================================")
    print("🎯 FINAL TOPIC SELECTION")
    print("================================")
    print()

    print(
        f"📚 Candidates: {len(topics)}"
    )

    prompt = build_prompt(
        topics
    )

    try:

        response = client.models.generate_content(

            model=MODEL_NAME,

            contents=prompt,

            config={
                "response_mime_type":
                    "application/json"
            }

        )

        text = getattr(
            response,
            "text",
            None
        )

        if not text:

            print(
                "❌ Gemini returned empty response"
            )

            return None

        data = json.loads(
            text
        )

    except Exception as error:

        print()
        print(
            f"❌ Topic selector error: {error}"
        )

        return None

    if not isinstance(
        data,
        dict
    ):

        print(
            "❌ Invalid selector response"
        )

        return None

    selected_topic = str(
        data.get(
            "topic",
            ""
        )
    ).strip()

    if not selected_topic:

        print(
            "❌ Gemini did not select a topic"
        )

        return None

    # =====================================================
    # VERIFY TOPIC
    # =====================================================

    original_topics = {

        str(
            item.get(
                "topic",
                ""
            )
        ).strip()

        for item in topics

    }

    if selected_topic not in original_topics:

        print()
        print(
            "❌ Gemini returned a topic "
            "that was not in the approved list:"
        )

        print(
            selected_topic
        )

        return None

    # =====================================================
    # FIND ORIGINAL OBJECT
    # =====================================================

    selected = None

    for item in topics:

        if str(
            item.get(
                "topic",
                ""
            )
        ).strip() == selected_topic:

            selected = dict(
                item
            )

            break

    if selected is None:

        return None

    # =====================================================
    # ADD SELECTOR DATA
    # =====================================================

    selected["selection_reason"] = str(
        data.get(
            "reason",
            ""
        )
    ).strip()

    selected["selector_score"] = data.get(
        "score",
        selected.get(
            "score",
            0
        )
    )

    return selected


# =========================================================
# SAVE
# =========================================================

def save_selected_topic(topic):

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
            topic,
            file,
            ensure_ascii=False,
            indent=4
        )

    print()
    print(
        f"💾 Saved: {OUTPUT_FILE}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    topics = load_topics()

    if not topics:

        return

    selected = select_topic(
        topics
    )

    if not selected:

        print(
            "❌ No final topic selected"
        )

        return

    print()
    print("================================")
    print("🏆 FINAL TOPIC")
    print("================================")
    print()

    print(
        selected.get(
            "topic",
            ""
        )
    )

    print()

    print(
        f"Judge Score: "
        f"{selected.get('score', 0):.0f}/100"
    )

    print(
        f"Selector Score: "
        f"{selected.get('selector_score', 0)}"
    )

    print(
        f"Category: "
        f"{selected.get('category', 'other')}"
    )

    print()

    print(
        "Reason:"
    )

    print(
        selected.get(
            "selection_reason",
            ""
        )
    )

    save_selected_topic(
        selected
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()
