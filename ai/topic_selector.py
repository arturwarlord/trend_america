import os
import json
import re

from google import genai


# =========================================================
# SETTINGS
# =========================================================

API_KEY = os.getenv("GEMINI_KEY")

if not API_KEY:
    raise RuntimeError(
        "❌ GEMINI_KEY is not configured"
    )


MODEL_NAME = "gemini-3.5"


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# HELPERS
# =========================================================

def clean_json_response(text):

    text = text.strip()

    # Remove markdown code fences
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

    return text.strip()


# =========================================================
# PREPARE TOPICS
# =========================================================

def prepare_topics(topics):

    prepared = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        if not isinstance(topic, dict):
            continue

        title = str(
            topic.get(
                "topic",
                ""
            )
        ).strip()

        if not title:
            continue

        prepared.append({

            "index": index,

            "topic": title,

            "score": topic.get(
                "score",
                0
            ),

            "category": topic.get(
                "category",
                "unknown"
            ),

            "global_interest": topic.get(
                "global_interest",
                0
            ),

            "viral_potential": topic.get(
                "viral_potential",
                0
            ),

            "english_audience": topic.get(
                "english_audience",
                0
            ),

            "story_potential": topic.get(
                "story_potential",
                0
            ),

            "specificity": topic.get(
                "specificity",
                0
            ),

            "factual_confidence": topic.get(
                "factual_confidence",
                0
            ),

            "originality": topic.get(
                "originality",
                0
            ),

            "reason": topic.get(
                "reason",
                ""
            )

        })

    return prepared


# =========================================================
# AI TOPIC SELECTOR
# =========================================================

def select_with_ai(topics):

    topics_text = json.dumps(
        topics,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are the final topic selector for an automated
GLOBAL ENGLISH YouTube Shorts channel.

The topics below have ALREADY passed a strict AI Judge.

Your job is NOT to reject them again.

Your job is to select EXACTLY ONE topic that has
the strongest potential to become a viral,
informational YouTube Short.

IMPORTANT:

The final video will be:

- English
- 30-60 seconds
- vertical YouTube Short
- informational
- designed for a global audience
- based on factual information
- narrated with AI voice
- supported by stock footage

Evaluate the candidates using:

1. Viral potential
2. Curiosity
3. Strength of the opening hook
4. Global audience appeal
5. Storytelling potential
6. Ability to explain the topic quickly
7. Visual storytelling potential
8. Factual reliability
9. Originality
10. Potential for comments/discussion
11. Current relevance
12. Potential to make viewers watch until the end

IMPORTANT:

Do NOT automatically choose the candidate
with the highest existing AI score.

The existing score is only one signal.

For example:

A topic with score 77 is NOT automatically better
than a topic with score 69.

Prefer a topic that creates a strong question
in the viewer's mind.

Good examples:

"Why does this happen?"

"Scientists discovered something strange..."

"Nobody expected this..."

"This changes what we thought about..."

"Here's why..."

Avoid topics that are:

- too generic
- too technical
- too local
- difficult to explain in under 60 seconds
- dependent on long context
- boring without visual explanation

The selected topic must be suitable for
an English global YouTube Shorts channel.

CANDIDATE TOPICS:

{topics_text}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "selected_index": 1,
    "topic": "exact topic from candidates",
    "final_score": 0,
    "hook_score": 0,
    "curiosity_score": 0,
    "global_score": 0,
    "story_score": 0,
    "visual_score": 0,
    "reason": "short explanation why this topic is the best choice",
    "suggested_hook": "one powerful English hook for the Short"
}}

Rules:

