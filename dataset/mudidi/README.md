---
language:
- mul
license: cc-by-4.0
task_categories:
- image-to-text
- text-generation
tags:
- dictionary-digitization
- ocr
- multilingual
- mdf
- mudidi
- lexicography
size_categories:
- n<1K
dataset_info:
- config_name: stage1
  features:
  - name: page_id
    dtype: string
  - name: dictionary_id
    dtype: string
  - name: page_number
    dtype: int32
  - name: image_path
    dtype: string
  - name: alphabet_path
    dtype: string
  - name: stage1_gold_tsv
    dtype: string
  - name: stage1_gold_flat
    dtype: string
  - name: stage2_gold_mdf
    dtype: string
  splits:
  - name: evaluation
    num_examples: 85
- config_name: stage2
  features:
  - name: page_id
    dtype: string
  - name: dictionary_id
    dtype: string
  - name: stage2_gold_mdf
    dtype: string
  splits:
  - name: evaluation
    num_examples: 10
---

# MUDIDI Dataset

Gold annotations and source pages for **MUDIDI**, a two-stage benchmark for multilingual bilingual-dictionary digitization.

## Dataset summary

| Property | Value |
| --- | --- |
| Dictionaries | 30 public-domain bilingual dictionaries |
| Stage 1 gold pages | 85 annotated pages across 30 dictionaries (27 complete at 3 pages; Yiddish-English 1, Georgian-Russian 1, Japanese-English 2) |
| Stage 1 snippet pages | 90 source images (3 per dictionary; includes pages without gold yet) |
| Stage 2 pages | 10 (1 representative page per Stage 2 subset dictionary) |
| Writing systems | Latin, Cyrillic, Greek, Devanagari, Bengali, Gujarati, Gurmukhi, Telugu, Hebrew, Syriac, Arabic-based, Khmer, Han, Kana, Cuneiform, IPA, and more |
| Splits | **None** — evaluation benchmark only (no train/test split) |
| Version | v1.0.0 |

## Folder layout

Each dictionary lives under `dictionaries/<Source-Target>/` with human-readable Title Case subfolders:

| Folder | Contents | Format |
| --- | --- | --- |
| **Introduction** | Dictionary preface / usage notes used for Stage 2 field discovery | PDF or image (`page_<N>.pdf`, `.png`, …) |
| **Alphabet list** | Source-language character inventory (optional hint for Stage 1) | `alphabet.txt` — one character per line |
| **Dictionary pages** | Three sampled dictionary entry pages | PDF or image (`page_<N>.pdf`, …) |
| **Stage 1 Gold OCR** | Human column-aligned gold + derived flat transcript | `page_<N>_stage1_GOLD.tsv`, `page_<N>_stage1_GOLD_flat.txt` |
| **Stage 2 Gold Cheat Sheet** | Human MDF marker schema (10 dicts only) | `field_cheatsheet.json` |
| **Stage 2 MDF file** | Human Toolbox MDF records (10 dicts only) | `page_<N>.mdf.txt` |

Shared reference material:

| Path | Contents |
| --- | --- |
| `references/MDF Guidelines/Pages from ToolboxReferenceManual.pdf` | SIL Toolbox MDF manual excerpt used in Stage 2 Pass 2 |
| `manifest/dictionaries.jsonl` | One metadata record per dictionary |
| `manifest/pages.jsonl` | One record per Stage 1 evaluation page |
| `manifest/version.json` | Build provenance (source commit, version) |
| `manifest/checksums.sha256` | SHA256 integrity checksums |

Each dictionary also includes `dictionary_languages.yaml` with source/target language codes, writing system, and HathiTrust archive ID.

## Stage 1 gold format

- **`page_<N>_stage1_GOLD.tsv`** — column-aligned human annotation (primary gold).
- **`page_<N>_stage1_GOLD_flat.txt`** — derived flat transcript: one line per visible row, column-major reading order, with `<b>` / `<i>` markup preserved.

See [docs/stage_1_methodology.md](../docs/stage_1_methodology.md) for annotation conventions.

## Stage 2 gold format

Stage 2 gold is available for **10 dictionaries** only:

- Evenki-Russian, Chukchi-Russian, Nahuatl-French, Na-English-Chinese-French, Kashmiri-English, Tiri-English, Greek-English, Efik-English, Circassian-English-Turkish, Iñupiatun Eskimo-English

- **`field_cheatsheet.json`** — maps dictionary-specific MDF markers to entry structure rules (Pass 1 gold).
- **`page_<N>.mdf.txt`** — blank-line-delimited SIL Toolbox MDF records (Pass 2 gold).

See [docs/stage_2_methodology.md](../docs/stage_2_methodology.md).

## Loading the dataset

### Browse files directly

Clone this repository and read `manifest/pages.jsonl` for paths to images and gold files.

### Programmatic access

```python
import json
from pathlib import Path

root = Path("dataset/mudidi")  # or HF cache path

pages = []
with open(root / "manifest/pages.jsonl") as f:
    for line in f:
        pages.append(json.loads(line))

# Stage 1 evaluation set (85 annotated pages)
stage1 = pages

# Stage 2 evaluation subset (10 pages with MDF gold)
stage2 = [p for p in pages if p["stage2_gold_mdf"]]
```

## Known limitations

- Stage 2 gold covers 10 of 30 dictionaries; do not assume MDF gold for all languages.
- Stage 1 gold is incomplete for Yiddish-English (1/3 pages), Georgian-Russian (1/3), and Japanese-English (2/3). All snippet images are included; only annotated pages appear in `manifest/pages.jsonl`.
- Some dictionaries have sparse or missing introduction pages in the source scan.
- Source PDFs are public-domain scans; typography and scan quality vary.

## Licensing

- **Annotations** (gold TSV, flat transcripts, MDF, cheat sheets, alphabet lists): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Source page images**: derived from public-domain HathiTrust volumes

See `LICENSE` for details.

## Citation

```bibtex
@misc{mudidi_v1,
  title        = {{MUDIDI: Multilingual Dictionary Digitization Benchmark}},
  author       = {{MUDIDI Authors}},
  year         = {2026},
  version      = {v1.0.0},
  howpublished = {\url{https://huggingface.co/datasets/ORG/mudidi}}
}
```

See `CITATION.bib` for the full bibliography.