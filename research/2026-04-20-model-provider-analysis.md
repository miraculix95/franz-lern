# Model & Provider Analysis for Correction Use-Case

**Date:** 2026-04-20
**Context:** TES-539 E2E-Test zeigte, dass `gpt-4o-mini` französische Grammatik halluziniert (markierte korrektes "personnes attendent" als Fehler). Prompt-Fix wurde gepusht (`db0229d`), aber Modell-Wechsel steht zur Diskussion.

**Use-Case-Profil:**
- Chat completions, ~500 input / ~300 output Tokens pro Call
- Keine Tool-Calls, kein Multimodal, kein Streaming-Bedarf
- Französische Grammatik-Korrektur auf Native-Speaker-Niveau
- Interaktive UX → Speed ist spürbar wichtig
- BYOK-App → Kosten bezahlt der User, aber niedrig = mehr Nutzung

**Method:** Live-Scrape OpenRouter API (342 Modelle) + Groq-Pricing-Page. Keine Training-Daten-Ratung. Verifiziert 2026-04-20.

---

## Pricing-Landschaft (relevante Modelle, OpenRouter)

| Modell | In $/M | Out $/M | Cost pro 500+300-Correction | Ctx |
|---|---:|---:|---:|---:|
| **mistralai/mistral-small-3.2-24b-instruct** | 0.075 | 0.20 | **$0.00010** | 128k |
| mistralai/ministral-8b-2512 | 0.15 | 0.15 | $0.00012 | 262k |
| openai/gpt-4.1-nano | 0.10 | 0.40 | $0.00017 | 1M |
| openai/gpt-4o-mini (aktuell) | 0.15 | 0.60 | $0.00026 | 128k |
| google/gemini-2.5-flash-lite | 0.10 | 0.40 | $0.00017 | 1M |
| meta-llama/llama-3.3-70b-instruct | 0.12 | 0.38 | $0.00017 | 131k |
| deepseek/deepseek-v3.2 | 0.259 | 0.42 | $0.00025 | 164k |
| mistralai/mistral-medium-3.1 | 0.40 | 2.00 | $0.00080 | 131k |
| openai/gpt-4.1-mini | 0.40 | 1.60 | $0.00068 | 1M |
| **mistralai/mistral-large-2512** | 0.50 | 1.50 | $0.00070 | 262k |
| google/gemini-2.5-flash | 0.30 | 2.50 | $0.00090 | 1M |
| **anthropic/claude-haiku-4.5** | 1.00 | 5.00 | $0.00200 | 200k |
| openai/gpt-4o | 2.50 | 10.00 | $0.00425 | 128k |
| anthropic/claude-sonnet-4.6 | 3.00 | 15.00 | $0.00600 | 1M |

## Groq (direkt, nicht via OpenRouter)

Groq ist ein Inferenz-Anbieter der spezialisiertes Hardware (LPUs) nutzt — extreme Speed. Nur Open-Source-Modelle.

| Modell | In $/M | Out $/M | Speed (tps) | Ctx |
|---|---:|---:|---:|---:|
| llama-3.1-8b-instant | 0.05 | 0.08 | **840 tps** | 128k |
| gpt-oss-20b-128k | 0.075 | 0.30 | 1000 tps | 128k |
| llama-4-scout-17bx16e | 0.11 | 0.34 | 594 tps | 128k |
| gpt-oss-120b-128k | 0.15 | 0.60 | 500 tps | 128k |
| qwen3-32b-131k | 0.29 | 0.59 | 662 tps | 131k |
| llama-3.3-70b-versatile | 0.59 | 0.79 | 394 tps | 128k |

Zum Vergleich: typische OpenRouter-Response ~30-80 tps. Groq ist **~5-10× schneller** bei gleichem Modell.

---

## Multilingualer Use-Case

Die App unterstützt **5 Sprachen** mit sehr unterschiedlichen Anforderungen:

| Sprache | Familie | Tokenization | Schwierigkeit |
|---|---|---|---|
| Englisch | Germanic | optimal | Low — jedes Modell kann das |
| Französisch | Romance | effizient | Medium — Grammatik-Nuancen wichtig |
| Spanisch | Romance | effizient | Medium — Subjuntivo, Pronomen |
| Deutsch | Germanic | mittelmäßig (Komposita) | Medium — Deklination, Kasus |
| Ukrainisch | Slawisch (Cyrillic) | **teuer** (mehr Tokens/Wort) | **High** — 7-Kasus-System, Aspekt-Paare, weniger Trainingsdaten |

