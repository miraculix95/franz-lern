# Ticket: UX-Polish-Sprint + Reading-Task + Repo-Rename

**Status:** In Testing (wartet auf E2E-Verifikation durch Bastian)
**Datum:** 2026-04-21
**Pflichtfelder (für Linear):**
- Work-Area: `Feature` + `UX` + `Content & SEO` (About-Page-Refresh)
- Delegierbar: **Medium** — Briefing existiert aus diesem Ticket, aber Beta-Nutzer-Feedback treibt den Scope, das braucht Bastian-Judgement
- Location: **Coding Agent**
- Priority: 2 (High) — blockiert nichts, aber Beta-Tester-Release-ready
- Estimate: 8 Story Points

---

## Kontext

Nach der Gap-Analyse `lingua-app → Virtuelle Sprachschule` (siehe
`research/2026-04-21-gap-analysis-virtuelle-sprachschule.md`) war der größte
kritische Gap "Textverständnis / Reading Comprehension" — der Einstieg in die
DELF-Vorbereitung. Darum entstand dieser Sprint, der entlang echtem
Beta-Tester-Feedback zusätzlich alle UX-Schmerzpunkte für Nicht-Streamlit-User
abgearbeitet hat (verwirrende Ausdrücke, unklare Panel-Aufteilung,
schwer findbare Settings, stale Audio beim Sprachwechsel).

## Ausgeliefert

