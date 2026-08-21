# query_engine/tests/test_source_processor.py

from query_engine.source_processor import SourceProcessor
from query_engine.web_searcher import SearchResult


processor = SourceProcessor()


results = [
    SearchResult(
        angle="definition",
        query="What is hypertension?",
        result={
            "title": "WHO Hypertension",
            "url": "https://www.who.int/health-topics/hypertension",
            "content": """
            Hypertension is high blood pressure.

            © WHO Credits

            Privacy Policy

            Hypertension increases cardiovascular risk.
            """,
        },
    ),

    SearchResult(
        angle="symptoms",
        query="What are the symptoms of hypertension?",
        result={
            "title": "Mayo Clinic Hypertension",
            "url": "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure",
            "content": """
            Many people with hypertension have no symptoms.

            Read more

            Regular medical evaluation is important.
            """,
        },
    ),

    SearchResult(
        angle="risk factors",
        query="What are the risk factors for hypertension?",
        result={
            "title": "AHA Hypertension",
            "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
            "content": """
            Risk factors include several lifestyle and health factors.

            Subscribe

            Regular monitoring can be useful.
            """,
        },
    ),

    SearchResult(
        angle="definition",
        query="What is hypertension?",
        result={
            "title": "Bad Source",
            "url": "https://example.com/hypertension",
            "content": "This source should be rejected.",
        },
    ),
]


processed = processor.process(results)


print("=" * 70)
print("CARDIOGUIDE SOURCE PROCESSOR TEST")
print("=" * 70)

print(f"\nINPUT RESULTS: {len(results)}")
print(f"PROCESSED SOURCES: {len(processed)}")

print("\nPROCESSED SOURCES:")

for index, source in enumerate(
    processed,
    start=1,
):

    print(f"\n{index}. {source.title}")
    print(f"   DOMAIN: {source.domain}")
    print(f"   ANGLE: {source.angle}")
    print(f"   QUERY: {source.query}")
    print(f"   URL: {source.url}")
    print(f"   CONTENT: {source.content}")


print("\n" + "=" * 70)


# --------------------------------------------------
# Assertions
# --------------------------------------------------

assert len(processed) == 3


domains = {
    source.domain
    for source in processed
}


assert domains == {
    "who.int",
    "mayoclinic.org",
    "heart.org",
}


# Unapproved source must be rejected.
assert "example.com" not in domains


# Research metadata must survive processing.
angles = {
    source.angle
    for source in processed
}


assert angles == {
    "definition",
    "symptoms",
    "risk factors",
}


for source in processed:

    assert source.title
    assert source.url
    assert source.domain
    assert source.content
    assert source.angle
    assert source.query


# Junk content must be removed.
for source in processed:

    content = source.content.lower()

    assert "privacy policy" not in content
    assert "read more" not in content
    assert "subscribe" not in content
    assert "credits" not in content
    assert "©" not in content


# Useful content must remain.
all_content = " ".join(
    source.content.lower()
    for source in processed
)

assert "hypertension" in all_content
assert "risk factors" in all_content
assert "no symptoms" in all_content


print("STATUS: PASS")