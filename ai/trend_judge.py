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
# SYSTEM PROMPT V3
# ==========================================

SYSTEM_PROMPT = """
You are an expert global YouTube Shorts trend analyst.

Your job is to evaluate whether a trending topic can be turned
into an ORIGINAL English YouTube Short for a GLOBAL audience.

The goal is NOT to simply find popular searches.

The goal is to find topics that contain a REAL, SPECIFIC,
INTERESTING STORY or FACT that can become a compelling
30-60 second Short.

==========================================
GOOD TOPICS
==========================================

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
- unexpected scientific discoveries

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
IMPORTANT: DO NOT INVENT INFORMATION
==========================================

Judge ONLY what the topic itself reasonably supports.

Do NOT assume missing details.

Do NOT transform a vague keyword into a specific event.

For example:

"Army Sir Split The Village into Half.."

may sound interesting, but if the exact event,
location, people and context are unclear,
reduce factual confidence.

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

A strong Short topic should allow a structure such as:

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

We need the underlying real-world story,
not a reproduction of the original content.

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

score: 0-100

Use this approximate weighting:

global_interest       15%
viral_potential       15%
english_audience      10%
story_potential       20%
specificity           15%
factual_confidence    15%
originality           10%

==========================================
DECISION RULES
==========================================

is_good_for_shorts = TRUE only when:

- the topic is suitable for a global English audience
- it has a clear story/fact
- it is specific enough
- it can be turned into an original Short
- it does not require copying the original content
- factual confidence is reasonably high

If the topic is only a keyword or generic search query,
reject it.

If the topic is interesting but too vague,
reject it.

==========================================
CATEGORY
==========================================

Use one of:

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

Do not use markdown.

Do not use ```.

Do not add explanations outside JSON.
"""


# ==========================================
# CLEAN JSON
# ==========================================

def clean_json(text):

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

    text = text.strip()

    return text


# ==========================================
# DEFAULT RESULT
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
}}
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        text = response.text

        if not text:
            return failed_result(topic)

        text = clean_json(text)

        result = json.loads(text)

        # ==================================
        # VALIDATE
        # ==================================

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
                result[field] = float(
                    result.get(field, 0)
                )

            except Exception:
                result[field] = 0

        # ==================================
        # HARD SAFETY RULES
        # ==================================

        if result["specificity"] < 5:
            result["is_good_for_shorts"] = False

        if result["factual_confidence"] < 5:
            result["is_good_for_shorts"] = False

        if result["story_potential"] < 5:
            result["is_good_for_shorts"] = False

        if result["score"] < 60:
            result["is_good_for_shorts"] = False

        return result

    except Exception as error:

        print(
            f"⚠️ AI Judge error: {error}"
        )

        return failed_result(topic)


# ==========================================
# JUDGE MULTIPLE TOPICS
# ==========================================

def judge_topics(topics):

    print()
    print("================================")
    print("🤖 AI TREND JUDGE V3")
    print("================================")

    print(
        f"📊 Topics for AI Judge: {len(topics)}"
    )

    print()

    results = []

    for index, topic in enumerate(
        topics,
        start=1
    ):

        print(
            f"🤖 [{index}/{len(topics)}] "
            f"{topic}"
        )

        result = judge_topic(topic)

        results.append(result)

        status = (
            "✅ APPROVED"
            if result.get(
                "is_good_for_shorts",
                False
            )
            else "❌ REJECTED"
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

    # ==========================================
    # SORT
    # ==========================================

    results.sort(
        key=lambda item: item.get(
            "score",
            0
        ),
        reverse=True
    )

    return results
