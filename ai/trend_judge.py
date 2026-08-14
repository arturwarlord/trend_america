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
# SYSTEM PROMPT V4
# ==========================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate trending topics and determine whether
each topic can become an ORIGINAL English YouTube Short for
a GLOBAL audience.

The goal is NOT simply to find popular searches.

The goal is to find topics that contain a REAL, SPECIFIC,
INTERESTING STORY or FACT that can become a compelling
30-60 second informational Short.

==========================================
GOOD TOPICS
==========================================

Prefer:

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
BAD TOPICS
==========================================

Reject:

- video games
- gaming
- esports
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
- random people's names
- random search queries
- generic product searches
- local events
- fan content
- reaction videos
- livestreams
- gameplay
- fictional characters
- memes without a story

==========================================
VERY IMPORTANT
==========================================

A topic must contain enough SPECIFIC INFORMATION
to build a factual story.

Examples:

"google pixel"
= BAD

Reason:
Too broad. It is only a product/search term.

"Google Pixel introduces satellite messaging"
= GOOD

Reason:
Specific technological development with a clear story.

"ticketmaster"
= BAD

Reason:
Generic company/search query.

"Ticketmaster changes its pricing system"
= GOOD

Reason:
Specific business development.

"avgo stock"
= BAD

Reason:
Generic financial search query.

"Broadcom's AI chip business drives unexpected growth"
= GOOD

Reason:
Specific business/technology story.

==========================================
DO NOT INVENT INFORMATION
==========================================

Judge ONLY what the topic itself reasonably supports.

Do NOT assume missing details.

Do NOT transform a vague keyword into a specific event.

For example:

"Army Sir Split The Village into Half.."

may sound interesting, but if the exact event,
location, people and context are unclear,
reduce factual confidence and specificity.

A potentially interesting topic is NOT automatically
a good topic.

==========================================
GLOBAL AUDIENCE
==========================================

The topic should work for an English-speaking global audience.

Prefer topics that can be understood without:

- local political knowledge
- local language
- knowledge of a specific influencer
- knowledge of a specific game
- knowledge of a specific TV show
- knowledge of a specific music artist

==========================================
STORY POTENTIAL
==========================================

A strong Short topic should allow:

HOOK
→ surprising fact
→ explanation
→ escalation
→ payoff

The viewer should naturally want to know:

"What happened?"
"Why?"
"How?"
"What does this mean?"

==========================================
ORIGINALITY
==========================================

We are creating an ORIGINAL educational/informational Short.

Do not approve topics simply because the original video
has many views.

A viral music video is still BAD.

A viral gaming video is still BAD.

A viral movie trailer is still BAD.

A viral livestream is still BAD.

We need the underlying real-world story,
not a reproduction of the original content.

==========================================
SCORING
==========================================

Score every topic using:

global_interest: 0-10
viral_potential: 0-10
english_audience: 0-10
story_potential: 0-10
specificity: 0-10
factual_confidence: 0-10
originality: 0-10

Calculate:

global_interest       15%
viral_potential       15%
english_audience      10%
story_potential       20%
specificity           15%
factual_confidence    15%
originality           10%

Convert the result to score 0-100.

==========================================
DECISION RULES
==========================================

is_good_for_shorts = TRUE only when:

- the topic is suitable for a global English audience
- it has a clear story or factual angle
- it is specific enough
- it can be turned into an original Short
- it does not require copying the original content
- factual confidence is reasonably high

If the topic is only a keyword or generic search query,
reject it.

If the topic is interesting but too vague,
reject it.

Hard reject if:

specificity < 5

OR

factual_confidence < 5

OR

story_potential < 5

OR

score < 60

==========================================
CATEGORY
==========================================

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

==========================================
OUTPUT
==========================================

You will receive MULTIPLE topics.

Analyze ALL topics.

Return ONLY a valid JSON ARRAY.

Do not use markdown.

