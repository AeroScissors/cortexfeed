# File: cortexfeed/tests/intelligence/test_intent_classifier.py

from cortexfeed.intelligence.intent_classifier import (
    IntentClassifier,
)


def test_detects_symbol_lookup():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "Where is login handled?",
    )

    assert intent.intent == "symbol_lookup"
    assert intent.confidence > 0.5


def test_detects_symbol_lookup_implemented():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "Find where create_user is implemented",
    )

    assert intent.intent == "symbol_lookup"


def test_detects_bug_investigation():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "Login endpoint returns 500 error",
    )

    assert intent.intent == "bug_investigation"
    assert intent.confidence > 0.8


def test_detects_bug_investigation_for_exception():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "Promise sync fails with exception",
    )

    assert intent.intent == "bug_investigation"


def test_extracts_route():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "POST /login returns 500",
    )

    assert "POST:/login" in intent.routes


def test_extracts_multiple_routes():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "Compare GET /users and POST /users",
    )

    assert "GET:/users" in intent.routes
    assert "POST:/users" in intent.routes


def test_general_search_fallback():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "authentication system",
    )

    assert intent.intent == "general_search"


def test_preserves_raw_query():
    classifier = IntentClassifier()

    query = "Where is login handled?"

    intent = classifier.classify(
        query,
    )

    assert intent.raw_query == query


def test_route_case_insensitive():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "post /login returns 500",
    )

    assert "POST:/login" in intent.routes


def test_empty_query_returns_general_search():
    classifier = IntentClassifier()

    intent = classifier.classify(
        "",
    )

    assert intent.intent == "general_search"