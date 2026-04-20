"""Command-line variant of franz-lern.

Subset of the Streamlit app — text-based loop with multi-line input via
prompt_toolkit. Shares the same prompts, vocab, correction and task modules.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import openai
from dotenv import find_dotenv, load_dotenv
from prompt_toolkit import prompt

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (  # noqa: E402
    DEFAULT_LANGUAGE,
    LANGUAGES,
    LEVELS,
    MODELS,
    NIVEAU_LEVELS,
    THEMES,
    default_model_for_language,
)
from src.correction import correct_text, extract_comments  # noqa: E402
from src.tasks import cloze, translation, writing  # noqa: E402
from src.vocab import load_vocabulary  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--vocab-file", required=True, help="Path to vocabulary .txt file")
    p.add_argument("--language", default=DEFAULT_LANGUAGE)
    p.add_argument("--level", default="B1")
    p.add_argument("--niveau", default="Standardsprache")
    p.add_argument("--mentor", default="Netter Lehrer")
    p.add_argument("--model", default=None, help="OpenRouter model-id; default picked by language")
    p.add_argument(
        "--task",
        default="writing",
        choices=["writing", "cloze", "translation"],
    )
    args = p.parse_args()
    if args.language not in LANGUAGES:
        p.error(f"--language must be one of {LANGUAGES}")
    if args.level not in LEVELS:
        p.error(f"--level must be one of {LEVELS}")
    if args.niveau not in NIVEAU_LEVELS:
        p.error(f"--niveau must be one of {NIVEAU_LEVELS}")
    if args.model is None:
        args.model = default_model_for_language(args.language)
    elif args.model not in MODELS:
        print(f"Warning: --model {args.model} not in preset tiers {MODELS} — using as-is (must be a valid OpenRouter id).")
    return args


def main() -> None:
    args = _parse_args()
    load_dotenv(find_dotenv(usecwd=True))
    or_key = os.environ.get("OPENROUTER_API_KEY")
    oa_key = os.environ.get("OPENAI_API_KEY")
    if or_key:
        client = openai.OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
    elif oa_key:
        print("Warning: no OPENROUTER_API_KEY — falling back to direct OpenAI. Set OPENROUTER_API_KEY for tier dropdown.")
        client = openai.OpenAI(api_key=oa_key)
    else:
        sys.exit("Neither OPENROUTER_API_KEY nor OPENAI_API_KEY found in .env")

    vocab = load_vocabulary(args.vocab_file)
    print(f"Loaded {len(vocab)} vocabulary items from {args.vocab_file}")

    if args.task == "writing":
        instr = writing.build(themes=THEMES, previous_theme="")
    elif args.task == "cloze":
        instr = cloze.build(
            client,
            vocab_list=vocab,
            language=args.language,
            level=args.level,
            niveau=args.niveau,
            number_trous=4,
            model=args.model,
        )
    elif args.task == "translation":
        instr = translation.build(
            client,
            vocab_list=vocab,
            language=args.language,
            level=args.level,
            niveau=args.niveau,
            number_sentences=2,
            model=args.model,
        )
    else:
        raise AssertionError(f"unreachable: {args.task}")

    print("\n=== Aufgabe ===")
    print(instr.displayed_to_user)
    print("===============\n")

    user_text = prompt("Deine Antwort (Strg-D zum Absenden):\n", multiline=True)
    cleaned, _ = extract_comments(user_text)
    corrected = correct_text(
        client,
        task=instr.displayed_to_user,
        user_text=cleaned,
        language=args.language,
        niveau=args.niveau,
        mentor=args.mentor,
        model=args.model,
    )
    print("\n=== Korrigiert ===")
    print(corrected)


if __name__ == "__main__":
    main()
