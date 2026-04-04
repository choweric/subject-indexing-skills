# AI Agent Skills for LCSH Subject Indexing

A modular pipeline of four AI agent skills that automates subject indexing with Library of Congress Subject Headings (LCSH). Built for [Claude Code](https://claude.ai/code) using its agent skill framework.

**Paper:** Chow, E. H. C. (2026). AI Agent Skills for Library of Congress Subject Headings: A Modular Pipeline Approach to Automated Subject Indexing. 

## What This Does

Subject indexing --- determining what a work is about and expressing that in MARC 21 subject access fields (650, 600, 651, 655, etc.) --- is one of the most time-consuming parts of library cataloging. This project decomposes the process into four sequential skills, each encoding rules from the LC Subject Headings Manual (SHM):

```
Title + Abstract + TOC
        |
        v
  [Skill 1] Conceptual Analysis      -- Wilson, Langridge, Joudrey-Taylor frameworks
        |
        v
  [Skill 2] Quantitative Filtering   -- 20% Rule, Rule of Three (SHM H 180)
        |
        v
  [Skill 3] Authority Validation     -- LCSH/LCGFT/LCNAF lookup
        |
        v
  [Skill 4] MARC 6xx Synthesis       -- H 1075 subfield ordering, 2026 LCGFT practice
        |
        v
  MARC 6xx Fields
```

Each skill produces inspectable intermediate output before passing results to the next stage --- an externalized form of chain-of-thought reasoning.

## Repository Structure

```
.
├── .claude/skills/                  # The four agent skills
│   ├── lcsh-conceptual-analysis/    # Skill 1: aboutness determination
│   │   └── SKILL.md
│   ├── lcsh-quantitative-filtering/ # Skill 2: SHM H 180 rules
│   │   └── SKILL.md
│   ├── lc-authority/                # Skill 3: authority file validation
│   │   ├── SKILL.md
│   │   ├── references/              # Raw authority files (see Data Setup)
│   │   └── scripts/                 # Python search/indexing tools
│   │       ├── tfidf_search.py      # Main search interface
│   │       ├── tfidf_indexer.py     # Build TF-IDF indexes
│   │       ├── lcnaf_api.py         # LCNAF name lookup via LC API
│   │       └── index/               # Pre-built TF-IDF indexes
│   │           ├── subjects/        # ~1.01M LCSH headings
│   │           └── genreforms/      # ~8,600 LCGFT terms
│   └── marc-6xx-synthesizer/        # Skill 4: MARC field construction
│       ├── SKILL.md
│       └── scripts/
│           └── marc_synthesizer.py
├── reference_material/              # LC policy documents (PDFs)
│   ├── H0080.pdf ... H1075.pdf      # SHM instruction sheets
│   ├── J105.pdf ... J110.pdf        # LCGFT manual sections
│   └── form-announcement.pdf        # 2026 $v discontinuation memo
├── results/                         # Pipeline output for 10 test titles
│   ├── 1. Classical and Christian Ideas ... (Rivers, 1994).txt
│   ├── 2. Trauma Room Two (Green, 2015).txt
│   └── ... (10 titles total)
├── sources.csv                      # Test corpus metadata (title, abstract, TOC, etc.)
├── CLAUDE.md                        # Instructions for Claude Code
└── README.md                        # This file
```

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) (CLI, desktop app, or IDE extension)
- Python 3.11+ (standard library only --- no pip packages needed)
- Network connection (only for LCNAF name lookups via LC API)

### Data Setup

Two large files are required for the authority validation skill but exceed GitHub's 100 MB file size limit. Download them from the **[Releases page](https://github.com/choweric/subject-indexing-skills/releases/tag/v1.0-authority-data)** and place them in the correct locations:

