from trends.collector import collect_trends

from trends.storage import save_trends

from trends.analyzer import (
    analyze_trends,
    save_top_trends
)

from ai.trend_judge import (
    judge_topics
)

from ai.topic_selector import (
    select_topic
)


# =========================================================
# SETTINGS
# =========================================================

TARGET_TOPICS = 10

# Сколько кандидатов отдаём AI Judge
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
    # DISPLAY AI APPROVED
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
    # SAVE APPROVED TOPICS
    # =====================================================

    save_top_trends(
        approved_trends
    )

    # =====================================================
    # FINAL TOPIC SELECTION
    # =====================================================

    if not approved_trends:

        print()
        print(
            "❌ No approved topics available "
            "for final selection."
        )

        print()

        print(
            "================================"
        )

        print(
            "⚠️ Global trend pipeline finished "
            "without a final topic"
        )

        print(
            "================================"
        )

        return

    print()
    print("================================")
    print("🎯 FINAL TOPIC SELECTION")
    print("================================")
    print()

    try:

        selected_topic = select_topic(
            approved_trends
        )

    except Exception as e:

        print()
        print(
            "❌ Topic Selector failed:"
        )

        print(
            f"   {e}"
        )

        print()

        return

    # =====================================================
    # CHECK RESULT
    # =====================================================

    if not selected_topic:

        print(
            "❌ Topic Selector returned no topic"
        )

        return

    # =====================================================
    # DISPLAY FINAL TOPIC
    # =====================================================

    print()
    print("================================")
    print("🏆 FINAL SELECTED TOPIC")
    print("================================")
    print()

    print(
        f"🔥 Topic: "
        f"{selected_topic.get('topic', '')}"
    )

    print(
        f"📊 Judge Score: "
        f"{selected_topic.get('judge_score', 0):.0f}/100"
    )

    print(
        f"🧠 Final AI Score: "
        f"{selected_topic.get('final_score', 0):.0f}/100"
    )

    print(
        f"🎣 Hook Score: "
        f"{selected_topic.get('hook_score', 0):.0f}/100"
    )

    print(
        f"❓ Curiosity Score: "
        f"{selected_topic.get('curiosity_score', 0):.0f}/100"
    )

    print(
        f"🌎 Global Score: "
        f"{selected_topic.get('global_score', 0):.0f}/100"
    )

    print(
        f"📖 Story Score: "
        f"{selected_topic.get('story_score', 0):.0f}/100"
    )

    print(
        f"🎬 Visual Score: "
        f"{selected_topic.get('visual_score', 0):.0f}/100"
    )

    print(
        f"💡 Reason: "
        f"{selected_topic.get('reason', '')}"
    )

    print()

    print(
        "🎣 Suggested Hook:"
    )

    print(
        f"   {selected_topic.get('suggested_hook', '')}"
    )

    print()

    # =====================================================
    # FINAL STATUS
    # =====================================================

    print("================================")
    print("✅ Global trend pipeline completed")
    print("================================")
    print()

    print(
        f"📊 Analyzed trends: "
        f"{len(analyzed_trends)}"
    )

    print(
        f"🤖 AI Judge candidates: "
        f"{len(topics)}"
    )

    print(
        f"🔥 Approved topics: "
        f"{len(approved_trends)}"
    )

    print(
        f"🏆 Selected topic: "
        f"{selected_topic.get('topic', '')}"
    )

    print()

    # =====================================================
    # TARGET STATUS
    # =====================================================

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
