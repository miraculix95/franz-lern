"""Static configuration constants for lingua-app.

Everything that used to be top-of-file globals in the legacy Streamlit monolith
lives here. Kept pure (no imports beyond stdlib) so tests stay fast.
"""
from __future__ import annotations

LEVELS: list[str] = ["A1", "A2", "B1", "B2", "C1", "C2"]

NIVEAU_LEVELS: list[str] = [
    "Gossensprache/Kriminelle Sprache",
    "Argot/Vulgär",
    "Umgangssprache",
    "Standardsprache",
    "Gehoben/Vornehm",
    "Hohe Literatur",
    "Technisch",
]

LANGUAGES: list[str] = [
    "französisch",
    "englisch",
    "spanisch",
    "ukrainisch",
    "deutsch",
    "polnisch",
    "griechisch",
    "arabisch",
    "hebräisch",
]

# Right-to-left learning languages — UI wraps task/feedback output in dir=rtl.
RTL_LANGUAGES: set[str] = {"hebräisch", "arabisch"}

# Learning languages written in a non-Latin script: the learner's physical
# keyboard likely can't type them, so the practice area shows an input-help hint
# (OS keyboard shortcut + an online-keyboard fallback for copy-paste).
# Note: orthogonal to RTL — Ukrainian/Greek are LTR but still need their own layout.
INPUT_KEYBOARD_URL: dict[str, str] = {
    "ukrainisch": "https://www.lexilogos.com/keyboard/ukrainian.htm",
    "griechisch": "https://www.lexilogos.com/keyboard/greek_modern.htm",
    "arabisch": "https://www.lexilogos.com/keyboard/arabic.htm",
    "hebräisch": "https://www.lexilogos.com/keyboard/hebrew.htm",
}
NON_LATIN_LANGUAGES: frozenset[str] = frozenset(INPUT_KEYBOARD_URL)

MENTORS: list[str] = [
    "Netter Lehrer",
    "Strenger Lehrer",
    "Dalai Lama",
    "Vitalik Buterin",
    "Elon Musk",
    "Jesus Christus",
    "Chairman Mao",
    "Homer",
    "Konfuzius",
    "Machiavelli",
]

MENTOR_AVATARS: dict[str, str] = {
    "Netter Lehrer": "🎓",
    "Strenger Lehrer": "📏",
    "Dalai Lama": "🧘",
    "Vitalik Buterin": "⛓️",
    "Elon Musk": "🚀",
    "Jesus Christus": "✝️",
    "Chairman Mao": "🌾",
    "Homer": "📜",
    "Konfuzius": "🏯",
    "Machiavelli": "🗡️",
}

MENTOR_QUOTES: dict[str, str] = {
    "Netter Lehrer": "Jeder Fehler ist ein Schritt nach vorne.",
    "Strenger Lehrer": "Präzision ist die Höflichkeit der Könige.",
    "Dalai Lama": "Be kind whenever possible. It is always possible.",
    "Vitalik Buterin": "Decentralization of power; centralization of knowledge.",
    "Elon Musk": "When something is important enough, you do it even if the odds are not in your favor.",
    "Jesus Christus": "Der Buchstabe tötet, der Geist macht lebendig.",
    "Chairman Mao": "Eine Reise von tausend Meilen beginnt mit dem ersten Schritt.",
    "Homer": "Even in sleep, sorrow descends upon our souls.",
    "Konfuzius": "Lernen ohne Nachdenken ist vergeblich; Nachdenken ohne Lernen ist gefährlich.",
    "Machiavelli": "Fortune favors the bold.",
}

THEMES: list[str] = [
    "Urlaub",
    "Schule",
    "Essen",
    "Sport",
    "Kultur",
    "Medien",
    "Raumfahrt",
    "Business",
    "Politik",
]

# Transformation exercise: sentence-rewriting drills. Keys are stable (used by
# the UI + dispatch); the English phrase is injected into the (English) prompt,
# the label is localized per UI language in i18n.TRANSFORM_DISPLAY.
TRANSFORMATIONS: dict[str, str] = {
    "active_passive": "rewrite each sentence switching between active and passive voice",
    "direct_indirect": "convert each sentence between direct and indirect (reported) speech",
    "tense_change": "shift each sentence into a different tense (e.g. present → past, or past → future)",
    "affirm_negate": "turn affirmative sentences into negative ones and negative ones into affirmative",
    "statement_question": "turn statements into questions and questions into statements",
    "singular_plural": "switch the subject between singular and plural, adjusting all agreement",
    "mixed": (
        "apply a DIFFERENT transformation to each sentence — vary among active/passive, "
        "direct/indirect speech, tense change, negation, statement/question and "
        "singular/plural — and label each sentence with the transformation it requires"
    ),
}
DEFAULT_TRANSFORMATION: str = "mixed"

