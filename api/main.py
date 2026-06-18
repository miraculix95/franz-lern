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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.client import DEFAULT_MODEL, build_client
from src.config import TEXT_TYPES, TRANSFORMATIONS
from src.correction import correct_text
from src.tasks import cloze as cloze_task
from src.tasks import delf as delf_task
from src.tasks import placement as placement_task
from src.tasks import reading as reading_task
from src.tasks import transformation as transform_task
from src.vocab import generate_vocabulary_via_function_call

app = FastAPI(title="lingua-core", version="0.1.0")

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