Ukrainisch ist der Stresstest. Modelle mit wenig UK-Training produzieren entweder:
- Halluzinierte Kasus-Endungen
- Falsch-Positive bei perfekten/imperfekten Aspekten
- Schwaches Vokabular außerhalb Alltagswortschatz

**Informierte Qualitäts-Einschätzung pro Sprache** (basiert auf Anbieter-Trainings-Schwerpunkten, Community-Reports, Modell-Architektur — keine offiziellen Benchmarks):

| Modell | EN | FR | ES | DE | UK | Notizen |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Claude Sonnet 4.6 | S | S | S | S | A | Premium-Allrounder |
| Claude Haiku 4.5 | A | A | A | A | A | Solid across the board |
| GPT-4.1 | A | A | A | A | A | OpenAI post-2022 stark auf UK |
| GPT-4.1-mini | A | B | A | A | B | Gut, Ukrainisch merklich schwächer |
| GPT-4.1-nano | B | B | B | B | C | UK-Halluzinationen möglich |
| Mistral Large 3 | A | **S** | A | A | C | FR/Romance stark, UK weak |
| Mistral Medium 3.1 | B | A | A | A | C | Gleiches Pattern |
| Mistral Small 3.2 | B | A | B | B | D | **UK risky** — nicht für UK-Korrektur |
| Gemini 2.5 Flash | B | B | B | B | B | Google indexiert viel UK-Content |
| Gemini 2.5 Flash Lite | B | B | B | B | C | Preis-Wunder, UK okay aber nicht toll |
| gpt-4o-mini (aktuell) | B | **C** | B | B | C | Bewiesen FR-halluzinierend (TES-539) |
| Llama 3.3 70B | A | B | B | B | C | English-first Training |
| DeepSeek V3.2 | A | C | C | C | D | Chinese-English fokussiert |
| Qwen3 | A | C | C | C | D | Gleiches Pattern |

**Legende:** S = native-Speaker-Niveau · A = fast fehlerfrei · B = gelegentlich kleine Fehler · C = systematische Schwächen · D = halluziniert Grammatik

### Was das für die Default-Wahl heißt

Mistral Small 3.2 war in meiner ersten Analyse Top-Pick wegen FR-Qualität. Mit UK im Scope fällt das flach — kleine Mistral-Modelle haben wenig slawisches Training. Genauso Llama.

Die **robust-multilingualen** Kandidaten (alle 5 Sprachen mindestens B):

| Modell | Cost/Correction | Worst-Case-Sprache | Kommentar |
|---|---:|---|---|
| **claude-haiku-4.5** | $0.00200 | UK=A | Premium, sicher |
| **gemini-2.5-flash** | $0.00090 | UK=B | Sweet spot price/quality |
| **gpt-4.1-mini** | $0.00068 | UK=B | OpenAI multilingual neu |
| **gemini-2.5-flash-lite** | $0.00017 | UK=C | Kompromiss-günstig |
| **gpt-4.1-nano** | $0.00017 | UK=C | Gleicher Preis, ähnliche Qualität |

### Ukrainisch-Kostenfaktor

Cyrillic braucht ~1.5-2× mehr Tokens pro Zeichen als Latin. Ein UK-Korrektur-Call mit 500+300 Latin-Tokens äquivalent wäre real ~900+500 UK-Tokens. Cost entsprechend höher — für UK-User lohnt es sich trotzdem nicht Mistral Small zu forcen.

## Speed-Vergleich (spürbar in UX)

Typische Korrektur (~300 Output-Tokens):
- gpt-4o-mini (OpenAI direkt): ~80 tps → **~4 Sekunden**
- Mistral Small via OpenRouter (Mistral-gehostet): ~60 tps → ~5s
- Claude Haiku 4.5 (Anthropic direkt/OpenRouter): ~100 tps → ~3s
- **Llama 3.3 70B auf Groq: 394 tps → unter 1s**
- **gpt-oss-20b auf Groq: 1000 tps → 0.3s**

Groq ist eine andere Kategorie Speed. Aber die Modelle dort sind alle Open-Source (keine Claude/GPT/Mistral-Closed).

---

## Architektur-Implikationen

