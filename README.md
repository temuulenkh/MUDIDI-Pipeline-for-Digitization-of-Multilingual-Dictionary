# MUDIDI

A two-stage framework for multilingual bilingual-dictionary digitization with vision-language models (VLMs) and large language models (LLMs).

This repository implements **MUDIDI** — the benchmark pipeline, evaluation code, example shell scripts, and aggregate results from our work on multilingual dictionary digitization with language models. It compares specialized document VLMs (MinerU 2.5 Pro, PaddleOCR-VL 1.5, GLM-OCR), commercial OCR (Mathpix), and general-purpose LLMs (Gemini 3 Flash, Gemini 3.1 Pro, GPT-5.5, Claude Opus 4.7, Qwen3-VL-235B) on **30 public-domain dictionaries** spanning **diverse writing systems** (Cuneiform, Bengali, Devanagari, Cyrillic, Arabic-based, Han, Khmer, Hebrew, Syriac, Latin, …).

- Stage 1 — **page transcription**: faithful Unicode + markup OCR of dictionary pages.
- Stage 2 — **lexicographic parsing**: transcript → SIL Toolbox MDF (Multi-Dictionary Formatter) records.

The pipeline is modular: each OCR backend produces an `OCRPageResult`; each extraction strategy consumes one and produces a `DictionaryPage` or MDF text. Adding a new model, backend, or strategy is one file.

---

## Pipeline at a glance

```
                    ┌───────────────────────────────────────────────┐
Page image  ───────►│ Stage 1 — transcription (vanilla OCR)         │
Alphabet (opt.)     │  • flat .txt (one line per row, column-major) │
OCR hint (opt.)     │  • <b>/<i> markup preserved                   │
                    └──────────────────────┬────────────────────────┘
                                           │
                                           ▼
                    ┌───────────────────────────────────────────────┐
Intro pages (opt.)  │ Stage 2 — direct MDF (two passes)             │
Toolbox PDF (opt.)  │  Pass 1: field_cheatsheet.json (per dict)     │
                    │  Pass 2: {stem}.mdf.txt (per page)            │
                    └──────────────────────┬────────────────────────┘
                                           ▼
                    eval-flat   (TextEdit, GCER, WER, Markup F1, ReadOrderEdit)
                    eval-stage2 (Record Accuracy, MDF Fields F1, ReadOrderEdit)
```

Detailed module map: [`docs/architecture.md`](docs/architecture.md). Stage 1 methodology: [`docs/stage_1_methodology.md`](docs/stage_1_methodology.md). Stage 2 methodology: [`docs/stage_2_methodology.md`](docs/stage_2_methodology.md).

---

## Quick start

```bash
# Install (uv-managed; do not invoke pip / python directly)
uv sync                  # creates .venv + installs all deps
uv sync --extra paddle   # also install PaddleOCR / paddlepaddle (optional)

# Configure API keys (any subset, depending on which backends you run)
cp .env.example .env
# then fill in:
#   GEMINI_API_KEY=...        # Gemini 3 Flash / 3.1 Pro
#   OPEN_ROUTER_API_KEY=...   # GPT-5.5, Claude Opus 4.7, Qwen3-VL
#   ANTHROPIC_API_KEY=...     # direct Claude (alternative to OpenRouter)
#   OPENAI_API_KEY=...        # direct OpenAI (alternative to OpenRouter)
#   MATHPIX_APP_ID=...        # Mathpix OCR baseline
#   MATHPIX_APP_KEY=...

# Reproduce the paper sweeps
bash examples/stage-1/run_stage1_extraction.sh           # Stage 1 transcription (LLMs + OCR + VLM)
bash examples/stage-2/run_stage2_extraction.sh           # Stage 2 direct MDF (intro × toolbox ablations)
bash examples/evaluation/run_stage1_eval_flat.sh         # Stage 1 evaluation
bash examples/evaluation/run_stage2_eval_mdf.sh          # Stage 2 evaluation
```

Both stage scripts are the canonical entry points used to produce all numbers in the paper. They drive `mudidi run --benchmark` and write per-page outputs into the samples tree under `{lang}/outputs/`.

---

## Repository layout

