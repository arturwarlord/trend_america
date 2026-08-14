import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import re
import html


# =========================================================
# SETTINGS
# =========================================================

MAX_RESULTS = 8

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0 Safari/537.36"
)


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):
    """
    Cleans HTML entities and unnecessary whitespace.
    """

    if not text:
        return ""

    text = html.unescape(
        str(text)
    )

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# FETCH URL
# =========================================================

def fetch_url(url):
    """
    Download URL using standard Python library.
    """

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            data = response.read()

            return data.decode(
                "utf-8",
                errors="ignore"
            )

    except Exception as error:

        print(
            f"⚠️ Search request failed: "
            f"{error}"
        )

        return ""


# =========================================================
# GOOGLE NEWS RSS
# =========================================================

def search_google_news(
    query,
    max_results=MAX_RESULTS
):
    """
    Searches Google News using RSS.

    No API key required.
    """

    if not query:
        return []

    encoded_query = urllib.parse.quote(
        query
    )

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}"
        "&hl=en-US"
        "&gl=US"
        "&ceid=US:en"
    )

    xml_text = fetch_url(
        url
    )

    if not xml_text:

        return []

    results = []

    try:

        root = ET.fromstring(
            xml_text
        )

    except Exception as error:

        print(
            f"⚠️ RSS parse error: "
            f"{error}"
        )

        return []

    for item in root.findall(
        ".//item"
    ):

        title_node = item.find(
            "title"
        )

        link_node = item.find(
            "link"
        )

        description_node = item.find(
            "description"
        )

        pub_date_node = item.find(
            "pubDate"
        )

        source_node = item.find(
            "source"
        )

        title = ""

        link = ""

        description = ""

        published = ""

        source = ""

        if title_node is not None:

            title = clean_text(
                title_node.text
            )

        if link_node is not None:

            link = clean_text(
                link_node.text
            )

        if description_node is not None:

            description = clean_text(
                description_node.text
            )

        if pub_date_node is not None:

            published = clean_text(
                pub_date_node.text
            )

        if source_node is not None:

            source = clean_text(
                source_node.text
            )

        if not title:

            continue

        results.append({

            "title": title,

            "description": description,

            "source": source,

            "published": published,

            "url": link

        })

        if len(results) >= max_results:

            break

    return results


# =========================================================
# GOOGLE NEWS MULTI-QUERY SEARCH
# =========================================================

def search_topic(
    topic,
    max_results=MAX_RESULTS
):
    """
    Search one topic using several query variations.

    The goal is to collect enough independent
    information for the researcher.
    """

    if not topic:

        return []

    topic = str(
        topic
    ).strip()

    if not topic:

        return []

    print()
    print(
        f"🔎 Research search: {topic}"
    )

    queries = [

        topic,

        f"{topic} news",

        f"{topic} latest",

        f"{topic} facts",

    ]

    all_results = []

    seen_urls = set()

    seen_titles = set()

    for query in queries:

        print(
            f"   🔍 {query}"
        )

        results = search_google_news(
            query,
            max_results=max_results
        )

        for result in results:

            url = result.get(
                "url",
                ""
            ).strip()

            title = result.get(
                "title",
                ""
            ).strip().lower()

            # -----------------------------------------
            # Remove duplicates
            # -----------------------------------------

            if url and url in seen_urls:

                continue

            if title and title in seen_titles:

                continue

            if url:

                seen_urls.add(
                    url
                )

            if title:

                seen_titles.add(
                    title
                )

            all_results.append(
                result
            )

    # ---------------------------------------------
    # Limit final results
    # ---------------------------------------------

    all_results = all_results[
        :max_results
    ]

    print(
        f"   ✅ Sources found: "
        f"{len(all_results)}"
    )

    return all_results


# =========================================================
# FORMAT SOURCES FOR AI
# =========================================================

def format_sources(
    sources
):
    """
    Converts search results into a compact
    text block for Gemini.
    """

    if not sources:

        return "NO SOURCES FOUND."

    blocks = []

    for index, source in enumerate(
        sources,
        start=1
    ):

        title = source.get(
            "title",
            ""
        )

        description = source.get(
            "description",
            ""
        )

        publisher = source.get(
            "source",
            ""
        )

        published = source.get(
            "published",
            ""
        )

        url = source.get(
            "url",
            ""
        )

        block = (
            f"SOURCE {index}\n"
            f"Title: {title}\n"
            f"Publisher: {publisher}\n"
            f"Published: {published}\n"
            f"Description: {description}\n"
            f"URL: {url}"
        )

        blocks.append(
            block
        )

    return "\n\n".join(
        blocks
    )
