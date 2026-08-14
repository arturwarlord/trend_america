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

AI_INPUT_LIMIT = 50


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

    # -----------------------------------------------------
    # Analyzer already returns TOP 50 in V8
    # -----------------------------------------------------

    candidates = analyzed_trends[
        :AI_INPUT_LIMIT
    ]

    topics = []

    for trend in candidates:

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

        topics.append(
            topic
        )

    print(
        f"📥 Original topics: "
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
    #
    # IMPORTANT:
    #
    # DO NOT check score >= 60 here.
    #
    # judge_topics() already calculates the score
    # and controls is_good_for_shorts.
    #
    # This prevents double filtering.
    # =====================================================

    approved_trends = [

        trend

        for trend in judged_trends

        if trend.get(
            "is_good_for_shorts",
            False
        )

    ]

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
    # LIMIT
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
            "💡 Consider increasing the number "
            "of input trends."
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