```
src/mudidi/
    cli/                # argparse entry points (registered as console scripts)
    extraction/         # Extraction strategies — two_stage, vlm_ocr
    llm/                # litellm client, prompts, Pass 1 discovery, Pass 2 direct-MDF
    ocr/                # OCR backends: mathpix, mathpix_convert, paddle, vlm/
    ocr/adapters/       # OCR layout → flat .txt adapter (frozen v1)
    ocr/vlm/            # MinerU / PaddleOCR-VL / GLM-OCR runners + prompts
    schemas/            # Pydantic models (entry, field_cheatsheet, field_map, …)
    evaluation/
        stage1/         # Flat eval: TextEdit, GCER, WER, Markup F1, ReadOrderEdit
        stage2/         # MDF eval: Record Accuracy, MDF Fields F1, ReadOrderEdit
    utils/              # I/O, image, PDF render, MDF helpers, stage-1 input resolution

docs/                   # Architecture + per-stage methodology + evaluation metrics
examples/
    stage-1/            # Stage 1 extraction sweeps (LLM + OCR + VLM)
    stage-2/            # Stage 2 direct MDF + gold cheat-sheet sweeps
    evaluation/         # Evaluation batch wrappers
    helper/             # Sample setup, Mathpix batch, VLM-OCR flatten, etc.
    label-studio/       # Provision Label Studio projects for human post-editing
evaluations/            # Frozen evaluation outputs reported in the paper
scripts/                # Maintenance scripts (sample extraction, gold flatten, validators)
label-studio/           # Label Studio project setup
assets/                 # Sample dictionaries, gold annotations (gitignored — local only)
```

---

## CLI reference

Install the package (`uv sync`), then use:

```bash
# Inference (default): explicit inputs, neighbor-page context, stage-1 → stage-2 chain
uv run mudidi run \
  --pages /path/to/snippets \
  --intro /path/to/introduction \
  --alphabet /path/to/alphabet.txt \
  --output-dir /path/to/out \
  --stage all \
  --model gemini/gemini-3-flash-preview

# Benchmark (paper workflow): samples tree, gold defaults, independent pages
uv run mudidi run --benchmark \
  --samples-dir assets/dictionaries/samples \
  --languages Evenki-Russian \
  --experiment-name gemini31pro_flat_alpha \
  --stage 1 \
  --strategy two_stage \
  --model gemini/gemini-3-flash-preview
```

| Console script           | Purpose                                      |
|--------------------------|----------------------------------------------|
| `mudidi`                 | Main CLI (`run`, `eval stage1`, `eval stage2`) |
| `mudidi-eval-flat`       | Stage 1 flat transcription evaluation        |
| `mudidi-eval-stage2-mdf` | Stage 2 MDF evaluation                       |

Standalone scripts under `scripts/` include `run_mathpix_convert.py` (Mathpix Convert API batch driver; feeds Stage 1 OCR hints).

Pass `--help` to any command for full options.

---

## Stage 1 — transcription

Stage 1 produces a faithful, markup-preserving transcription of each page. Three model families participate, all writing to the same flat `.txt` contract for fair cross-paradigm comparison:

| Family                     | Backend                                       | Prompt configurable | Alphabet hint | OCR hint |
|----------------------------|-----------------------------------------------|:-------------------:|:-------------:|:--------:|
| **General LLM**            | Gemini 3 Flash, Gemini 3.1 Pro, GPT-5.5, Claude Opus 4.7 | yes | yes | yes |
| **Open-weights VLM**       | Qwen3-VL-235B-A22B-Instruct                   | yes                 | yes           | yes      |
| **Specialised document VLM** | MinerU 2.5 Pro, PaddleOCR-VL 1.5             | no                  | —             | —        |
| **Specialised document VLM** | GLM-OCR                                      | yes                 | yes           | —        |
| **Commercial OCR (hint)**  | Mathpix Convert → `--ocr-text` / auto `mathpix/` | no               | —             | yes      |

Entry point: [`examples/stage-1/run_stage1_extraction.sh`](examples/stage-1/run_stage1_extraction.sh).

Key flags exposed by `mudidi-extract`:

- `--strategy two_stage --stage 1 --stage1-mode flat` — flat transcription pass.
- `--strategy vlm_ocr --vlm-model {mineru2.5-pro|paddleocr-vl-1.5|glm-ocr}` — specialised VLM run (uses isolated venvs from `examples/helper/install_models_venv.sh`).
- `--ocr-text <entry>/mathpix` — Mathpix OCR hint (auto-wired in `--samples-dir` mode when `mathpix/` exists; run `scripts/run_mathpix_convert.py` first).
- `--no-alphabet` / `--no-ocr-hint` — ablation knobs.
- `--experiment-name <name>` — independent output slot under `outputs/stage-1/<name>/`. Each slot keeps its own `run_config.json` capturing the full configuration.

Outputs land under the samples tree:

```
{lang}/outputs/stage-1/<experiment>/<page>/<page>_stage1_flat.txt   # one line per visible row
                                          <page>_stage1_raw.json    # structured LLM response
                                          <page>_stage1_input.json  # request snapshot
                          run_config.json                            # full experiment manifest
```

