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
from pydantic import BaseModel

from api.client import DEFAULT_MODEL, build_client, elevenlabs_key
from src.config import TEXT_TYPES, TRANSFORMATIONS
from src.correction import correct_text
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
from src.vocab import generate_vocabulary_via_function_call

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
    model: str | None = None


@app.post("/vocab/generate")
def vocab_generate(r: VocabReq):
    vocab = generate_vocabulary_via_function_call(
        client(), language=r.language, level=r.level, niveau=r.niveau, model=_model(r.model),
    )
    return {"vocab": vocab}


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
    ui_language_name: str = "English"
    model: str | None = None


@app.post("/listening")
def listening(r: ListeningReq):
    key = elevenlabs_key()
    if not key:
        raise HTTPException(status_code=503, detail="TTS not configured")
    transcript = dictation_task.generate_text(
        client(), language=r.language, level=r.level, niveau=r.niveau,
        model=_model(r.model), sentences=6,
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
    return {
        "correction": correct_text(
            client(), task=r.task, user_text=r.user_text, language=r.language,
            niveau=r.niveau, mentor=r.mentor, model=_model(r.model),
            ui_language_name=r.ui_language_name,
        )
    }


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
