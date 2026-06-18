# lingua-app V2 — Architektur-Konzept (Multi-Tenant-Produkt)

**Status:** Entwurf · **Datum:** 2026-06-18 · **Autor:** Bastian + Claude
**Vorgänger:** V1 (Streamlit, BYOK-stateless) — läuft produktiv auf `lingua.ai-devhub-247.site`

---

## 1. Kontext & Auslöser

V1 deckt drei der vier DELF-Kompetenzen mit echter Bewertung ab (Reading, Listening, Production écrite + Einstufungstest). Alle bisherigen Features sind **zustandslos** und passen zu Streamlit-BYOK.

**SRS (Spaced Repetition), Fehler-Journal und Progress sind die ersten Features, die pro Nutzer dauerhaften Zustand + Identität brauchen.** Das bricht das BYOK-stateless-Modell und ist (Entscheidung 2026-06-18) der Anlass, lingua-app zum **echten Mehrnutzer-Produkt** zu machen — Zielgruppe u. a. (halb-alphabetisierte) Migranten, die Sprachzertifikate (DELF/telc/Goethe) brauchen.

## 2. Harte Randbedingungen (nicht verhandelbar)

1. **V1 läuft unangetastet weiter.** Kein In-place-Umbau der Streamlit-App. V1 bleibt auf `lingua.ai-devhub-247.site` als funktionierendes Tool/Showcase.
2. **V2 entsteht in einem neuen Projekt-Verzeichnis** (`~/cc-dev/lingua-v2/`) und auf einer **neuen Subdomain** (Vorschlag: `lingua2.ai-devhub-247.site` oder eigene Produkt-Domain — Naming offen, siehe §7).
3. **Die Python-Logik wird nicht in TypeScript neu geschrieben.** prompts / tasks / DELF-Grille / Placement / Grading werden als Service wiederverwendet.
4. **Architektur kostenmodell-agnostisch** bauen: managed API-Keys serverseitig + Usage-Tracking pro Nutzer von Anfang an, damit später jedes Kostenmodell (gefördert / Freemium / B2B) ohne Umbau aufsetzbar ist.

## 3. ADR — V1→V2-Architektur

- **Optionen:**
  - **A) Streamlit + lokale Single-User-Persistenz** (SQLite, kein Auth) — nur für „persönliches Tool". Verworfen, da Mehrnutzer-Produkt beschlossen.
  - **B) Streamlit + Supabase + Auth-Bolt-on** — Streamlit ist schwacher Multi-Tenant-Host (ein geteilter Prozess, keine Pro-User-Isolation, fummeliges Auth). Halbschritt, der Streamlits Schwächen erbt. Verworfen.
  - **C) Voll-Rewrite in Next.js/TypeScript** (inkl. Prompts/Grading in TS) — wirft die mühsam gebaute, getestete Python-Logik (112 Tests) weg. Verworfen.
  - **D) Next.js + Auth + Postgres als Hülle, FastAPI um die bestehende Python-Logik** — gewählt.
- **Gewählt:** **D.** Next.js (Frontend, Auth, Vercel) + **FastAPI-Service** (wrappt die existierenden `src/`-Module von V1 unverändert) + **Postgres** (User, SRS, Journal, Progress, Usage). Behält das Gehirn, ersetzt nur die Hülle; nutzt fertige SaaS-Bausteine (Auth, DB) statt Eigenbau (`saas-before-coding`).
- **Konsequenz:** Zwei deploybare Artefakte statt einem (Next.js + FastAPI), eine DB, managed LLM-Keys = laufende Kosten pro Nutzer (BYOK-Vorteil entfällt) + GDPR-Pflichten (Nutzerdaten). Mehr Infra als V1.
- **Revisions-Trigger:** Wenn sich herausstellt, dass es doch ein Single-User-Tool bleibt → zurück zu A (V2 einmotten). Wenn die FastAPI-Wiederverwendung an V1-Code-Kopplung scheitert → Logik-Extraktion in ein sauberes `lingua-core`-Package neu bewerten.

## 4. Ziel-Architektur

```
Browser (Lerner, mobil-first)
        │  HTTPS
        ▼
Next.js (App Router) — neue Subdomain, Vercel
  • Auth (Clerk ODER Supabase Auth — Entscheidung §7)
  • UI: Übungen, SRS-Review, Fehler-Journal, Progress, Einstufungstest
  • i18n (8 UI-Sprachen aus V1 übernehmen)
        │  authentifizierte API-Calls (JWT)
        ▼
FastAPI „lingua-core" — App-Server (Tailscale/Caddy)
  • importiert V1-`src/`: prompts.py, tasks/*, correction, delf, placement
  • managed LLM-Keys (OpenRouter/Anthropic) serverseitig
  • Endpunkte: generate_task, correct_text, evaluate_delf, placement, tts(ElevenLabs)
  • Usage-Tracking pro Nutzer (Tokens/Calls) → Postgres
        │
        ▼
Postgres (Supabase ODER App-Server)
  • users, srs_cards, error_journal, progress, usage_events
```

**Hosting:** Next.js → Vercel (wie HypeType). FastAPI → App-Server (Docker, hinter Caddy, neue Subdomain für die API oder interne Tailscale-Route). Postgres → Supabase (managed, kommt ggf. mit Auth) ODER App-Server-Postgres (datalab-Box) — Entscheidung §7.