Gold flats live under `{lang}/outputs/stage-1-gold/<page>/<page>_stage1_GOLD_flat.txt`; regenerate after editing column gold with `uv run python scripts/flatten_stage1_gold.py`.

Stage 1 metrics: [`docs/stage_1_evaluation_metrics.md`](docs/stage_1_evaluation_metrics.md).

---

## Stage 2 — direct MDF

Stage 2 turns a gold (or predicted) Stage-1 transcript into Toolbox **MDF** lexicon records. The pipeline runs in two passes:

1. **Pass 1 — field discovery** (once per dictionary): the LLM reads the dictionary introduction and one sample page and emits a `field_cheatsheet.json` that lists which MDF markers this dictionary uses and how entries are structured. Cached under `outputs/stage-2/<experiment>/field_cheatsheet.json`.
2. **Pass 2 — page extraction** (per page): the LLM copies vernacular and gloss characters verbatim from the Stage-1 transcript and emits blank-line-delimited Toolbox MDF using the markers from the cheat sheet. Image + introduction are used **only** for entry boundaries and marker assignment.

Entry point: [`examples/stage-2/run_stage2_extraction.sh`](examples/stage-2/run_stage2_extraction.sh) — runs the full intro × Toolbox-manual ablation per model on the 10 dictionaries reported in the paper.

Key flags:

- `--prompts-file assets/PROMPT.json` — Stage 1 and Stage 2 LLM prompts (edit during inference; reloads on next call).
- `--no-intro` — withhold the dictionary introduction from both passes.
- `--toolbox-pdf "Pages from ToolboxReferenceManual.pdf"` — attach the SIL Toolbox MDF manual in Pass 2 only.
- `--stage1-input flat|column|auto` — choose the Stage 1 transcript source. The paper uses `--stage1-input flat` against `stage-1-gold/` to isolate parsing from OCR error.
- `--stage2-reasoning {low|medium|high}` — reasoning effort (paper uses `high`).
- `--one-page-per-entry` — limit each language to its lowest-numbered annotated page (used in the paper sweeps).

Outputs:

```
{lang}/outputs/stage-2/<experiment>/<page>/<page>.mdf.txt          # Toolbox MDF
                                          <page>_stage2_raw.txt    # raw LLM response
                                          <page>_stage2_input.json # request snapshot
                                          <page>_usage.json        # token / cost
                                  field_cheatsheet.json             # Pass 1 cache
                                  run_config.json                   # experiment manifest
```

Gold MDF lives under `{lang}/outputs/stage-2-gold/<page>/<page>.mdf.txt`.

Stage 2 metrics: [`docs/stage_2_evaluation_metrics.md`](docs/stage_2_evaluation_metrics.md). JSON / MDF field mapping: [`docs/stage_2_outline.md`](docs/stage_2_outline.md). Full marker reference: [`docs/mdf_field_reference.md`](docs/mdf_field_reference.md).

---

## Dataset

The benchmark covers **30 public-domain bilingual dictionaries** sourced from HathiTrust and spanning Latin, Cyrillic, Greek, Devanagari, Bengali, Gujarati, Gurmukhi, Kannada, Telugu, Hebrew, Syriac, Arabic-based, Khmer, Han + IPA, Kana + Kanji, and Cuneiform scripts. **Stage 1** is evaluated on **3 i.i.d. content pages per dictionary** (90 pages total). **Stage 2** focuses on **10 dictionaries × 1 page** chosen to be representative of formats, descriptive traditions, and target languages (English, Russian, French, Chinese, Turkish).

The curated gold release lives at [`dataset/mudidi/`](dataset/mudidi/) (source pages, Stage 1/2 gold, manifests). See [`dataset/mudidi/README.md`](dataset/mudidi/README.md) for layout and loading instructions.

Per-language sample folders follow:

```
assets/dictionaries/samples/<Source-Target>/
    snippets/                    # page images or PDFs (3 per dictionary)
    introduction/                # intro pages (text, image, or PDF)
    alphabet.txt                 # source-language alphabet list (optional)
    dictionary_languages.yaml    # source/target roles + layout type
    outputs/                     # populated by the pipeline (gitignored locally)
```

The full per-language table (script, language family, region, EGIDS, Joshi class) is reproduced in the paper's Table 1.

Sample-extraction helpers under [`examples/helper/`](examples/helper/) bootstrap a new language from a dictionary PDF + metadata CSV.

---

## Reproducing the paper