### 1. Neues Feature: Reading Comprehension (Leseverstehen)
Commit [`a68605c`](https://github.com/miraculix95/lingua-app/commit/a68605c)

- Neues Task-Modul `src/tasks/reading.py` (166 LoC, 9 Tests)
- Vier Text-Quellen: AI-generiert (Slider kurz/mittel/lang) · URL (via
  newspaper3k) · Paste · TXT-Upload
- Strukturierte Fragegenerierung per Function-Call: 5 MC-Fragen (4 Optionen, 1
  korrekt, Rationale) + 3 offene Fragen (mit Referenzantwort für LLM-Bewertung)
- Cognitive-kind-Mix (fact/inference/vocabulary/intent) explizit im Prompt
- MC lokal gescort, offene Antworten via zweitem LLM-Call gegen Referenz mit
  Verdict `CORRECT/PARTIAL/INCORRECT`
- Neue Prompts + Tool-Spec in `src/prompts.py`
- i18n für alle 7 UI-Sprachen

### 2. Repo-Rename: franz-lern → lingua-app
Commit [`158b98a`](https://github.com/miraculix95/lingua-app/commit/158b98a)

- pyproject.toml, README.md, Docstrings in src/app.py/cli.py/config.py
- About-Page-Links (alle 7 Sprachen)
- CLAUDE.md komplett auf aktuellen Stand refactored (war noch "2025 archived
  prototype")
- Legacy-Filenames unter `archive/legacy/` unberührt (no-delete-archive rule)

### 3. UX-Orientierungs-Pass
Commit [`bad28c0`](https://github.com/miraculix95/lingua-app/commit/bad28c0)

- Panel-Überschriften: `⚙️ Konfiguration` (Sidebar) + `🎯 Übungsbereich` (Main)
- `how_it_works`-Banner: "Schritt 1 Sidebar → Schritt 2 hier"
- ~20 `help=`-Tooltips an allen wichtigen Widgets
- Neuer Übungstyp-Expander mit Vorschau aller 10 Typen + Beschreibungen
- Info-Box nach Auswahl mit Beschreibung des gewählten Typs (`desc_*` × 10
  Typen × 7 Sprachen = 70 Strings)
- `practice_intro`-Caption unter dem Heading
- Beta-Tester-Hinweise am Setup-Guide und API-Key-Tooltip
- LinkedIn-Link auf About-Page

### 4. Wording-Schärfung (alle 7 Sprachen)
- `Übung wählen` → `Übungstyp wählen` (konzeptuell ehrlich: es ist ein Typ-Picker)
- Reset-Button: `🏠 Start` → `🔄 Zurücksetzen` (Ambiguität entfernt; "Start"
  wurde als "anfangen" gelesen)
- About-Page: `What's different` → `Highlights – compared to Duolingo/Babbel/
  Busuu` (Vergleich mit was?)
- `Seven registers` → `Seven language registers` ("Was ist ein Register?" war
  echtes Beta-Feedback)
- Faktische Korrekturen: 10 Übungstypen statt 9 (+ Reading), 7 UI-Sprachen
  statt 4

### 5. Light-Mode-Entgrellung
- Streamlit-default #FFFFFF war zu hart → neues `_LIGHT_CSS`: Main #F3F4F6
  (neutral-100), Sidebar #E5E7EB (neutral-200)
- Cards/Expander/Alerts bleiben weiß mit grauem Border → Content poppt gegen Bg

### 6. Autor-Biografie auf About-Seite
Basiert auf scraped [`bastian-brand.com`](https://www.bastian-brand.com/)
(Original archiviert unter `originals/bastian-brand-website.md`).

- Ein-Satz-Profil mit Munich-based, McKinsey-Alumnus, Consultant für
  Datenanalyse/Finanzen/KI-Automatisierung, Kunden in PE/Reise/Versicherung/
  Automotive in Europa
- Zusätzlicher Website-Link neben GitHub + LinkedIn

### 7. Bugfixes

#### 7a. Quiz-Scoring-Bug
Commit [`31006b1`](https://github.com/miraculix95/lingua-app/commit/31006b1)

Das Quiz zeigte die UI-Sprache-Übersetzung als Prompt und fragte nach dem
Zielsprache-Wort — aber `score_answers` verglich die User-Antwort gegen die
UI-Sprache-Übersetzung. Folge: jede korrekte Antwort wurde als falsch
markiert. Fix: Vergleich gegen Dict-Key (Zielsprache-Wort). Tests hatten die
falsche Richtung kodiert und wurden mitkorrigiert.

#### 7b. Cache-Bust bei Sidebar-Änderung
Commit [`bad28c0`](https://github.com/miraculix95/lingua-app/commit/bad28c0)

Nach Sprach- oder Niveau-/Register-/Mentor-Wechsel blieben dictation/quiz/
reading-Session-State-Keys stehen → altes Audio in neuer Sprache etc. Fix:
Cache-Bust bei Sprachwechsel und via `_last_secondary_params`-Tupel bei
Level/Niveau/Mentor.

#### 7c. UI-Sprache ging auf About-Page verloren
Commit [`bad28c0`](https://github.com/miraculix95/lingua-app/commit/bad28c0)

Streamlit garbage-collected den Widget-State-Key `ui_lang_label`, sobald man
auf `/about` war (der Selectbox wird dort nicht gerendert). Folge: About-Page
fiel immer auf Englisch zurück. Fix: Mirror in eine nicht-widget-gebundene
Session-State-Variable `_ui_lang_persisted` auf Main-Page-Render.

## Verifikation

- Tests: **85 passed** (1 pre-existing Failure bei UK-Default-Modell unabhängig
  von dieser Arbeit)
- Lint: keine neuen Findings (Pre-existing Imports in app.py bewusst unberührt
  per Surgical-Changes-Rule)
- E2E-Spot-Check via Playwright: About-Page-Sprachwechsel funktioniert

## Offen (für Follow-up-Tickets)

- **Neue Screenshots für `docs/assets/*.png`** — README referenziert Bilder,
  die die alten Labels/Layouts zeigen (`01-hero-dark.png`, `03-hero-light.png`,
  `04-exercises-menu.png`, `02-coach-dropdown-open.png`). Mit Playwright
  wiederaufnehmen.
- **README-Feature-Matrix updaten** — zeigt noch 9 Übungen, jetzt 10 (+ Reading
  Comprehension).
- **UK/PL/HE-Übersetzungen muttersprachlich prüfen** — meine Übersetzungen
  sind funktional aber nicht nativ-proofed. Bastian plant dies über das
  Beta-Programm zu sammeln.
- **Reading-Task Follow-ups:**
  - PDF-Upload (braucht `mistral-ocr`-Wiring — steht in `tools-catalog.md`)
  - Textlänge frei einstellbar statt 3-Stops-Slider
  - Konfigurierbare Frage-Zahl (MC + offen)
- **Persistenz-ADR:** Retention-Features (SRS, Fehler-Journal, Portfolio) aus
  der Gap-Analyse brauchen eine Architektur-Entscheidung BYOK-rein vs.
  Supabase-Backend. Eigenes Konzept-Ticket mit ADR.

## ADR-Hinweis

Keine Architektur-Entscheidung in diesem Sprint, der BYOK-stateless-Ansatz
wurde bewusst beibehalten. Die Streamlit-Widget-GC-Thematik wurde pragmatisch
per Mirror gelöst statt durch Page-Refactoring — das ist Workaround für eine
bekannte Streamlit-Eigenart, kein architektonisches Gewicht.

---

## Linear-Migration

Beim Einfügen in Linear:
1. Titel: **"UX-Polish-Sprint + Reading-Task + Repo-Rename → lingua-app"**
2. Status: **In Testing** (Bastian testet E2E, dann Done)
3. Related: Research-Ticket mit Gap-Analyse verlinken falls vorhanden
4. Alle Commit-SHAs oben sind klickbar auf GitHub
