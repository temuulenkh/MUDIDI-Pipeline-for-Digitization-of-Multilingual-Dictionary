# MUDIDI

Digitize scanned bilingual dictionary pages into structured lexicon records using LLMs.

MUDIDI runs a two-stage pipeline:

1. **Stage 1 — transcription** — faithful OCR of each page (Unicode, diacritics, bold/italic markup).
2. **Stage 2 — MDF export** — parse the transcript into [SIL Toolbox MDF](https://software.sil.org/toolbox/) records.

This README focuses on **running the pipeline on a new dictionary**. Benchmark and paper-reproduction instructions are at the bottom.

---

## Install

```bash
git clone <repo-url> && cd MUDIDI
uv sync
cp .env.example .env   # add at least one LLM provider key (see below)
```

After `uv sync`, the `mudidi` command is installed in the project virtualenv. Use either:

```bash
uv run mudidi run --help          # recommended — no need to activate the venv
# or:
source .venv/bin/activate
mudidi run --help
```

### API keys (`.env`)

| Key | Used for |
|-----|----------|
| `GEMINI_API_KEY` | Gemini models (`gemini/...`) |
| `OPEN_ROUTER_API_KEY` | GPT, Claude, Qwen via OpenRouter (`openrouter/...`) |
| `MATHPIX_APP_ID` / `MATHPIX_APP_KEY` | Optional OCR hints via Mathpix Convert |

Models are routed through [litellm](https://github.com/BerriAI/litellm). The model string selects the provider (e.g. `gemini/gemini-3-flash-preview`, `openrouter/openai/gpt-5.5`).

---

## Prepare your dictionary folder

You can supply pages in either of two ways:

### Option A — snippets directory (recommended for large jobs)

Place inputs in a working directory (layout is flexible; paths are passed on the CLI):

```
my-dictionary/
    snippets/          # required — page images or PDFs (page_1.png, page_2.pdf, …)
    introduction/      # optional — front-matter images/PDFs for Stage 2
    alphabet.txt       # optional — source-script character inventory
    mathpix/           # optional — OCR hint files from Mathpix Convert (.md per page)
```

**`snippets/`** — one file per dictionary page. Supported: `.png`, `.jpg`, `.jpeg`, `.webp`, `.pdf`. Pages are processed in numeric order (`page_1`, `page_2`, …, `page_10`).

**`introduction/`** — helps Stage 2 learn abbreviations, entry structure, and which MDF markers the dictionary uses.

**`alphabet.txt`** — character list or legend for the vernacular script. Improves Stage 1 accuracy on rare glyphs.

**`mathpix/`** — optional OCR hints. Generate with:

```bash
uv run python scripts/run_mathpix_convert.py --samples-dir my-dictionary
```

(requires Mathpix credentials; writes `{stem}.md` + `{stem}.lines.json` under `mathpix/`)

### Option B — single source PDF

Pass the full scanned dictionary PDF on `--pages` and list which **1-based PDF page numbers** to process. Dictionary entries and introduction can both come from the same file — use `--dict-pages` for entry pages and `--intro-pages` for front matter. MUDIDI splits each page internally with **pdftk** (must be installed and on `PATH`).

| Flag | Required | Page spec examples |
|------|----------|-------------------|
| `--pages dictionary.pdf` | yes | path to the scan |
| `--dict-pages` | yes | `97-123`, `1,3,5`, `97-123, 179-182` |
| `--intro-pages` | no | `1-5`, `1,2,4` (same PDF as `--pages`) |

Do **not** pass `--intro` when using a PDF — introduction pages are selected with `--intro-pages` from the same file.

Split pages are cached under `{output_dir}/.rendered_snippets/split/` (dictionary) and `{output_dir}/.rendered_intro/split/` (introduction) as `page_{N}.pdf`. Re-runs reuse cached splits unless you pass `--overwrite`.

**pdftk install:** `apt install pdftk-java`, `brew install pdftk-java`, or your distro’s equivalent.

---

## Quick start — full pipeline

Run Stage 1 and Stage 2 in one command. Stage 2 automatically reads Stage 1 output from the same run.

### From a snippets directory

```bash
uv run mudidi run \
  --pages my-dictionary/snippets \
  --intro my-dictionary/introduction \
  --alphabet my-dictionary/alphabet.txt \
  --output-dir my-dictionary/output \
  --stage all \
  --strategy two_stage \
  --stage1-mode flat \
  --model gemini/gemini-3-flash-preview \
  --stage2-reasoning high
```

### From a single PDF

Process dictionary pages 97–123 and introduction pages 1–5 from one scan:

```bash
uv run mudidi run \
  --pages scans/evenki-russian.pdf \
  --dict-pages 97-123 \
  --intro-pages 1-5 \
  --alphabet my-dictionary/alphabet.txt \
  --output-dir my-dictionary/output \
  --stage all \
  --strategy two_stage \
  --stage1-mode flat \
  --model gemini/gemini-3-flash-preview
```

Pick non-contiguous pages with comma lists:

```bash
uv run mudidi run \
  --pages scans/my-dict.pdf \
  --dict-pages 19,83,162 \
  --output-dir my-dictionary/output \
  --stage 1 \
  --stage1-mode flat \
  --model gemini/gemini-3-flash-preview
```

### Stage 1 only

```bash
uv run mudidi run \
  --pages my-dictionary/snippets \
  --alphabet my-dictionary/alphabet.txt \
  --output-dir my-dictionary/output \
  --stage 1 \
  --strategy two_stage \
  --stage1-mode flat \
  --model gemini/gemini-3-flash-preview
```

### Stage 2 only (reuse existing Stage 1 output)

```bash
uv run mudidi run \
  --pages my-dictionary/snippets \
  --intro my-dictionary/introduction \
  --output-dir my-dictionary/output \
  --stage 2 \
  --strategy two_stage \
  --stage1-source predictions \
  --model gemini/gemini-3-flash-preview
```

Stage 2 reads `{output_dir}/stage-1/{page}/{page}_stage1_flat.txt` by default in inference mode.

---

## What you get — output layout

All artifacts land under `--output-dir`:

```
output/
├── field_cheatsheet.json          # Pass 1: MDF marker cheat sheet (once per dictionary)
├── stage-1/
│   └── page_1/
│       ├── page_1_stage1_flat.txt     # Stage 1 transcript (one line per visible row)
│       ├── page_1_stage1_raw.json     # raw LLM structured response
│       └── page_1_stage1_input.json   # request snapshot (for debugging)
└── stage-2/
    └── page_1/
        ├── page_1.mdf.txt             # Toolbox MDF records for this page
        ├── page_1_stage2_raw.txt      # raw LLM MDF response
        ├── page_1_stage2_input.json   # request snapshot
        └── page_1_usage.json          # token counts / estimated cost
```

Re-running the same command **skips pages that already have output** (resume). Pass `--overwrite` to force re-processing.

---

## CLI commands

| Command | Purpose |
|---------|---------|
| `mudidi run` | Run Stage 1, Stage 2, or both on your dictionary |
| `mudidi eval stage1` | Evaluate Stage 1 against gold transcripts (benchmark) |
| `mudidi eval stage2` | Evaluate Stage 2 MDF against gold (benchmark) |
| `mudidi-eval-flat` | Same as `mudidi eval stage1` (standalone script) |
| `mudidi-eval-stage2-mdf` | Same as `mudidi eval stage2` (standalone script) |

Get full flag lists:

```bash
uv run mudidi run --help
```

Model, strategy, and tuning flags (e.g. `--model`, `--stage1-mode`, `--overwrite`) are passed on the same command line — they are forwarded automatically:

```bash
uv run mudidi run \
  --pages my-dictionary/snippets \
  --output-dir my-dictionary/output \
  --model openrouter/openai/gpt-5.5 \
  --stage1-mode flat \
  --overwrite
```

---

## `mudidi run` arguments

### Required (inference mode)

| Flag | Description |
|------|-------------|
| `--pages PATH` | Snippets directory **or** a single source PDF |
| `--output-dir PATH` | Where to write `stage-1/` and `stage-2/` results |
| `--dict-pages SPEC` | **Required when `--pages` is a PDF.** 1-based dictionary page numbers: `1-10`, `1,3,5`, or `97-123, 179-182` |

### Common optional flags

| Flag | Default | Description |
|------|---------|-------------|
| `--stage {1,2,all}` | `all` | Run transcription only, MDF only, or both |
| `--intro PATH` | — | Introduction directory or text/image file (snippets-directory mode only) |
| `--intro-pages SPEC` | — | When `--pages` is a PDF: intro pages from the **same PDF** (same syntax as `--dict-pages`) |
| `--alphabet PATH` | — | Alphabet file (`.txt`/`.md`) or image |
| `--ocr-text PATH` | — | Directory of OCR hint files (`.md`/`.docx`/`.txt`), matched by page stem |
| `--prompts-file PATH` | bundled `PROMPT.json` | Custom prompts; edits reload on next LLM call |
| `--cheatsheet-page STEM` | first page | Which page Pass 1 uses for field discovery |
| `--stage1-source {gold,predictions}` | `predictions` | Stage 2 input source (inference uses predictions) |

### Model and strategy flags

Pass these on the same command line (forwarded to the extraction engine):

| Flag | Default | Description |
|------|---------|-------------|
| `--strategy` | `two_stage` | `two_stage` (LLM) or `vlm_ocr` (specialised VLM backends) |
| `--model` | `gemini/gemini-3-flash-preview` | Stage 1 model (litellm string) |
| `--structure-model` | same as `--model` | Stage 2 model |
| `--stage1-mode {column,flat}` | `column` | Stage 1 output format; use **`flat`** for new dictionaries |
| `--stage1-reasoning {none,low,medium,high}` | `low` | Stage 1 reasoning effort |
| `--stage2-reasoning {low,medium,high}` | `low` | Stage 2 reasoning effort |
| `--toolbox-pdf PATH` | — | Attach SIL Toolbox MDF manual in Pass 2 |
| `--stage-1-guides PATH` | — | Extra rules appended to Stage 1 prompt |
| `--stage-2-guides PATH` | — | Extra rules appended to Stage 2 prompt |
| `--overwrite` | off | Re-process pages even if output exists |
| `--limit N` | — | Process at most N pages |
| `--no-alphabet` | off | Skip alphabet hint |
| `--no-ocr-hint` | off | Skip OCR hint |
| `--no-intro` | off | Skip introduction in Stage 2 |

### Inference-specific behaviour

- **Neighbor page context** — in inference mode, each page receives previous/next page images (and prior transcripts when available) so the model can handle entries that span page breaks. Output still belongs to the current page only.
- **Stage chaining** — with `--stage all`, Stage 2 reads Stage 1 predictions from `--output-dir` automatically.
- **Prompts** — inference uses `*_inference` prompt variants in `assets/PROMPT.json` (editable via `--prompts-file`).

---

## Pipeline overview

```
snippets/ + alphabet + OCR hints
        │
        ▼
┌─────────────────────────┐
│ Stage 1 — transcription │  →  stage-1/{page}/{page}_stage1_flat.txt
└───────────┬─────────────┘
            │
 intro + Pass 1 cheat sheet
            ▼
┌─────────────────────────┐
│ Stage 2 — MDF export    │  →  stage-2/{page}/{page}.mdf.txt
│  Pass 1: field map      │      field_cheatsheet.json
│  Pass 2: per-page MDF   │
└─────────────────────────┘
```

**Stage 1** transcribes every visible line on the page image. Use `--stage1-mode flat` for the standard one-line-per-row format.

**Stage 2 Pass 1** runs once: reads the introduction + one sample page and writes `field_cheatsheet.json` (which MDF markers this dictionary uses).

**Stage 2 Pass 2** runs per page: copies characters verbatim from the Stage 1 transcript and assigns MDF markers using the cheat sheet.

Further detail: [`docs/stage_1_methodology.md`](docs/stage_1_methodology.md), [`docs/stage_2_methodology.md`](docs/stage_2_methodology.md).

---

## Customising prompts

Prompts live in `assets/PROMPT.json` (also bundled inside the installed package). Each entry has `prompt` text and a `variables` list documenting placeholders like `{alphabet_text}` and `{ocr_hint}`.

```bash
cp assets/PROMPT.json my-prompts.json
# edit my-prompts.json …
uv run mudidi run \
  --pages my-dictionary/snippets \
  --output-dir my-dictionary/output \
  --prompts-file my-prompts.json \
  --strategy two_stage \
  --stage1-mode flat
```

Changes are picked up on the next LLM call (mtime-based reload).

---

## Tooling notes

- Use **`uv sync`** and **`uv run`** (or activate `.venv` first). This ensures dependencies and console scripts resolve correctly.
- LLM calls go through litellm; provider keys are inferred from the model string.
- **`pdftk`** is required when `--pages` is a PDF file (page splitting). Snippets-directory workflows do not need it.
- Specialised VLM backends (`--strategy vlm_ocr`) require separate model venvs — see [`examples/helper/install_models_venv.sh`](examples/helper/install_models_venv.sh). Most new-dictionary workflows use `--strategy two_stage` with a general LLM.

---

## Benchmark mode (paper / evaluation)

The sections below are for reproducing the MUDIDI benchmark on the 30-dictionary evaluation set — not needed for digitizing a new dictionary.

### Benchmark vs inference

| | Inference (default) | Benchmark (`--benchmark`) |
|--|---------------------|---------------------------|
| Purpose | Digitize your dictionary | Evaluate models against gold labels |
| Inputs | `--pages`, `--output-dir` | `--samples-dir` + samples tree layout |
| Stage 2 input | Stage 1 predictions | Gold transcripts (default) |
| Page context | Previous/next pages | Independent pages |
| Output layout | `{output_dir}/stage-1/`, `stage-2/` | `{lang}/outputs/stage-1/{experiment}/` |

### Benchmark quick start

```bash
uv run mudidi run --benchmark \
  --samples-dir assets/dictionaries/samples \
  --languages Evenki-Russian \
  --experiment-name gemini31pro_flat_alpha \
  --stage 1 \
  --strategy two_stage \
  --stage1-mode flat \
  --model gemini/gemini-3-flash-preview
```

Paper sweeps:

```bash
bash examples/stage-1/run_stage1_extraction.sh
bash examples/stage-2/run_stage2_extraction.sh
bash examples/evaluation/run_stage1_eval_flat.sh
bash examples/evaluation/run_stage2_eval_mdf.sh
```

### Benchmark sample layout

```
assets/dictionaries/samples/<Source-Target>/
    snippets/
    introduction/
    alphabet.txt
    dictionary_languages.yaml
    outputs/                     # populated by the pipeline
        stage-1-gold/            # human gold (evaluation only)
        stage-2-gold/
        stage-1/<experiment>/
        stage-2/<experiment>/
```

### Dataset

The benchmark covers **30 public-domain bilingual dictionaries**. Gold data and manifests: [`dataset/mudidi/`](dataset/mudidi/). See [`dataset/mudidi/README.md`](dataset/mudidi/README.md).

### Reproducing paper tables

| Paper artifact | Command |
|----------------|---------|
| Table 2 — Stage 1 alphabet ablation | `examples/stage-1/run_stage1_extraction.sh` + `examples/evaluation/run_stage1_eval_flat.sh` |
| Table 3 — Stage 1 OCR-hint ablation | `examples/stage-1/run_stage1_per_lang_best_flat_alpha_ocr.sh` + eval script |
| Table 4 — Stage 2 MDF aggregate | `examples/stage-2/run_stage2_extraction.sh` + `examples/evaluation/run_stage2_eval_mdf.sh` |
| Table 5 — Stage 2 gold cheat-sheet | `examples/stage-2/run_stage2_gold_cheatsheet.sh` + eval script |

Frozen evaluation outputs: [`evaluations/`](evaluations/).

---

## Documentation

| Doc | Topic |
|-----|-------|
| [`docs/architecture.md`](docs/architecture.md) | Module map and data flow |
| [`docs/stage_1_methodology.md`](docs/stage_1_methodology.md) | Stage 1 pipeline detail |
| [`docs/stage_2_methodology.md`](docs/stage_2_methodology.md) | Pass 1 + Pass 2 design |
| [`docs/mdf_field_reference.md`](docs/mdf_field_reference.md) | SIL Toolbox MDF markers |
| [`docs/stage_1_evaluation_metrics.md`](docs/stage_1_evaluation_metrics.md) | Benchmark metrics (Stage 1) |
| [`docs/stage_2_evaluation_metrics.md`](docs/stage_2_evaluation_metrics.md) | Benchmark metrics (Stage 2) |

---

## Citation

```bibtex
@inproceedings{mudidi2026,
  title  = {MUDIDI: A Two-Stage Framework for Multilingual Dictionary Digitization with Language Models},
  author = {Anonymous},
  year   = {2026},
  note   = {Under review}
}
```