## 5. Reuse vs. Rewrite

| V1-Komponente | V2 |
|---|---|
| `src/prompts.py`, `src/tasks/*`, `src/correction.py`, `delf.py`, `placement.py` | **1:1 wiederverwenden** hinter FastAPI |
| `src/i18n.py` (Übersetzungen) | Strings nach Next.js-i18n übernehmen (JSON-Export) |
| `src/config.py` (LEVELS, NIVEAU, TEXT_TYPES, …) | als Konstanten/Config in beide Seiten spiegeln |
| `src/app.py` (Streamlit-UI) | **wegwerfen** — durch Next.js ersetzt |
| Tests (`tests/`, 112) | Pure-Function-Tests bleiben gültig (testen `src/`-Logik) |

## 6. Datenmodell (Skizze)

- **users** — id (von Auth-Provider), ui_lang, learning_language, level, created_at
- **srs_cards** — id, user_id, learning_language, front (Vokabel), back (Übersetzung/Kontext), FSRS-Felder (stability, difficulty, due, reps, lapses, last_review) — **FSRS** als Algorithmus (moderner als SM-2)
- **error_journal** — id, user_id, task_type, original, correction, category, created_at
- **progress** — user_id, metriken (tasks_done, corrections, streak, per-skill)
- **usage_events** — user_id, endpoint, model, tokens_in/out, cost_estimate, ts → für jedes Kostenmodell

## 7. Offene Entscheidungen (vor/bei Umsetzung)

1. **Kostenmodell** — *bewusst offen gelassen* (Entscheidung Bastian 2026-06-18). Optionen: gratis/gefördert · Freemium (Stripe) · B2B (Träger zahlen pro Gruppe). Architektur ist agnostisch (managed keys + usage_events von Anfang an). **Bestimmt** Auth-Wahl + ob Payment/Quota gebaut wird.
2. **Auth:** Clerk (stark bei B2B/Organizations) vs. Supabase Auth (kommt mit der DB, eine Sache weniger). Hängt an (1): B2B → Clerk; reines B2C → Supabase Auth.
3. **Postgres:** Supabase (managed, + evtl. Auth gebündelt) vs. App-Server-Postgres (schon da, datalab-Box, kein neuer Dienst).
4. **Subdomain-Name** (Public-Surface, deine Entscheidung): `lingua2.` / `app.lingua…` / eigene Produkt-Domain?
5. **Default-LLM-Modell** bei managed keys (Kosten!): günstiges Default (Gemini Flash Lite / Haiku) mit Usage-Limits.

## 8. Phasen-Plan (kein Big-Bang; V1 läuft durchgehend weiter)

- **Phase 0 — FastAPI um V1-Logik.** `lingua-core` Service, importiert V1-`src/`, Endpunkte für die bestehenden Tasks. *Verify:* curl gegen jeden Endpunkt liefert dieselben Ergebnisse wie V1.
- **Phase 1 — Next.js-Shell + Auth + 1 Sprache.** Projekt-Setup, Auth-Flow, ein Exercise-Type (z. B. Cloze) end-to-end gegen FastAPI. *Verify:* eingeloggter Nutzer macht eine Übung, Korrektur erscheint.
- **Phase 2 — Exercise-Types portieren.** Reading, Listening, DELF, Transformation, Einstufungstest. i18n-Strings übernehmen. *Verify:* Feature-Parität mit V1 je Type.
- **Phase 3 — Persistenz/SRS.** Postgres-Schema, SRS (FSRS) + Fehler-Journal + Progress. *Verify:* Karte heute gelernt → morgen fällig; Journal persistiert über Sessions/Geräte.
- **Phase 4 — Kostenmodell + Limits** (sobald Entscheidung 1 fällt): Quota/Payment/Org-Seats je nach Modell.
- **Phase 5 — Launch** auf der neuen Subdomain; V1 bleibt als Fallback/Showcase online (oder wird später eingemottet).

Jede Phase ist ein eigenes Linear-Ticket unter dem V2-Epic; je Phase Verifikation + E2E-Test durch Bastian, bevor die nächste startet.

## 9. Risiken

- **Laufende LLM-Kosten** ohne geklärtes Kostenmodell → vor Public-Launch klären (Phase 4 blockt Launch).
- **GDPR/Datenschutz** — Nutzerdaten (Lerntexte, Fehler) speichern; DPA mit Auth/DB-Provider, Lösch-Flow.
- **FastAPI-Kopplung an V1-Code** — falls `src/` zu Streamlit-nah ist (st.*-Aufrufe in der Logik?), erst entkoppeln. (Vorprüfen: prompts/tasks/correction/delf/placement sind reine Funktionen — Risiko gering.)
- **Scope-Creep** — V2 ist ein Wochen-Epic; Phasen-Disziplin halten, V1 nicht anfassen.

## 10. Nächste Schritte

1. Dieses Konzept als **Linear-Epic** im Projekt lingua-app anlegen, Phasen als Sub-Tickets.
2. Kostenmodell-Entscheidung (1) terminieren — sie blockt Phase 4, nicht Phase 0–3.
3. Subdomain-Name + Auth/DB-Wahl (§7) festlegen, dann Phase 0 starten.
