from query_engine.web_searcher import WebSearcher


class MockWebSearcher(WebSearcher):

    def __init__(self, working_domains):
        self.working_domains = working_domains

    def search(self, queries, max_sources=3):
        all_results = []

        fake_results = {
            "who.int": {
                "title": "WHO Hypertension",
                "url": "https://www.who.int/health-topics/hypertension",
                "content": "WHO hypertension evidence."
            },
            "mayoclinic.org": {
                "title": "Mayo Clinic Hypertension",
                "url": "https://www.mayoclinic.org/hypertension",
                "content": "Mayo Clinic hypertension evidence."
            },
            "heart.org": {
                "title": "AHA Hypertension",
                "url": "https://www.heart.org/hypertension",
                "content": "AHA hypertension evidence."
            }
        }

        for domain in self.working_domains:
            all_results.append(fake_results[domain])

        return all_results[:max_sources]


queries = [
    "What is hypertension?",
    "What is hypertension? medical evidence",
    "What is hypertension? patient education"
]


test_cases = [
    (
        "3/3 SOURCES",
        ["who.int", "mayoclinic.org", "heart.org"]
    ),
    (
        "2/3 SOURCES",
        ["who.int", "mayoclinic.org"]
    ),
    (
        "1/3 SOURCES",
        ["who.int"]
    ),
    (
        "0/3 SOURCES",
        []
    )
]


for name, working_domains in test_cases:

    searcher = MockWebSearcher(working_domains)

    results = searcher.search(queries)

    print("=" * 70)
    print(name)
    print(f"SOURCES RETURNED: {len(results)}")

    for source in results:
        print(f"- {source['title']}")

    if len(results) == len(working_domains):
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")

    print()