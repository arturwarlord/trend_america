from trends.collector import collect_trends

from trends.storage import save_trends

from trends.analyzer import (
    analyze_trends,
    save_top_trends
)

from ai.trend_judge import (
    judge_topics
)


# =========================================================
# SETTINGS
# =========================================================

TARGET_TOPICS = 10

# Сколько кандидатов отдаём AI Judge.
#
# Раньше здесь фактически использовалось около 60.
# Теперь даём Judge больше материала.
AI_INPUT_LIMIT = 120


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("🚀 YouTube Global Shorts")
    print()

    # =====================================================
    # COLLECT
    # =====================================================

    trends = collect_trends()

    save_trends(
        trends
    )

    # =====================================================
    # ANALYZE
    # =====================================================

    analyzed_trends = analyze_trends(
        trends
    )

    if not analyzed_trends:

        print(
            "❌ No analyzed trends found"
        )

        save_top_trends([])

        return

    # =====================================================
    # PREPARE AI CANDIDATES
    # =====================================================

    print()
    print("================================")
    print("🤖 PREPARING AI TREND JUDGE")
    print("================================")
    print()

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique_topics = []

    seen_topics = set()

    for trend in analyzed_trends:

        topic = trend.get(
            "topic",
            ""
        )

        if not topic:
            continue

        topic = str(
            topic
        ).strip()

        if not topic:
            continue

        # Case-insensitive deduplication
        topic_key = topic.lower()

        if topic_key in seen_topics:
            continue

        seen_topics.add(
            topic_key
        )

        unique_topics.append(
            topic
        )

    # =====================================================
    # LIMIT AI INPUT
    # =====================================================

    topics = unique_topics[
        :AI_INPUT_LIMIT
    ]

    # =====================================================
    # DISPLAY
    # =====================================================

    print(
        f"📥 Analyzer trends: "
        f"{len(analyzed_trends)}"
    )

    print(
        f"🔗 Unique topics: "
        f"{len(unique_topics)}"
    )

    print(
        f"🧠 Topics sent to AI Judge: "
        f"{len(topics)}"
    )

    print(
        f"🎯 Target approved topics: "
        f"{TARGET_TOPICS}"
    )

    print()

    if not topics:

        print(
            "❌ No trend candidates found"
        )

        save_top_trends([])

        return

    # =====================================================
    # AI JUDGE
    # =====================================================

    judged_trends = judge_topics(
        topics
    )

    if not judged_trends:

        print(
            "❌ AI Judge returned no results"
        )

        save_top_trends([])

        return

    # =====================================================
    # KEEP AI APPROVED
    # =====================================================

    approved_trends = []

    for trend in judged_trends:

        if trend.get(
            "is_good_for_shorts",
            False
        ):

            approved_trends.append(
                trend
            )

    # =====================================================
    # SORT
    # =====================================================

    approved_trends.sort(

        key=lambda item:
            item.get(
                "score",
                0
            ),

        reverse=True

    )

    # =====================================================
    # LIMIT TO TARGET
    # =====================================================

    approved_trends = approved_trends[
        :TARGET_TOPICS
    ]

    # =====================================================
    # DISPLAY
    # =====================================================

    print()
    print("================================")
    print("🔥 AI APPROVED TRENDS")
    print("================================")
    print()

    if not approved_trends:

        print(
            "❌ AI did not approve any topics"
        )

    else:

        for index, trend in enumerate(
            approved_trends,
            start=1
        ):

            print(
                f"#{index} "
                f"{trend.get('topic', '')}"
            )

            print(
                f"   AI Score: "
                f"{trend.get('score', 0):.0f}/100"
            )

            print(
                f"   Category: "
                f"{trend.get('category', 'unknown')}"
            )

            print(
                f"   Global Interest: "
                f"{trend.get('global_interest', 0):.0f}/10"
            )

            print(
                f"   Viral Potential: "
                f"{trend.get('viral_potential', 0):.0f}/10"
            )

            print(
                f"   English Audience: "
                f"{trend.get('english_audience', 0):.0f}/10"
            )

            print(
                f"   Story Potential: "
                f"{trend.get('story_potential', 0):.0f}/10"
            )

            print(
                f"   Specificity: "
                f"{trend.get('specificity', 0):.0f}/10"
            )

            print(
                f"   Facts: "
                f"{trend.get('factual_confidence', 0):.0f}/10"
            )

            print(
                f"   Originality: "
                f"{trend.get('originality', 0):.0f}/10"
            )

            print(
                f"   Reason: "
                f"{trend.get('reason', '')}"
            )

            print()

    # =====================================================
    # SAVE
    # =====================================================

    save_top_trends(
        approved_trends
    )

    # =====================================================
    # FINAL STATUS
    # =====================================================

    print()
    print("================================")
    print("✅ Global trend pipeline completed")
    print("================================")
    print()

    print(
        f"🎯 Final topics: "
        f"{len(approved_trends)}"
    )

    print()

    if len(approved_trends) < TARGET_TOPICS:

        print(
            f"⚠️ Only "
            f"{len(approved_trends)} "
            f"topics approved."
        )

        print(
            f"🎯 Target: "
            f"{TARGET_TOPICS}"
        )

        print(
            "💡 AI Judge needs to evaluate "
            "more candidates."
        )

    else:

        print(
            f"✅ Target reached: "
            f"{len(approved_trends)}/"
            f"{TARGET_TOPICS}"
        )

    print()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()