| Paper artifact                                          | How to reproduce                                                                                             |
|---------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Table 2** — Stage 1 alphabet ablation (30 dict. agg.) | `bash examples/stage-1/run_stage1_extraction.sh` then `bash examples/evaluation/run_stage1_eval_flat.sh`     |
| **Table 3** — Stage 1 OCR-hint ablation                 | `bash examples/stage-1/run_stage1_per_lang_best_flat_alpha_ocr.sh` then `bash examples/evaluation/run_stage1_eval_ocr_hint.sh` |
| **Table 4** — Stage 2 MDF (intro × manual) aggregate    | `bash examples/stage-2/run_stage2_extraction.sh` then `bash examples/evaluation/run_stage2_eval_mdf.sh`      |
| **Table 5** — Stage 2 gold cheat-sheet diagnostic       | `bash examples/stage-2/run_stage2_gold_cheatsheet.sh` then `bash examples/evaluation/run_stage2_eval_gold_cheat_sheet.sh` |
| **Tables 6–11** — Per-dictionary Stage 1 breakdown      | Same as Table 2; per-dictionary CSVs are written under `evaluations/stage1_flat_eval/<experiment>/`          |
| **Table 12** — Per-dictionary Stage 2 breakdown         | Same as Table 4; per-dictionary rows live in `evaluations/stage2_mdf_eval/stage2_mdf_eval_summary.csv`       |

Frozen evaluation outputs that back the published tables are committed under [`evaluations/`](evaluations/) for direct inspection.

Human post-editing of silver-standard transcripts was driven by Label Studio; see [`examples/label-studio/`](examples/label-studio/) and [`label-studio/setup.py`](label-studio/setup.py).

---

## Documentation map

| Doc                                                                          | Topic                                                                  |
|------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`docs/architecture.md`](docs/architecture.md)                               | Module-by-module breakdown and data-flow diagrams                      |
| [`docs/stage_1_outline.md`](docs/stage_1_outline.md)                         | Stage 1 quick reference (tracks, file layout, versioning)              |
| [`docs/stage_1_methodology.md`](docs/stage_1_methodology.md)                 | Full Stage 1 pipeline: LLM flat, VLM-OCR adapter, typography normalise |
| [`docs/stage_1_evaluation_metrics.md`](docs/stage_1_evaluation_metrics.md)   | TextEdit, GCER, WER, Markup F1, ReadOrderEdit definitions              |
| [`docs/stage_2_outline.md`](docs/stage_2_outline.md)                         | Direct MDF + legacy JSON/TSV mapping                                   |
| [`docs/stage_2_methodology.md`](docs/stage_2_methodology.md)                 | Pass 1 + Pass 2 design, prompts, experiment slots                      |
| [`docs/stage_2_evaluation_metrics.md`](docs/stage_2_evaluation_metrics.md)   | Record Accuracy, MDF Fields F1, ReadOrderEdit definitions              |
| [`docs/mdf_field_reference.md`](docs/mdf_field_reference.md)                 | Full SIL Toolbox MDF marker reference                                  |
| [`docs/evaluation_metrics.md`](docs/evaluation_metrics.md)                   | Overview of both evaluation tracks                                     |
| [`docs/uv.md`](docs/uv.md)                                                   | uv cheat sheet                                                         |

---

## Tooling notes

- The project uses [`uv`](https://docs.astral.sh/uv/). Never invoke `pip` or run `python` directly — always go through `uv run` (registered console scripts only resolve when launched by uv).
- LLM calls are routed through `litellm`. Provider keys are resolved by substring of the model string (`gemini` → `GEMINI_API_KEY`, `claude` → `ANTHROPIC_API_KEY` or OpenRouter, etc.). Model-family quirks are centralised in [`src/mudidi/llm/client.py`](src/mudidi/llm/client.py).
- Specialised VLMs run in isolated venvs (`.venv-mineru-vllm`, `.venv-paddleocr`, `.venv-glmocr`) provisioned by [`examples/helper/install_models_venv.sh`](examples/helper/install_models_venv.sh).
- `assets/` is gitignored — sample dictionaries, gold labels, and runtime outputs are local-only.
- Generated LaTeX tables under `examples/evaluation/*.tex` are gitignored; regenerate via the Python generators in the same folder.

---

## Citation

If you use this benchmark or code, please cite the paper. The citation block below is a placeholder and will be updated once the paper is published.

```bibtex
@inproceedings{mudidi2026,
  title  = {MUDIDI: A Two-Stage Framework for Multilingual Dictionary Digitization with Language Models},
  author = {Anonymous},
  year   = {2026},
  note   = {Under review}
}
```