# Cloze grammar-focus presets: bias the blanks toward one grammar point instead
# of the default vocab-driven blanks. Keys are stable; the English phrase is
# injected into the (English) cloze prompt, the label is localized in
# i18n.GRAMMAR_FOCUS_DISPLAY. Free-text focus (typed by the user) overrides these.
GRAMMAR_FOCI: dict[str, str] = {
    "tenses": "verb tenses — the blanks must test correctly conjugated verb forms across tenses",
    "mood": "verb mood — the blanks must test the subjunctive/conditional where the language has it",
    "pronouns": "pronouns — the blanks must test subject, object, relative and possessive pronouns",
    "articles_gender": "articles and grammatical gender — the blanks must test the correct article/gender form",
    "adjective_agreement": "adjective agreement — the blanks must test adjective endings agreeing in gender and number",
    "prepositions": "prepositions — the blanks must test the correct preposition (and any case it governs)",
    "cases": "noun/adjective case — the blanks must test correct case endings and declension",
    "negation": "negation — the blanks must test correct negation forms and particles",
}

# DELF production-écrite text types: keys are stable, the English phrase is the
# consigne hint injected into the (English) task prompt, the label is localized
# in i18n.TEXT_TYPE_DISPLAY.
TEXT_TYPES: dict[str, str] = {
    "email": "an email — state clearly to whom and why (e.g. to a friend, or a semi-formal email to a colleague), with an appropriate opening and closing",
    "formal_letter": "a formal letter (e.g. a complaint, an application, or a request to an institution), with a proper salutation, structured body and closing formula",
    "opinion_essay": "an argumentative opinion essay: introduction, two or three arguments with examples, a counter-argument, and a conclusion",
    "forum_post": "a forum or blog post reacting to a topic, giving a personal opinion supported by reasons and examples",
    "summary": "a summary in your own words that condenses the key points of the described text or situation without adding personal opinion",
}
DEFAULT_TEXT_TYPE: str = "email"

# OpenRouter model IDs (https://openrouter.ai/models).
# 4-tier selection: budget / balanced / premium / best.
# See research/2026-04-20-model-provider-analysis.md for the rationale.
MODEL_TIERS: dict[str, str] = {
    "💰 Budget (Gemini Flash Lite)": "google/gemini-2.5-flash-lite",
    "⚖️ Balanced (Claude Haiku 4.5)": "anthropic/claude-haiku-4.5",
    "🚀 Premium (Mistral Large 3)": "mistralai/mistral-large-2512",
    "👑 Best (Claude Sonnet 4.6)": "anthropic/claude-sonnet-4.6",
}

MODELS: list[str] = list(MODEL_TIERS.values())

# Default picked by learning-language — cyrillic languages need UK-safe model.
# Default model tier: Claude Haiku 4.5 (Balanced) — best quality/cost across all
# 5 learning languages including Ukrainian. Budget tier still one click away in
# the sidebar for cost-conscious users.
DEFAULT_MODEL: str = "anthropic/claude-haiku-4.5"
DEFAULT_MODEL_UK: str = "anthropic/claude-haiku-4.5"

DEFAULT_LANGUAGE: str = "französisch"


def default_model_for_language(language: str) -> str:
    """Pick a sensible default model based on target language.

    Ukrainian (Cyrillic), Polish (Slavic with heavy diacritics), Greek
    (non-Latin alphabet + rich case morphology), Arabic (non-Latin + RTL +
    rich morphology) and Hebrew (non-Latin + RTL) all need the stronger Haiku
    default — smaller models hallucinate morphology.
    """
    lang = language.lower()
    if lang.startswith(("ukrain", "polnisch", "griech", "arab", "hebrä", "hebra")):
        return DEFAULT_MODEL_UK
    return DEFAULT_MODEL

NO_ANSWERS_HINT: str = " Nenne nicht die Antworten. "
