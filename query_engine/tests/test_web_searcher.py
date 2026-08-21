from query_engine.web_searcher import WebSearcher
from query_engine.research_query_builder import ResearchQuery


searcher = WebSearcher()


queries = [
    ResearchQuery(
        angle="definition",
        query="What is hypertension?",
    ),
    ResearchQuery(
        angle="symptoms",
        query="What are the symptoms of hypertension?",
    ),
    ResearchQuery(
        angle="causes",
        query="What causes hypertension?",
    ),
    ResearchQuery(
        angle="risk factors",
        query="What are the risk factors for hypertension?",
    ),
    ResearchQuery(
        angle="diagnosis",
        query="How is hypertension diagnosed?",
    ),
    ResearchQuery(
        angle="complications",
        query="What are the complications of hypertension?",
    ),
    ResearchQuery(
        angle="prevention",
        query="How can hypertension be prevented?",
    ),
    ResearchQuery(
        angle="management and treatment",
        query="How is hypertension treated?",
    ),
    ResearchQuery(
        angle="types",
        query="What are the types of hypertension?",
    ),
    ResearchQuery(
        angle="monitoring",
        query="How should hypertension be monitored?",
    ),
    ResearchQuery(
        angle="lifestyle",
        query="What lifestyle changes help with hypertension?",
    ),
    ResearchQuery(
        angle="when to seek medical care",
        query="When should someone seek medical care for hypertension?",
    ),
]


response = searcher.search(
    queries=queries,
    max_sources=6,
)


print("=" * 70)
print("CARDIOGUIDE MULTI-ANGLE SOURCE RETRIEVAL TEST")
print("=" * 70)

print(
    f"\nRESEARCH QUERIES: {len(queries)}"
)

print(
    f"SOURCES RETURNED: {len(response)}"
)


# --------------------------------------------------
# APPROVED DOMAINS
# --------------------------------------------------

approved_domains = {
    "who.int",
    "www.who.int",
    "mayoclinic.org",
    "www.mayoclinic.org",
    "heart.org",
    "www.heart.org",
}


returned_domains = {
    result.result.get("url", "")
    for result in response
}


successful_domains = set()

for result in response:

    url = result.result.get(
        "url",
        "",
    )

    if not url:
        continue

    for domain in approved_domains:

        if domain in url:
            successful_domains.add(domain)


print("\nSUCCESSFUL DOMAINS:")

for domain in sorted(
    successful_domains
):
    print(f"- {domain}")


# --------------------------------------------------
# APPROVED SOURCE ASSERTION
# --------------------------------------------------

returned_approved_domains = set()

for result in response:

    url = result.result.get(
        "url",
        "",
    ).lower()

    if "who.int" in url:
        returned_approved_domains.add(
            "who.int"
        )

    elif "mayoclinic.org" in url:
        returned_approved_domains.add(
            "mayoclinic.org"
        )

    elif "heart.org" in url:
        returned_approved_domains.add(
            "heart.org"
        )


assert returned_approved_domains

print(
    "\nAPPROVED DOMAINS FOUND: PASS"
)


# --------------------------------------------------
# RESULT STRUCTURE
# --------------------------------------------------

for result in response:

    assert result.angle is not None
    assert result.query
    assert isinstance(
        result.result,
        dict,
    )

    assert result.result.get(
        "url"
    )

    assert result.result.get(
        "title"
    )

    assert result.result.get(
        "content"
    )


print(
    "RESULT STRUCTURE: PASS"
)


# --------------------------------------------------
# DUPLICATE URL CHECK
# --------------------------------------------------

urls = [
    result.result.get(
        "url",
        "",
    )
    for result in response
]

assert len(urls) == len(
    set(urls)
)

print(
    "DUPLICATE URL CHECK: PASS"
)


# --------------------------------------------------
# MAX RETRIEVAL LIMIT
# --------------------------------------------------

assert len(response) <= 6

print(
    "MAX RETRIEVAL LIMIT: PASS"
)


# --------------------------------------------------
# PRINT SOURCES
# --------------------------------------------------

print(
    "\nRETRIEVED SOURCES:"
)

for index, result in enumerate(
    response,
    start=1,
):

    data = result.result

    print(
        f"\n{index}. "
        f"{data.get('title', 'Untitled')}"
    )

    print(
        f"   ANGLE: {result.angle}"
    )

    print(
        f"   QUERY: {result.query}"
    )

    print(
        f"   URL: {data.get('url', '')}"
    )


print("\n" + "=" * 70)
print("STATUS: PASS")
print("=" * 70)