- selected_index must match one of the candidate indexes.
- topic must exactly match the selected candidate.
- Scores must be integers from 0 to 100.
- final_score must represent the overall quality.
- suggested_hook must be short and attention-grabbing.
- Do not include Markdown.
- Do not include additional fields.
"""


    response = client.models.generate_content(

        model=MODEL_NAME,

        contents=prompt

    )


    if not response.text:

        raise RuntimeError(
            "❌ Topic Selector returned empty response"
        )


    raw_text = response.text.strip()

    clean_text = clean_json_response(
        raw_text
    )


    try:

        result = json.loads(
            clean_text
        )

    except json.JSONDecodeError:

        print()
        print(
            "❌ Invalid JSON from Topic Selector:"
        )

        print(
            raw_text
        )

        raise RuntimeError(
            "Topic Selector returned invalid JSON"
        )


    return result


# =========================================================
# VALIDATE RESULT
# =========================================================

def validate_selection(
    result,
    topics
):

    selected_index = result.get(
        "selected_index"
    )

    if not isinstance(
        selected_index,
        int
    ):

        raise RuntimeError(
            "❌ Invalid selected_index"
        )


    if selected_index < 1:

        raise RuntimeError(
            "❌ selected_index is below 1"
        )


    if selected_index > len(topics):

        raise RuntimeError(
            "❌ selected_index is outside candidate range"
        )


    selected_candidate = topics[
        selected_index - 1
    ]


    selected_topic = str(
        result.get(
            "topic",
            ""
        )
    ).strip()


    # AI must return the exact topic
    if selected_topic != selected_candidate["topic"]:

        print(
            "⚠️ AI topic text differs from candidate."
        )

        print(
            f"AI:        {selected_topic}"
        )

        print(
            f"Candidate: {selected_candidate['topic']}"
        )

        # Use trusted candidate value
        selected_topic = selected_candidate[
            "topic"
        ]


    result["topic"] = selected_topic


    # Keep original Judge data
    result["category"] = selected_candidate.get(
        "category",
        "unknown"
    )

    result["judge_score"] = selected_candidate.get(
        "score",
        0
    )

    result["global_interest"] = selected_candidate.get(
        "global_interest",
        0
    )

    result["viral_potential"] = selected_candidate.get(
        "viral_potential",
        0
    )

    result["english_audience"] = selected_candidate.get(
        "english_audience",
        0
    )

    result["story_potential"] = selected_candidate.get(
        "story_potential",
        0
    )

    result["specificity"] = selected_candidate.get(
        "specificity",
        0
    )

    result["factual_confidence"] = selected_candidate.get(
        "factual_confidence",
        0
    )

    result["originality"] = selected_candidate.get(
        "originality",
        0
    )


    return result


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def select_topic(topics):

    print()
    print(
        "================================"
    )
    print(
        "🎯 AI TOPIC SELECTOR"
    )
    print(
        "================================"
    )
    print()


    if not topics:

        print(
            "❌ No approved topics available"
        )

        return None


    prepared_topics = prepare_topics(
        topics
    )


    if not prepared_topics:

        print(
            "❌ No valid topics available"
        )

        return None


    print(
        f"📥 Approved candidates: "
        f"{len(prepared_topics)}"
    )

    print()


    for item in prepared_topics:

        print(
            f"#{item['index']} "
            f"{item['topic']}"
        )

        print(
            f"   Judge Score: "
            f"{item['score']}/100"
        )

        print(
            f"   Viral: "
            f"{item['viral_potential']}/10"
        )

        print(
            f"   Global: "
            f"{item['global_interest']}/10"
        )

        print(
            f"   Story: "
            f"{item['story_potential']}/10"
        )

        print()


    # =====================================================
    # AI SELECTION
    # =====================================================

    print(
        "🧠 Asking AI to select the final topic..."
    )

    print()


    result = select_with_ai(
        prepared_topics
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    result = validate_selection(
        result,
        prepared_topics
    )


    # =====================================================
    # FINAL OUTPUT
    # =====================================================

    print()
    print(
        "================================"
    )
    print(
        "🏆 FINAL TOPIC"
    )
    print(
        "================================"
    )
    print()


    print(
        f"🔥 {result['topic']}"
    )

    print()

    print(
        f"📊 Judge Score: "
        f"{result.get('judge_score', 0)}/100"
    )

    print(
        f"🧠 Final AI Score: "
        f"{result.get('final_score', 0)}/100"
    )

    print(
        f"🎣 Hook Score: "
        f"{result.get('hook_score', 0)}/100"
    )

    print(
        f"❓ Curiosity: "
        f"{result.get('curiosity_score', 0)}/100"
    )

    print(
        f"🌎 Global: "
        f"{result.get('global_score', 0)}/100"
    )

    print(
        f"📖 Story: "
        f"{result.get('story_score', 0)}/100"
    )

    print(
        f"🎬 Visual: "
        f"{result.get('visual_score', 0)}/100"
    )

    print()

    print(
        f"💡 Reason: "
        f"{result.get('reason', '')}"
    )

    print()

    print(
        f"🎣 Suggested Hook:"
    )

    print(
        f"   {result.get('suggested_hook', '')}"
    )

    print()


    return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    test_topics = [

        {
            "topic": "iphone 15 pro",
            "score": 77,
            "category": "technology",
            "global_interest": 8,
            "viral_potential": 7,
            "english_audience": 9,
            "story_potential": 7,
            "specificity": 8,
            "factual_confidence": 9,
            "originality": 6,
            "reason": "High-interest consumer technology topic."
        },

        {
            "topic": "google pixel 10",
            "score": 72,
            "category": "technology",
            "global_interest": 7,
            "viral_potential": 7,
            "english_audience": 9,
            "story_potential": 7,
            "specificity": 7,
            "factual_confidence": 8,
            "originality": 6,
            "reason": "Upcoming major tech release."
        },

        {
            "topic": "australian housing market",
            "score": 69,
            "category": "business",
            "global_interest": 6,
            "viral_potential": 6,
            "english_audience": 8,
            "story_potential": 8,
            "specificity": 6,
            "factual_confidence": 8,
            "originality": 6,
            "reason": "Strong economic topic."
        },

        {
            "topic": "flood situation near baitarani river",
            "score": 65,
            "category": "world",
            "global_interest": 5,
            "viral_potential": 6,
            "english_audience": 6,
            "story_potential": 7,
            "specificity": 7,
            "factual_confidence": 8,
            "originality": 6,
            "reason": "Real-world natural event."
        }

    ]


    selected = select_topic(
        test_topics
    )


    print(
        json.dumps(
            selected,
            ensure_ascii=False,
            indent=2
        )
    )