**OpenRouter:** Ein unified Endpoint, `openai`-SDK-kompatibel. Switch von OpenAI-direct zu OpenRouter ist **eine Zeile**:

```python
client = openai.OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
# model strings ändern: "gpt-4o-mini" → "mistralai/mistral-small-3.2-24b-instruct"
```

Vorteil: User-Model-Wahl im Sidebar trivial — mehr Modelle verfügbar ohne Code-Änderung.
Nachteil: OpenRouter-Markup ~5-10% auf den Provider-Preis (bei Mistral Small praktisch nicht spürbar, bei Claude merklich).

**Groq:** Eigener Endpoint, eigener SDK-Aufruf-Stil (auch OpenAI-kompatibel via `base_url="https://api.groq.com/openai/v1"`). Kann **parallel** zu OpenRouter laufen.

**Litellm:** Ja, existiert noch und ist weiter gut gewartet — aber OpenRouter hat de-facto dasselbe Feature-Set mit weniger Setup (keine lokale Proxy, keine API-Key-Config pro Provider). Für einen BYOK-Consumer-Flow ist OpenRouter praktischer: User hat **einen** Key für Dutzende Modelle.

---

## Empfehlung (revised 2026-04-20 nach UK-Scope-Clarification)

**Wechsel zu OpenRouter, sprach-abhängiger Default:**

- User wählt **FR / ES / DE / EN** als Lern-Sprache → Default `google/gemini-2.5-flash-lite` ($0.00017/Call)
- User wählt **Ukrainisch** → Default wechselt automatisch auf `anthropic/claude-haiku-4.5` ($0.002/Call)

Grund: UK ist slawisch + cyrillisch, kleine Modelle halluzinieren dort Grammatik-Regeln. Haiku ist der günstigste Kandidat mit zuverlässigem UK-Niveau.

### Sidebar-Dropdown (4 Tiers, manuell überschreibbar)

| Tier | Modell | $/Call | Notizen |
|---|---|---:|---|
| 💰 Budget-Default | `google/gemini-2.5-flash-lite` | $0.00017 | Fehlt nur UK-Tiefe |
| ⚖️ Quality-Default (UK-safe) | `anthropic/claude-haiku-4.5` | $0.00200 | Alle 5 Sprachen A-Tier |
| 🚀 Premium (FR/Romance-stark) | `mistralai/mistral-large-2512` | $0.00070 | Günstiger als Haiku, FR=S, UK=C |
| 👑 Best | `anthropic/claude-sonnet-4.6` | $0.00600 | Wenn Geld egal |

Mistral Small 3.2 wurde aus der Default-Rolle gestrichen — zu risky auf UK. Könnte optional als "🇫🇷 Ultra-Budget (nur EU-Sprachen)"-Tier rein, wenn Bastian das will.

Groq: Separate Option für Speed-Experiments (Llama 3.3 70B auf Groq: 394 tps, <1s Response), aber nicht im Default-Flow.

### Warum nicht gpt-4.1-nano als Budget-Default?

Gemini 2.5 Flash Lite und gpt-4.1-nano sind preislich identisch ($0.10/$0.40 per M). Gemini hat marginal besseren Ruf für Romance + UK, gpt-4.1-nano marginal besser für Englisch. Unterschied zu gering — beides akzeptabel. Gemini als Default weil Google multilingual historisch etwas konsistenter trainiert hat.

## Vor-Implementierungs-Test (MUST DO)

Bevor ich das umstelle: Bastian sollte die **gleiche Lückentext-Korrektur** (die gpt-4o-mini verbockt hat) gegen Mistral Small 3.2 testen. Einfachster Weg:

1. Temporär OpenRouter-Key in `.env` setzen (`OPENROUTER_API_KEY`)
2. Ein-Zeilen-Test-Script das die `correct_text()`-Funktion mit Mistral aufruft
3. Gleicher Input → Output vergleichen

Wenn Mistral Small 3.2 genauso halluziniert → Upgrade auf Mistral Medium 3.1 als Default erwägen (noch billiger als Claude Haiku).

---

## Quellen

- **OpenRouter API:** https://openrouter.ai/api/v1/models (scraped 2026-04-20)
- **Groq Pricing:** https://groq.com/pricing (firecrawl'd 2026-04-20)
- **Mistral Blog/Docs:** https://docs.mistral.ai (für Positionierung French-first)

Alle Preise aus Live-API, nicht aus Training-Daten.
