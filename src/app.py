"""Streamlit entrypoint for franz-lern.

Start::

    streamlit run src/app.py -- --language=französisch
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import openai
import streamlit as st
from dotenv import find_dotenv, load_dotenv

# Make "src" importable when run via `streamlit run src/app.py`
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (  # noqa: E402
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    LANGUAGES,
    LEVELS,
    MENTORS,
    MODELS,
    NIVEAU_LEVELS,
    TASK_LIST,
    THEMES,
)
from src.correction import answer_comment, correct_text, extract_comments  # noqa: E402
from src.logging_setup import get_logger  # noqa: E402
from src.state import init_session_state  # noqa: E402
from src.tasks import cloze as cloze_task  # noqa: E402
from src.tasks import conjugation as conj_task  # noqa: E402
from src.tasks import error_detection as err_task  # noqa: E402
from src.tasks import quiz as quiz_task  # noqa: E402
from src.tasks import sentence_building as sent_task  # noqa: E402
from src.tasks import synonym_antonym as syn_task  # noqa: E402
from src.tasks import translation as trans_task  # noqa: E402
from src.tasks import writing as write_task  # noqa: E402
from src.tasks.radio import RADIO_TASK_NAME, get_channels, is_audio_available  # noqa: E402
from src.vocab import (  # noqa: E402
    extract_vocabulary_from_text,
    fetch_article_text,
    generate_vocabulary_via_function_call,
)

log = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    """Single-call argparse that tolerates Streamlit's own CLI flags.

    Fixes TES-542 — legacy code called ``parser.parse_args()`` twice in a row
    and crashed as soon as Streamlit forwarded its own ``--server.*`` flags.
    """
    parser = argparse.ArgumentParser(description="franz-lern Streamlit app")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model to use")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Language to learn")
    args, _unknown = parser.parse_known_args()
    if args.model not in MODELS:
        args.model = DEFAULT_MODEL
    if args.language not in LANGUAGES:
        args.language = DEFAULT_LANGUAGE
    return args


def _ensure_openai_client() -> openai.OpenAI:
    load_dotenv(find_dotenv(usecwd=True))
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("Kein OPENAI_API_KEY gefunden. Bitte `.env` aus `.env.example` erstellen.")
        st.stop()
    return openai.OpenAI(api_key=api_key)


def main() -> None:
    args = _parse_args()
    model = args.model
    language = args.language

    init_session_state(st.session_state)
    state = st.session_state["state"]

    log.info("Run %s — model=%s language=%s", state.num_runs, model, language)

    st.title(f"{language.capitalize()} — Lernprogramm")
    st.caption("Out-game-Kommentare bitte in <> packen — werden separat beantwortet.")

    client = _ensure_openai_client()

    # --- Sidebar ------------------------------------------------------------
    st.sidebar.title("Einstellungen")
    mentor = st.sidebar.selectbox("Coach:", MENTORS, index=0, key="mentor")
    level = st.sidebar.selectbox("Sprachniveau:", LEVELS, index=2, key="level")
    niveau = st.sidebar.selectbox("Sprachregister:", NIVEAU_LEVELS, index=3, key="niveau")
    st.sidebar.divider()
    st.sidebar.markdown("## Vokabelliste")

    extract_files = st.sidebar.file_uploader(
        "Vokabeln aus Txt-Dateien extrahieren:",
        accept_multiple_files=True,
        type=["txt"],
    )
    number_of_words = st.sidebar.number_input(
        "Anzahl Vokabeln:",
        min_value=1,
        max_value=200,
        value=state.number_of_words,
        key="number_of_words",
    )
    url_extract = st.sidebar.text_input("Oder: Vokabeln aus Webseite:")
    uploaded_vocab = st.sidebar.file_uploader("Oder: Vokabel-Datei hochladen:", type=["txt"])

    # --- Vocab source handling ---------------------------------------------
    if extract_files and extract_files != state.file_path_extract:
        all_text = "\n".join(f.read().decode("utf-8") for f in extract_files)
        state.vocab_list = extract_vocabulary_from_text(
            client,
            text=all_text,
            language=language,
            level=level,
            number=number_of_words,
            model=model,
        )
        st.sidebar.write(sorted(state.vocab_list))
    elif url_extract and url_extract != state.html_path_extract:
        article_text = fetch_article_text(url_extract)
        state.vocab_list = extract_vocabulary_from_text(
            client,
            text=article_text,
            language=language,
            level=level,
            number=number_of_words,
            model=model,
        )
        st.sidebar.write(sorted(state.vocab_list))
    elif uploaded_vocab and uploaded_vocab != state.uploaded_vocab_file:
        content = uploaded_vocab.read().decode("utf-8")
        state.vocab_list = [line.strip() for line in content.splitlines() if line.strip()]
        st.sidebar.write(sorted(state.vocab_list))
    elif state.auto_gen_vocabs:
        st.sidebar.write(sorted(state.vocab_list))

    state.file_path_extract = extract_files
    state.uploaded_vocab_file = uploaded_vocab
    state.html_path_extract = url_extract

    # --- Main panel --------------------------------------------------------
    task_type = st.selectbox("Übung wählen:", TASK_LIST, key="task_type_sel")

    vocab_missing = not state.vocab_list
    needs_vocab = task_type not in ("", "Schreiben eines Textes und danach Korrektur")
    if vocab_missing and needs_vocab:
        if st.button("Vokabelliste automatisch generieren"):
            state.vocab_list = generate_vocabulary_via_function_call(
                client,
                language=language,
                level=level,
                niveau=niveau,
                model=model,
            )
            state.auto_gen_vocabs = True
            st.rerun()
        else:
            st.info("Lade eine Vokabelquelle (Sidebar) oder klicke auf 'automatisch generieren'.")
            return

    if task_type == "Schreiben eines Textes und danach Korrektur":
        if st.button("Neue Aufgabe") or not state.task:
            instr = write_task.build(themes=THEMES, previous_theme=state.theme)
            state.theme = instr.internal_context["theme"]
            state.task = instr.displayed_to_user

    elif task_type == "Ausfüllen eines Lückentextes in Fremdsprache":
        number_trous = st.number_input("Wortlücken:", min_value=3, max_value=20, value=4)
        if st.button("Neue Aufgabe") or not state.task:
            instr = cloze_task.build(
                client,
                vocab_list=state.vocab_list,
                language=language,
                level=level,
                niveau=niveau,
                number_trous=number_trous,
                model=model,
            )
            state.task = instr.displayed_to_user

    elif task_type == "Vorgabe von deutschen Sätzen zum Übersetzen":
        number_sentences = st.number_input("Sätze:", min_value=1, max_value=20, value=1)
        if st.button("Neue Aufgabe") or not state.task:
            instr = trans_task.build(
                client,
                vocab_list=state.vocab_list,
                language=language,
                level=level,
                niveau=niveau,
                number_sentences=number_sentences,
                model=model,
            )
            state.task = instr.displayed_to_user

    elif task_type == "Satzbauübung":
        if st.button("Neue Aufgabe") or not state.task:
            instr = sent_task.build(
                client,
                vocab_list=state.vocab_list,
                language=language,
                level=level,
                niveau=niveau,
                model=model,
            )
            state.task = instr.displayed_to_user

    elif task_type == "Fehler im Text finden und korrigieren":
        if st.button("Neue Aufgabe") or not state.task:
            instr = err_task.build(
                client,
                vocab_list=state.vocab_list,
                language=language,
                level=level,
                niveau=niveau,
                model=model,
            )
            state.task = instr.displayed_to_user

    elif task_type == "Synonyme und Antonyme finden":
        if st.button("Neue Aufgabe") or not state.task:
            instr = syn_task.build(vocab_list=state.vocab_list)
            state.task = instr.displayed_to_user

    elif task_type == "Verbkonjugation üben":
        if st.button("Neue Aufgabe") or not state.task:
            instr = conj_task.build(
                client,
                vocab_list=state.vocab_list,
                language=language,
                level=level,
                niveau=niveau,
                model=model,
            )
            state.task = instr.displayed_to_user

    elif task_type == "Vokabel-Quiz":
        if st.button("Neues Quiz") or "current_quiz" not in st.session_state:
            st.session_state["current_quiz"] = quiz_task.build_quiz(
                client,
                vocab_list=state.vocab_list,
                language=language,
                count=5,
                model=model,
            )
            st.session_state["quiz_answers"] = {}
        quiz = st.session_state.get("current_quiz", {})
        for fw, trans in quiz.items():
            st.session_state["quiz_answers"][fw] = st.text_input(
                f"Was ist das {language}e Wort für '{trans}'?",
                key=f"quiz_{fw}",
            )
        if st.button("Auswerten"):
            result = quiz_task.score_answers(quiz, st.session_state["quiz_answers"])
            st.write(f"Score: {result.correct}/{result.total}")
            for word, ok in result.per_word.items():
                st.write(f"- {word}: {'✅' if ok else '❌'}")

    elif task_type == RADIO_TASK_NAME:
        if not is_audio_available():
            st.warning(
                "Audio-Output nicht verfügbar (pyaudio/PortAudio fehlt oder kein "
                "Output-Device). Radio-Task funktioniert nur lokal."
            )
        else:
            channels = get_channels()
            channel = st.selectbox("Radiokanal:", list(channels.keys()))
            st.info(
                "Streaming-Kern ist in `src/tasks/radio.py`. Transkriptions-Pipeline "
                "ist als Roadmap-Item dokumentiert — siehe README."
            )
            st.markdown(f"Stream-URL: `{channels[channel]}`")

    # --- Correction panel --------------------------------------------------
    if task_type and task_type != RADIO_TASK_NAME and state.task:
        st.write(state.task)
        user_text = st.text_area("Dein Text:", value=state.user_text, key="user_text_area")
        if st.button("Text korrigieren"):
            cleaned, comments = extract_comments(user_text)
            corrected = correct_text(
                client,
                task=state.task,
                user_text=cleaned,
                language=language,
                niveau=niveau,
                mentor=mentor,
                model=model,
            )
            st.markdown("### Korrigierter Text")
            st.write(corrected)
            for c in comments:
                ans = answer_comment(client, comment=c, model=model)
                st.markdown(f"**Kommentar:** {c}  \n**Antwort:** {ans}")


if __name__ == "__main__":
    main()