Do not use ```.

Do not add explanations outside JSON.

Every array element must have exactly this structure:

{
    "topic": "original topic",
    "is_good_for_shorts": false,
    "category": "other",

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

IMPORTANT:

Return one result for EVERY input topic.

Do not omit topics.

Keep the original topic text exactly as provided.
"""


# ==========================================
# CLEAN JSON
# ==========================================

def clean_json(text):

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    return text


# ==========================================
# DEFAULT RESULT
# ==========================================

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


# ==========================================
# NORMALIZE RESULT
# ==========================================

def normalize_result(
    result,
    topic
):

    if not isinstance(
        result,
        dict
    ):

        return failed_result(
            topic
        )

    # Always preserve original topic
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
                result.get(
                    field,
                    0
                )
            )

            # Keep values in valid range
            if field == "score":

                value = max(
                    0,
                    min(
                        100,
                        value
                    )
                )

            else:

                value = max(
                    0,
                    min(
                        10,
                        value
                    )
                )

            result[field] = value

        except Exception:

            result[field] = 0

    # ======================================
    # CATEGORY
    # ======================================

    allowed_categories = {

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
        "mystery",
        "other"

    }

    category = result.get(
        "category",
        "other"
    )

    if category not in allowed_categories:

        category = "other"

    result["category"] = category

    # ======================================
    # BOOLEAN
    # ======================================

    result["is_good_for_shorts"] = bool(
        result.get(
            "is_good_for_shorts",
            False
        )
    )

    # ======================================
    # HARD SAFETY RULES
    # ======================================

    if result["specificity"] < 5:

        result["is_good_for_shorts"] = False

    if result["factual_confidence"] < 5:

        result["is_good_for_shorts"] = False

    if result["story_potential"] < 5:

        result["is_good_for_shorts"] = False

    if result["score"] < 60:

        result["is_good_for_shorts"] = False

    # ======================================
    # REASON
    # ======================================

    if not result.get("reason"):

        result["reason"] = ""

    return result


# ==========================================
# PARSE AI RESPONSE
# ==========================================

def parse_response(
    text,
    topics
):

    text = clean_json(
        text
    )

    if not text:

        raise ValueError(
            "Gemini returned empty response"
        )

    try:

        data = json.loads(
            text
        )

    except json.JSONDecodeError:

        # ==================================
        # TRY TO EXTRACT JSON ARRAY
        # ==================================

        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1:

            raise ValueError(
                "Gemini response does not contain JSON array"
            )

        data = json.loads(
            text[
                start:end + 1
            ]
        )

    if not isinstance(
        data,
        list
    ):

        raise ValueError(
            "Gemini response is not a JSON array"
        )

    # ==========================================
    # MAP RESULTS BY TOPIC
    # ==========================================

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
            str(topic).strip()
        ] = item

    # ==========================================
    # BUILD RESULTS IN ORIGINAL ORDER
    # ==========================================

    results = []

    for topic in topics:

        item = result_map.get(
            str(topic).strip()
        )

        if item is None:

            # Try case-insensitive lookup
            item = None

            target = str(
                topic
            ).strip().lower()

            for key, value in result_map.items():

                if key.lower() == target:

                    item = value

                    break

        if item is None:

            results.append(
                failed_result(
                    topic,
                    "AI did not return a result for this topic"
                )
            )

        else:

            results.append(
                normalize_result(
                    item,
                    topic
                )
            )

    return results


# ==========================================
# JUDGE ALL TOPICS
# ==========================================

def judge_topics(
    topics
):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE V4")
    print("================================")

    if not topics:

        print(
            "❌ No topics for AI Judge"
        )

        return []

    # ==========================================
    # CLEAN TOPICS
    # ==========================================

    clean_topics = []

    seen = set()

    for topic in topics:

        if not isinstance(
            topic,
            str
        ):

            continue

        topic = topic.strip()

        if not topic:

            continue

        key = topic.lower()

        if key in seen:

            continue

        seen.add(key)

        clean_topics.append(
            topic
        )

    print(
        f"📊 Topics for AI Judge: "
        f"{len(clean_topics)}"
    )

    print()

    # ==========================================
    # PRINT TOPICS
    # ==========================================

    for index, topic in enumerate(
        clean_topics,
        start=1
    ):

        print(
            f"📥 [{index}/{len(clean_topics)}] "
            f"{topic}"
        )

    print()

    # ==========================================
    # BUILD ONE BATCH REQUEST
    # ==========================================

    topics_json = json.dumps(
        clean_topics,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
{SYSTEM_PROMPT}

==========================================
TOPICS TO ANALYZE
==========================================

Analyze ALL of the following topics:

{topics_json}

==========================================
FINAL REQUIREMENT
==========================================

Return exactly one JSON object for every topic.

Return ONLY the JSON array.
"""

    # ==========================================
    # RETRY SETTINGS
    # ==========================================

    max_attempts = 3

    retry_delay = 35

    response = None

    # ==========================================
    # ONE GEMINI REQUEST
    # ==========================================

    for attempt in range(
        1,
        max_attempts + 1
    ):

        print(
            f"🚀 Sending all "
            f"{len(clean_topics)} topics "
            f"in ONE Gemini request..."
        )

        print(
            f"   Attempt {attempt}/{max_attempts}"
        )

        try:

            response = client.models.generate_content(

                model=MODEL_NAME,

                contents=prompt

            )

            break

        except Exception as error:

            error_text = str(
                error
            )

            print()
            print(
                f"⚠️ Gemini error: "
                f"{error_text}"
            )

            # ==================================
            # RATE LIMIT
            # ==================================

            if (
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED"
                in error_text
            ):

                if attempt < max_attempts:

                    print()
                    print(
                        f"⏳ Rate limit detected."
                    )

                    print(
                        f"⏳ Waiting "
                        f"{retry_delay} seconds..."
                    )

                    time.sleep(
                        retry_delay
                    )

                    continue

            # ==================================
            # OTHER ERROR
            # ==================================

            print(
                "❌ AI Judge request failed"
            )

            return [

                failed_result(
                    topic,
                    "AI Judge request failed"
                )

                for topic in clean_topics

            ]

    # ==========================================
    # NO RESPONSE
    # ==========================================

    if response is None:

        print(
            "❌ Gemini returned no response"
        )

        return [

            failed_result(
                topic,
                "Gemini returned no response"
            )

            for topic in clean_topics

        ]

    # ==========================================
    # RESPONSE TEXT
    # ==========================================

    text = getattr(
        response,
        "text",
        None
    )

    if not text:

        print(
            "❌ Gemini returned empty text"
        )

        return [

            failed_result(
                topic,
                "Gemini returned empty response"
            )

            for topic in clean_topics

        ]

    # ==========================================
    # PARSE
    # ==========================================

    try:

        results = parse_response(
            text,
            clean_topics
        )

    except Exception as error:

        print()
        print(
            f"⚠️ JSON parsing error: "
            f"{error}"
        )

        print()
        print(
            "Gemini raw response:"
        )

        print(
            text[:5000]
        )

        return [

            failed_result(
                topic,
                "Invalid AI JSON response"
            )

            for topic in clean_topics

        ]

    # ==========================================
    # PRINT RESULTS
    # ==========================================

    print()
    print("================================")
    print("📊 AI JUDGE COMPLETE")
    print("================================")

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

        print()

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
            f"   English: "
            f"{result.get('english_audience', 0):.0f}/10"
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
            f"   Originality: "
            f"{result.get('originality', 0):.0f}/10"
        )

        print(
            f"   Reason: "
            f"{result.get('reason', '')}"
        )

    # ==========================================
    # SORT
    # ==========================================

    results.sort(
        key=lambda item:
            item.get(
                "score",
                0
            ),
        reverse=True
    )

    # ==========================================
    # SUMMARY
    # ==========================================

    print()
    print(
        f"📥 Analyzed: "
        f"{len(results)}"
    )

    print(
        f"✅ Approved: "
        f"{approved_count}"
    )

    print(
        f"❌ Rejected: "
        f"{len(results) - approved_count}"
    )

    print()

    return results


# ==========================================
# OPTIONAL: JUDGE ONE TOPIC
# ==========================================

def judge_topic(
    topic
):

    results = judge_topics(
        [topic]
    )

    if results:

        return results[0]

    return failed_result(
        topic
    )
