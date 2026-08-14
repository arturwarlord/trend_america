import os
import json
import re
from typing import List, Dict

from google import genai


# =========================================================
# SETTINGS
# =========================================================

API_KEY = os.getenv("GEMINI_KEY")

if not API_KEY:
    raise RuntimeError("❌ GEMINI_KEY is not configured")


MODEL_NAME = "gemini-3.5"


HISTORY_FILE = "topic_history.json"


MAX_TOPICS_FOR_AI = 30


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# HISTORY
# =========================================================

def load_history() -> List[str]:

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return data.get("topics", [])

    except Exception as e:

        print(
            f"⚠️ Cannot load topic history: {e}"
        )

    return []


# =========================================================
# NORMALIZE
# =========================================================

def normalize_topic(topic: str) -> str:

    topic = topic.lower().strip()

    topic = re.sub(
        r"[^\w\s]",
        "",
        topic,
        flags=re.UNICODE
    )

    topic = re.sub(
        r"\s+",
        " ",
        topic
    )

    return topic


# =========================================================
# DUPLICATE CHECK
# =========================================================

def is_duplicate(
    topic: str,
    history: List[str]
) -> bool:

    normalized = normalize_topic(topic)

    for old_topic in history:

        old_normalized = normalize_topic(
            old_topic
        )

        if normalized == old_normalized:
            return True

        # Простая проверка похожих тем
        words_a = set(normalized.split())
        words_b = set(old_normalized.split())

        if not words_a or not words_b:
            continue

        intersection = len(
            words_a & words_b
        )

        similarity = intersection / max(
            len(words_a),
            len(words_b)
        )

        if similarity >= 0.75:
            return True

    return False


# =========================================================
# PREPARE TRENDS
# =========================================================

def prepare_topics(
    trends: List[Dict]
) -> List[Dict]:

    history = load_history()

    result = []

    for trend in trends:

        topic = trend.get("topic")

        if not topic:
            continue

        if is_duplicate(
            topic,
            history
        ):
            print(
                f"⏭️ Duplicate topic: {topic}"
            )

            continue

        result.append(trend)

    return result


# =========================================================
# AI SELECTION
# =========================================================

def select_with_ai(
    trends: List[Dict]
) -> Dict:

    if not trends:
        raise RuntimeError(
            "❌ No suitable topics available"
        )

    trends = trends[:MAX_TOPICS_FOR_AI]

    topics_text = []

    for i, trend in enumerate(
        trends,
        start=1
    ):

        topic = trend.get(
            "topic",
            ""
        )

        source = trend.get(
            "source",
            "unknown"
        )

        score = trend.get(
            "score",
            0
        )

        topics_text.append(
            f"""
#{i}
Topic: {topic}
Source: {source}
Score: {score}
"""
        )

    topics_text = "\n".join(
        topics_text
    )


    prompt = f"""
You are an expert YouTube Shorts topic selector.

Your task is to select ONE topic with the highest viral potential.

The final video will be a short vertical YouTube Short.

Evaluate every topic using:

1. Viral potential
2. Current relevance
3. Curiosity
4. Emotional impact
5. Ability to create a strong hook
6. Ability to explain the topic in 30-60 seconds
7. Global audience potential
8. Comment/discussion potential
9. Uniqueness
10. Potential for visual storytelling

IMPORTANT:

Do NOT simply select the topic with the highest numeric score.

Think like a professional YouTube Shorts strategist.

Avoid:
- boring educational topics
- extremely narrow topics
- topics requiring long explanations
- repetitive topics
- topics with weak hooks

Prefer:
- surprising facts
- mysteries
- psychology
- science
- technology
- strange events
- human behavior
- paradoxes
- discoveries
- shocking statistics
- questions that make people want to know the answer

AVAILABLE TOPICS:

{topics_text}

Return ONLY valid JSON.

Format:

{{
    "index": 1,
    "topic": "selected topic",
    "reason": "short explanation",
    "viral_score": 0,
    "hook_score": 0,
    "curiosity_score": 0,
    "global_score": 0,
    "final_score": 0
}}

All scores must be integers from 0 to 100.
"""


    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )


    text = response.text.strip()


    # Убираем markdown JSON если Gemini его добавил
    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```",
        "",
        text
    )

    text = re.sub(
        r"```$",
        "",
        text
    )

    text = text.strip()


    try:

        result = json.loads(text)

    except json.JSONDecodeError:

        raise RuntimeError(
            "❌ AI returned invalid JSON:\n"
            + text
        )


    index = result.get("index")

    if not isinstance(
        index,
        int
    ):
        raise RuntimeError(
            "❌ AI returned invalid topic index"
        )


    if index < 1 or index > len(trends):

        raise RuntimeError(
            "❌ AI returned topic index outside available range"
        )


    selected = trends[index - 1].copy()


    selected["ai_reason"] = result.get(
        "reason",
        ""
    )

    selected["viral_score"] = result.get(
        "viral_score",
        0
    )

    selected["hook_score"] = result.get(
        "hook_score",
        0
    )

    selected["curiosity_score"] = result.get(
        "curiosity_score",
        0
    )

    selected["global_score"] = result.get(
        "global_score",
        0
    )

    selected["final_score"] = result.get(
        "final_score",
        0
    )


    return selected


# =========================================================
# MAIN SELECTOR
# =========================================================

def select_topic(
    trends: List[Dict]
) -> Dict:

    print()
    print("=" * 32)
    print("🎯 AI TOPIC SELECTOR")
    print("=" * 32)


    print(
        f"📊 Input trends: {len(trends)}"
    )


    candidates = prepare_topics(
        trends
    )


    print(
        f"🧹 After duplicate filter: {len(candidates)}"
    )


    if not candidates:

        raise RuntimeError(
            "❌ No new topics available"
        )


    selected = select_with_ai(
        candidates
    )


    print()
    print(
        "🏆 SELECTED TOPIC"
    )

    print(
        f"🔥 {selected.get('topic')}"
    )

    print(
        f"📈 Trend score: "
        f"{selected.get('score', 0)}"
    )

    print(
        f"🧠 AI score: "
        f"{selected.get('final_score', 0)}"
    )

    print(
        f"🎣 Hook score: "
        f"{selected.get('hook_score', 0)}"
    )

    print(
        f"🌎 Global score: "
        f"{selected.get('global_score', 0)}"
    )

    print(
        f"💡 Reason: "
        f"{selected.get('ai_reason', '')}"
    )


    return selected


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    test_topics = [

        {
            "topic": "Why do humans see faces in random objects?",
            "source": "Google",
            "score": 92
        },

        {
            "topic": "Scientists discover a strange behavior of time",
            "source": "YouTube",
            "score": 88
        },

        {
            "topic": "The psychological trick your brain uses every day",
            "source": "Google",
            "score": 85
        }

    ]


    selected = select_topic(
        test_topics
    )


    print()
    print(
        json.dumps(
            selected,
            ensure_ascii=False,
            indent=2
        )
    )
