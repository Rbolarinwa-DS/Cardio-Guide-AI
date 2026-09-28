from query_engine.normalizer import normalize_with_metadata


test_questions = [
    # Basic natural language
    "WHAT is hypertension??",
    "what's high blood pressure",
    "Can u tell me what high BP is?",
    "  Explain   hypertension   ",
    "I'm new to this, what's hypertension?",

    # Severe unseen misspellings / compressed text
    "wht r signs of hart failur",
    "my heart jus dey race for no reason",
    "i dey get dis weird beatin for chest",
    "my chest dey somehow nd i dey sweat",

    # Nigerian English / Pidgin-influenced phrasing
    "my mum dey feel weak nd her bp don high wat shld we do",
    "my papa chest dey press am since mornin",
    "can high bp make pesin eye dey blur",
    "she no fit breath well and her chest dey tight",
    "bp don dey 160 ova 100 lately wetin fit cause am",
    "my bp dey high small small abi",

    # Abbreviations / texting
    "doc said my chol is high wat does dat mean",
    "wat can make sum1 leg swellin wit heart problm",
    "xq my heart dey pound when i climb stairs",

    # Mixed corruption
    "my ma is dwn nd she say she had hih Bp wat shuld i do",

    # Deliberately unknown / ambiguous language
    "zzqplk my heart dey foo bar",
]


for i, question in enumerate(test_questions, 1):

    print("\n" + "=" * 80)
    print(f"TEST {i}")

    print("Original :")
    print(question)

    try:
        result = normalize_with_metadata(question)

        print("\nNormalized:")
        print(result.normalized)

        print("\nChanged   :", result.changed)
        print("Method    :", result.method)
        print("Confidence:", result.confidence)
        print("Ambiguity :", result.ambiguity)

        if result.changes:
            print("Changes   :", result.changes)

    except Exception as e:
        print("\nERROR:")
        print(repr(e))