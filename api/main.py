"""lingua-core — FastAPI wrapper around the V1 task/grading logic (V2 Phase 0).

The Streamlit V1 app stays untouched; this service re-uses the exact same
``src/`` modules (prompts, tasks, correction, delf, placement) behind HTTP, so
the future Next.js V2 frontend can call them without re-implementing anything.

Run (from the repo root, V1 venv):
    .venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8557

Representative endpoint coverage (one per task *shape*); the remaining types
(writing/sentence/error/synonym/conjugation/dictation/listening) are mechanical
additions in Phase 2.
"""
from __future__ import annotations

import base64
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.client import DEFAULT_MODEL, build_client, elevenlabs_key
from src.config import TEXT_TYPES, TRANSFORMATIONS
from src.correction import (
    answer_comment,
    correct_text,
    correct_text_stream,
    extract_comments,
)
from src.tasks import cloze as cloze_task
from src.tasks import delf as delf_task
from src.tasks import placement as placement_task
from src.tasks import reading as reading_task
from src.tasks import transformation as transform_task
from src.tasks import translation as translation_task
from src.tasks import sentence_building as sentence_task
from src.tasks import error_detection as error_task
from src.tasks import conjugation as conjugation_task
from src.tasks import synonym_antonym as synonym_task
from src.tasks import quiz as quiz_task
from src.tasks import dictation as dictation_task
from src.tasks import speaking as speaking_task
from src.tasks import chat as chat_task
from src.tasks import grammar as grammar_task
from src.vocab import (
    extract_vocabulary_from_text,
    fetch_article_text,
    generate_vocabulary_via_function_call,
    translate_vocabulary_via_function_call,
)

# Shared-secret auth. When LINGUA_CORE_TOKEN is set (production / public route),
# every endpoint except /health requires `Authorization: Bearer <token>`. When
# unset (local dev, 127.0.0.1-bound) it is open — same operator-gated pattern as
# the rest of the stack. This protects the managed OpenRouter key behind a public
# Caddy route (Vercel cannot reach Tailscale, so the API must be public).
_API_TOKEN = (os.environ.get("LINGUA_CORE_TOKEN") or "").strip()


async def require_token(request: Request) -> None:
    if request.url.path == "/health" or not _API_TOKEN:
        return
    if request.headers.get("authorization") != f"Bearer {_API_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid or missing token")


app = FastAPI(
    title="lingua-core", version="0.1.0", dependencies=[Depends(require_token)],
)

_client = None


def client():
    global _client
    if _client is None:
        try:
            _client = build_client()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _client


def _model(m: str | None) -> str:
    return (m or DEFAULT_MODEL).strip()


@app.get("/health")
def health():
    return {"status": "ok", "service": "lingua-core", "default_model": DEFAULT_MODEL}


# ---- vocabulary (foundational; most tasks need a vocab list) ----
class VocabReq(BaseModel):
    language: str
    level: str
    niveau: str
    theme: str = ""  # optional: pin the list to a topic (Topic-Units)
    model: str | None = None


@app.post("/vocab/generate")
def vocab_generate(r: VocabReq):
    vocab = generate_vocabulary_via_function_call(
        client(), language=r.language, level=r.level, niveau=r.niveau,
        theme=r.theme, model=_model(r.model),
    )
    return {"vocab": vocab}


# ---- vocab sourcing: extract from text / URL, translate (glosses) ----
class VocabExtractReq(BaseModel):
    text: str
    language: str
    level: str
    number: int = 20
    model: str | None = None


@app.post("/vocab/extract")
def vocab_extract(r: VocabExtractReq):
    vocab = extract_vocabulary_from_text(
        client(), text=r.text, language=r.language, level=r.level,
        number=r.number, model=_model(r.model),
    )
    return {"vocab": vocab}


class VocabUrlReq(BaseModel):
    url: str
    language: str
    level: str
    number: int = 20
    model: str | None = None


@app.post("/vocab/from-url")
def vocab_from_url(r: VocabUrlReq):
    try:
        text = fetch_article_text(r.url)
    except Exception as exc:  # newspaper3k raises various errors on bad URLs
        raise HTTPException(status_code=502, detail=f"could not fetch URL: {exc}") from exc
    vocab = extract_vocabulary_from_text(
        client(), text=text, language=r.language, level=r.level,
        number=r.number, model=_model(r.model),
    )
    return {"vocab": vocab}