| File | Size | Download From | Place In |
|------|------|--------------|----------|
| `subjects.madsrdf.jsonld` | 1.5 GB | [Releases](https://github.com/choweric/subject-indexing-skills/releases/tag/v1.0-authority-data) | `.claude/skills/lc-authority/references/` |
| `documents.ndjson` | 472 MB | [Releases](https://github.com/choweric/subject-indexing-skills/releases/tag/v1.0-authority-data) | `.claude/skills/lc-authority/scripts/index/subjects/` |

Alternatively, you can download the raw LCSH authority file directly from [id.loc.gov/download](https://id.loc.gov/download/) and rebuild the index:

```bash
cd .claude/skills/lc-authority/scripts
python3 tfidf_indexer.py subjects      # Takes ~3-5 minutes
python3 tfidf_indexer.py genreforms    # Takes ~5 seconds (already included in repo)
```

### Running the Pipeline

Open Claude Code in the repository directory. The skills are automatically available. To catalog a book, provide its title, abstract, and table of contents:

```
> Here is a book I'd like to subject index:

  Title: Banker to the poor : micro-lending and the battle against world poverty
  Abstract: The founder of the Grameen Bank relates how he developed the system
  of micro-credit to help eradicate poverty...
  TOC: Number 20 Boxirhat Road, Chittagong -- A Bengali in America -- ...

  Please run the full subject indexing pipeline.
```

Claude Code will invoke the four skills in sequence, producing MARC 6xx fields as output.

You can also invoke individual skills:

```
> /lcsh-conceptual-analysis    # Skill 1 only
> /lcsh-quantitative-filtering # Skill 2 only
> /lc-authority                # Skill 3 only
> /marc-6xx-synthesizer        # Skill 4 only
```

## The Four Skills

### Skill 1: Conceptual Analysis

Identifies what a work is about using established LIS frameworks:
- **Wilson's four methods**: purposive, figure-ground, objective, cohesion
- **Langridge's three questions**: What IS it? What is it ABOUT? What is it FOR?
- **Joudrey-Taylor concept identification**: discipline, topics, names, chronological, form/genre

Produces an aboutness statement and an exhaustive list of candidate concepts. Intentionally over-generates --- filtering is deferred to Skill 2.

### Skill 2: Quantitative Filtering

Applies SHM H 180 rules to determine which concepts merit subject headings:
- **20% Rule**: a topic must comprise ~20% of the work
- **Rule of Three**: 4+ subtopics of a broad subject -> assign only the broad heading
- **Specificity**: headings should match the scope of the work
- **Depth of indexing**: don't assign both a heading and its broader term
- **Predominance ordering** (H 80): primary topic listed first
- **LCGFT routing**: form concepts go to 655 fields, not $v subdivisions (2026 LC practice)

### Skill 3: Authority Validation

Validates each candidate heading against LC authority files:
- **LCSH subjects**: local TF-IDF index (~1.01M headings) with cosine similarity matching
- **LCGFT genre/forms**: local TF-IDF index (~8,600 terms)
- **LCNAF names**: real-time queries to the LC Linked Data Service suggest2 API

Checks authorized forms, resolves UF (Used For) cross-references, verifies geographic subdivision authorization (H 830), and reports BT/NT hierarchical relationships.

### Skill 4: MARC 6xx Synthesis

Constructs properly formatted MARC 21 subject access fields:
- **Subfield order**: $a -> $z -> $x -> $y (per H 1075)
- **Geographic subdivision**: indirect method (H 830)
- **Supported tags**: 600, 610, 611, 630, 650, 651, 655
- **2026 LCGFT practice**: no $v form subdivisions; genre/form expressed exclusively in 655 fields with `$2lcgft`

## SHM Instruction Sheets Implemented

| Document | Scope | Used By |
|----------|-------|---------|
| H 80 | Heading ordering by predominance | Skill 2 |
| H 180 | Assigning and constructing subject headings | Skills 1, 2 |
| H 405 | Establishing entities in name vs. subject authority | Skills 3, 4 |
| H 430 | Name headings as subjects | Skills 3, 4 |
| H 690 | Formulating geographic headings | Skills 3, 4 |
| H 830 | Geographic subdivision (indirect method) | Skills 3, 4 |
| H 860 | Subdivisions further subdivided by place | Skill 4 |
| H 1075 | Subdivisions: types, order, construction | Skill 4 |
| J 105 | MARC coding of LC genre/form terms | Skill 4 |
| J 107 | MARC authority records for genre/form terms | Skill 3 |
| J 110 | Assigning genre/form terms (LCGFT) | Skills 2, 4 |

## Example Output

For *Banker to the Poor* (Yunus, 2003):

```
600 10 $aYunus, Muhammad,$d1940-
610 20 $aGrameen Bank.
650  0 $aMicrofinance.
650  0 $aPoverty.
655  7 $aAutobiographies.$2lcgft
```

Full pipeline transcripts for all 10 test titles are in the `results/` folder.

## Test Corpus

The 10 test titles were sampled from the [Harvard Library Bibliographic Dataset](https://doi.org/10.7910/DVN/I8L0ZZ), an open-access collection of over 12.7 million MARC XML records. Metadata for the test titles is in `sources.csv`. The pipeline's MARC output was compared against the existing LCSH assignments in the Harvard records.

See the [paper](arXiv_paper/paper.pdf) for the full heading-by-heading comparison and analysis.

## Technical Notes

- **No external dependencies.** All Python scripts use the standard library only. No pip packages or virtual environments needed.
- **Stream processing.** The 1.5 GB LCSH authority file is processed line-by-line (NDJSON) to minimize memory usage.
- **Offline-capable.** Subjects and genre/forms use local TF-IDF indexes. Only LCNAF name lookups require a network connection.
- **2026 LC policy.** As of February 2, 2026, LC no longer uses form subdivisions ($v) in subject strings. This pipeline implements the new practice throughout.

## Citation

If you use this work, please cite:

```bibtex
@article{chow2026agent,
  title={AI Agent Skills for Library of Congress Subject Headings: A Modular Pipeline Approach to Automated Subject Indexing},
  author={Chow, Eric H. C.},
  year={2026},
  note={School of Humanities, The University of Hong Kong}
}
```

## License

The LC policy documents in `reference_material/` are works of the U.S. government and are in the public domain. The authority data files available on the Releases page are sourced from [id.loc.gov](https://id.loc.gov/download/) and are freely available. The test corpus metadata is derived from the [Harvard Library Bibliographic Dataset](https://doi.org/10.7910/DVN/I8L0ZZ), released under Harvard Library's Open Metadata Policy.
