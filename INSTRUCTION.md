# MUDIDI Run Instructions

## 0. Navigate to project directory

```bash
cd /Users/temuulenkh/Documents/github/MUDIDI
```

## 1. Setup

Copy environment variables:
```bash
cp /Users/temuulenkh/Documents/github/agentic-dictionary-extraction/.env /Users/temuulenkh/Documents/github/MUDIDI/.env
```

Sync dependencies:
```bash
cd /Users/temuulenkh/Documents/github/MUDIDI && uv sync
```

## 2. Create dictionary_languages.yaml

```bash
cat > inputs/dictionary_languages.yaml << 'EOF'
layout: bilingual
source:
  language: Carolinian
  code: cal
targets:
  - language: English
    code: en
EOF
```

## 3. Run the pipeline

Place your PDF at `inputs/carolinian_full.pdf`, then:

```bash
uv run mudidi run \
  --pages inputs/carolinian_full.pdf \
  --dict-pages 53-56 \
  --output-dir outputs \
  --intro-pages 19-26 \
  --stage all \
  --model gemini/gemini-3-flash-preview \
  --stage2-reasoning medium \
  --prompts-file assets/PROMPT.json \
  --dictionary-languages inputs/dictionary_languages.yaml
```

## 4. Re-run Stage 2 only (e.g. after editing parse-rules.json)

Use `--parse-rules-file` to skip Pass 1 and use the curated parse-rules.json directly.
Use `--overwrite` to force re-processing pages that already have output.

```bash
uv run mudidi run \
  --pages inputs/carolinian_full.pdf \
  --dict-pages 53-56 \
  --output-dir outputs \
  --intro-pages 19-26 \
  --stage 2 \
  --model gemini/gemini-3-flash-preview \
  --stage2-reasoning medium \
  --prompts-file assets/PROMPT.json \
  --dictionary-languages inputs/dictionary_languages.yaml \
  --parse-rules-file outputs/parse-rules-updated.json \
  --overwrite
```

## 5. Run full dictionary in background (resumable)

Runs in background, survives terminal closure. Skips already-processed pages automatically.

```bash
nohup uv run mudidi run \
  --pages inputs/carolinian_full.pdf \
  --dict-pages 33-491 \
  --output-dir outputs \
  --intro-pages 19-26 \
  --stage all \
  --model gemini/gemini-3-flash-preview \
  --stage2-reasoning high \
  --prompts-file assets/PROMPT.json \
  --dictionary-languages inputs/dictionary_languages.yaml \
  --parse-rules-file outputs/parse-rules-manual.json \
  > outputs/run.log 2>&1 &
```

Monitor progress:
```bash
tail -f outputs/run.log
```

## 6. Convert MDF output to TSV

```bash
uv run dictextractor-mdf-to-tsv \
  --stage2-dir outputs/stage-2 \
  --output outputs/carolinian_combined.tsv
```