class VocabTranslateReq(BaseModel):
    words: list[str]
    learning_language: str
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/vocab/translate")
def vocab_translate(r: VocabTranslateReq):
    translations = translate_vocabulary_via_function_call(
        client(), words=r.words, learning_language=r.learning_language,
        ui_language_name=r.ui_language_name, model=_model(r.model),
    )
    return {"translations": translations}


# ---- cloze (structured tool-call task) ----
class ClozeReq(BaseModel):
    vocab_list: list[str]
    language: str
    level: str
    niveau: str
    number_trous: int = 4
    grammar_focus: str = ""
    ui_lang: str = "en"
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/generate/cloze")
def generate_cloze(r: ClozeReq):
    instr = cloze_task.build(
        client(), vocab_list=r.vocab_list, language=r.language, level=r.level,
        niveau=r.niveau, number_trous=r.number_trous, model=_model(r.model),
        ui_lang=r.ui_lang, ui_language_name=r.ui_language_name, grammar_focus=r.grammar_focus,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


# ---- transformation (free-answer task) ----
class TransformReq(BaseModel):
    vocab_list: list[str]
    language: str
    level: str
    niveau: str
    number_sentences: int = 3
    transformation: str = "mixed"
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/generate/transformation")
def generate_transformation(r: TransformReq):
    t_en = TRANSFORMATIONS.get(r.transformation, TRANSFORMATIONS["mixed"])
    instr = transform_task.build(
        client(), vocab_list=r.vocab_list, language=r.language, level=r.level,
        niveau=r.niveau, number_sentences=r.number_sentences, transformation_en=t_en,
        model=_model(r.model), ui_language_name=r.ui_language_name,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


# ---- translation (free-answer task) ----
class TranslationReq(BaseModel):
    vocab_list: list[str]
    language: str
    level: str
    niveau: str
    number_sentences: int = 3
    direction: str = "to_learning"
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/generate/translation")
def generate_translation(r: TranslationReq):
    instr = translation_task.build(
        client(), vocab_list=r.vocab_list, language=r.language, level=r.level,
        niveau=r.niveau, number_sentences=r.number_sentences, model=_model(r.model),
        ui_language_name=r.ui_language_name, direction=r.direction,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


# ---- sentence building / error detection / conjugation (free-answer, vocab-based) ----
class VocabTaskReq(BaseModel):
    vocab_list: list[str]
    language: str
    level: str
    niveau: str
    ui_lang: str = "en"
    model: str | None = None


@app.post("/generate/sentence")
def generate_sentence(r: VocabTaskReq):
    instr = sentence_task.build(
        client(), vocab_list=r.vocab_list, language=r.language, level=r.level,
        niveau=r.niveau, model=_model(r.model), ui_lang=r.ui_lang,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


@app.post("/generate/error")
def generate_error(r: VocabTaskReq):
    instr = error_task.build(
        client(), vocab_list=r.vocab_list, language=r.language, level=r.level,
        niveau=r.niveau, model=_model(r.model), ui_lang=r.ui_lang,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


@app.post("/generate/conjugation")
def generate_conjugation(r: VocabTaskReq):
    instr = conjugation_task.build(
        client(), vocab_list=r.vocab_list, language=r.language, level=r.level,
        niveau=r.niveau, model=_model(r.model), ui_lang=r.ui_lang,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


# ---- synonym / antonym (local free-answer task, no LLM in build) ----
class SynonymReq(BaseModel):
    vocab_list: list[str]
    ui_lang: str = "en"


@app.post("/generate/synonym")
def generate_synonym(r: SynonymReq):
    instr = synonym_task.build(vocab_list=r.vocab_list, ui_lang=r.ui_lang)
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


# ---- vocabulary quiz (translation prompts + tolerant scoring) ----
class QuizBuildReq(BaseModel):
    vocab_list: list[str]
    language: str
    count: int = 8
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/quiz/build")
def quiz_build(r: QuizBuildReq):
    quiz = quiz_task.build_quiz(
        client(), vocab_list=r.vocab_list, language=r.language, count=r.count,
        model=_model(r.model), ui_language_name=r.ui_language_name,
    )
    return {"quiz": quiz}


class QuizScoreReq(BaseModel):
    quiz: dict[str, str]
    answers: dict[str, str]


@app.post("/quiz/score")
def quiz_score(r: QuizScoreReq):
    result = quiz_task.score_answers(r.quiz, r.answers)
    return {
        "correct": result.correct,
        "total": result.total,
        "per_word": result.per_word,
    }


# ---- dictation (LLM text → ElevenLabs TTS) ----
class DictationReq(BaseModel):
    language: str
    level: str
    niveau: str
    sentences: int = 3
    model: str | None = None


@app.post("/dictation")
def dictation(r: DictationReq):
    key = elevenlabs_key()
    if not key:
        raise HTTPException(status_code=503, detail="TTS not configured")
    text = dictation_task.generate_text(
        client(), language=r.language, level=r.level, niveau=r.niveau,
        model=_model(r.model), sentences=r.sentences,
    )
    try:
        audio = dictation_task.synthesize_speech(text, api_key=key)
    except dictation_task.TTSUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"text": text, "audio_base64": base64.b64encode(audio).decode("ascii")}


# ---- listening (TTS passage + comprehension questions) ----
class ListeningReq(BaseModel):
    language: str
    level: str
    niveau: str
    theme: str = ""  # optional: pin the passage to a topic (Topic-Units)
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/listening")
def listening(r: ListeningReq):
    key = elevenlabs_key()
    if not key:
        raise HTTPException(status_code=503, detail="TTS not configured")
    transcript = dictation_task.generate_text(
        client(), language=r.language, level=r.level, niveau=r.niveau,
        theme=r.theme, model=_model(r.model), sentences=6,
    )
    try:
        audio = dictation_task.synthesize_speech(transcript, api_key=key)
    except dictation_task.TTSUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    q = reading_task.generate_questions(
        client(), text=transcript, language=r.language, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    return {
        "transcript": transcript,
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "multiple_choice": q.multiple_choice,
        "open_questions": q.open_questions,
    }


# ---- correction (shared grading path for free-answer tasks) ----
class CorrectReq(BaseModel):
    task: str
    user_text: str
    language: str
    niveau: str
    mentor: str = "Netter Lehrer"
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/correct")
def correct(r: CorrectReq):
    # V1 parity: pull <meta-questions> out of the answer, grade the cleaned text,
    # and answer each embedded question separately.
    cleaned, comments = extract_comments(r.user_text)
    correction = correct_text(
        client(), task=r.task, user_text=cleaned, language=r.language,
        niveau=r.niveau, mentor=r.mentor, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    comment_answers = [
        {
            "question": c,
            "answer": answer_comment(client(), comment=c, model=_model(r.model)),
        }
        for c in comments
    ]
    return {"correction": correction, "comment_answers": comment_answers}


@app.post("/correct/stream")
def correct_stream(r: CorrectReq):
    # Same grading as /correct, streamed token-by-token for the live-feedback UI.
    # Any embedded <meta-questions> are answered and appended after the feedback.
    cleaned, comments = extract_comments(r.user_text)

    def gen():
        yield from correct_text_stream(
            client(), task=r.task, user_text=cleaned, language=r.language,
            niveau=r.niveau, mentor=r.mentor, model=_model(r.model),
            ui_language_name=r.ui_language_name,
        )
        for c in comments:
            ans = answer_comment(client(), comment=c, model=_model(r.model))
            yield f"\n\n---\n\n**{c}**\n\n{ans}"

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")


# ---- DELF production écrite (consigne + grille assessment) ----
class DelfTaskReq(BaseModel):
    language: str
    level: str
    text_type: str = "email"
    word_target: int = 160
    theme: str = "everyday life"
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/delf/task")
def delf_task_endpoint(r: DelfTaskReq):
    tt = TEXT_TYPES.get(r.text_type, TEXT_TYPES["email"])
    instr = delf_task.build(
        client(), language=r.language, level=r.level, text_type_en=tt,
        word_target=r.word_target, theme=r.theme, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


class DelfEvalReq(BaseModel):
    task: str
    user_text: str
    language: str
    level: str
    text_type: str = "email"
    word_target: int = 160
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/delf/evaluate")
def delf_evaluate_endpoint(r: DelfEvalReq):
    tt = TEXT_TYPES.get(r.text_type, TEXT_TYPES["email"])
    a = delf_task.evaluate(
        client(), task=r.task, user_text=r.user_text, language=r.language, level=r.level,
        text_type_en=tt, word_target=r.word_target, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    return {
        "criteria": a.criteria, "word_count": a.word_count, "overall": a.overall,
        "suggestions": a.suggestions, "total": a.total, "max_total": delf_task.MAX_TOTAL,
    }


# ---- speaking (production orale): spoken-task brief + Gemini audio grille ----
class SpeakingTaskReq(BaseModel):
    language: str
    level: str
    theme: str = ""
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/speaking/task")
def speaking_task_endpoint(r: SpeakingTaskReq):
    instr = speaking_task.build_task(
        client(), language=r.language, level=r.level, theme=r.theme,
        model=_model(r.model), ui_language_name=r.ui_language_name,
    )
    return {"displayed": instr.displayed_to_user, "language": r.language}


class SpeakingEvalReq(BaseModel):
    audio_base64: str
    mime_type: str = "audio/webm"
    task: str
    language: str
    level: str
    ui_language_name: str = "English"
    gemini_model: str = speaking_task.DEFAULT_GEMINI_MODEL


@app.post("/speaking/evaluate")
def speaking_evaluate_endpoint(r: SpeakingEvalReq):
    try:
        audio = base64.b64decode(r.audio_base64)
    except Exception as exc:  # malformed payload
        raise HTTPException(status_code=400, detail=f"invalid audio: {exc}") from exc
    if not audio:
        raise HTTPException(status_code=400, detail="empty audio")
    try:
        a = speaking_task.evaluate_audio(
            audio_bytes=audio, mime_type=r.mime_type, task=r.task,
            language=r.language, level=r.level, ui_language_name=r.ui_language_name,
            gemini_model=r.gemini_model,
        )
    except RuntimeError as exc:  # missing GEMINI key / transcode failure
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "criteria": a.criteria, "transcript": a.transcript, "overall": a.overall,
        "suggestions": a.suggestions, "total": a.total, "max_total": speaking_task.MAX_TOTAL,
    }


# ---- conversation chat (reply + inline correction) ----
class ChatMsg(BaseModel):
    role: str
    content: str


class ChatReq(BaseModel):
    history: list[ChatMsg]
    language: str
    niveau: str
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/chat")
def chat_endpoint(r: ChatReq):
    return chat_task.respond(
        client(), history=[m.model_dump() for m in r.history], language=r.language,
        niveau=r.niveau, model=_model(r.model), ui_language_name=r.ui_language_name,
    )


# ---- reading comprehension (multi-step: passage → questions) ----
class ReadingTextReq(BaseModel):
    language: str
    level: str
    niveau: str
    theme: str = "everyday life"
    length: str = "medium"
    model: str | None = None


@app.post("/reading/text")
def reading_text(r: ReadingTextReq):
    return {
        "passage": reading_task.generate_text(
            client(), language=r.language, level=r.level, niveau=r.niveau,
            theme=r.theme, length=r.length, model=_model(r.model),
        )
    }


class ReadingQReq(BaseModel):
    text: str
    language: str
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/reading/questions")
def reading_questions(r: ReadingQReq):
    q = reading_task.generate_questions(
        client(), text=r.text, language=r.language, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    return {"multiple_choice": q.multiple_choice, "open_questions": q.open_questions}


class OpenEvalReq(BaseModel):
    text: str
    question: str
    reference_answer: str
    user_answer: str
    language: str
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/reading/evaluate-open")
def reading_evaluate_open(r: OpenEvalReq):
    # V1 parity: grade an open-ended answer with a verdict + feedback (used by
    # both reading and listening, which share generate_questions).
    ev = reading_task.evaluate_open(
        client(), text=r.text, question=r.question,
        reference_answer=r.reference_answer, user_answer=r.user_answer,
        language=r.language, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    return {"verdict": ev.verdict, "feedback": ev.feedback}


# ---- CEFR placement test (structured + pure-logic scoring) ----
class PlacementReq(BaseModel):
    language: str
    model: str | None = None


@app.post("/placement/test")
def placement_test(r: PlacementReq):
    return {"questions": placement_task.build_test(client(), language=r.language, model=_model(r.model))}


class RecommendReq(BaseModel):
    questions: list[dict]
    answers: list[int | None]


@app.post("/placement/recommend")
def placement_recommend(r: RecommendReq):
    return {"level": placement_task.recommend_level(r.questions, r.answers)}


# ---- standalone grammar track (P4): on-the-fly explanation + focused drill ----
class GrammarExplainReq(BaseModel):
    language: str
    level: str
    topic: str
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/grammar/explain")
def grammar_explain(r: GrammarExplainReq):
    instr = grammar_task.explain(
        client(), language=r.language, level=r.level, topic=r.topic,
        model=_model(r.model), ui_language_name=r.ui_language_name,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}


class GrammarDrillReq(BaseModel):
    language: str
    level: str
    topic: str
    exercise_type: str = "cloze"
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/grammar/drill")
def grammar_drill(r: GrammarDrillReq):
    instr = grammar_task.drill(
        client(), language=r.language, level=r.level, topic=r.topic,
        exercise_type=r.exercise_type, model=_model(r.model),
        ui_language_name=r.ui_language_name,
    )
    return {"displayed": instr.displayed_to_user, "context": instr.internal_context}
