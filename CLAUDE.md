# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Getting Started

This is a specialized LCSH (Library of Congress Subject Headings) cataloging system. When users request help with cataloging books:

1. **Start with conceptual analysis**: Use the lcsh-conceptual-analysis skill to analyze the book's title and description
2. **Apply cataloging rules**: Use lcsh-quantitative-filtering skill to filter concepts based on the 20% rule and Rule of Three
3. **Validate headings**: Use lc-authority skill to check if headings exist in LC authority files (LCSH for subjects, LCGFT for genre/form)
4. **Generate MARC fields**: Use marc-6xx-synthesizer skill to create properly formatted MARC 21 subject access fields

The skills work in sequence - results from one skill are passed to the next in the workflow.

## Repository Architecture

This is a collection of AI skills/tools for Library of Congress Subject Headings (LCSH) cataloging workflows. The system consists of four interconnected Claude skills located in `.claude/skills/`:

1. **lcsh-conceptual-analysis** - Identifies core concepts from titles/abstracts using the Purposive Method
2. **lcsh-quantitative-filtering** - Applies cataloging rules (20% Rule, Rule of Three)
3. **lc-authority** - Validates headings against LC authority files (LCSH subjects, LCGFT genre/forms, LCNAF names) using TF-IDF semantic search
4. **marc-6xx-synthesizer** - Generates properly formatted MARC 21 subject access fields following H 1075 order

Each skill has both a SKILL.md file for Claude integration and a scripts/ folder containing Python implementations.

## Key Development Commands

### Working with Authority Files
```bash
# Test LCSH subject authority checking
cd .claude/skills/lc-authority/scripts
python3 tfidf_search.py "Companion planting"
python3 tfidf_search.py "Vegetable gardening" --top 5

# Test LCGFT genre/form authority checking
python3 tfidf_search.py "Essays" -a genreforms
python3 tfidf_search.py "Documentary films" -a genreforms

# Test LCNAF name authority checking (uses LC API, requires network)
python3 tfidf_search.py "Shakespeare, William" -a names
python3 tfidf_search.py "Library of Congress" -a names

# Check authority status of a specific heading
python3 tfidf_search.py "Tacos" --check
python3 tfidf_search.py "Instructional films" -a genreforms --check

# Build/rebuild authority indexes
python3 tfidf_indexer.py subjects      # LCSH subjects (~3-5 min)
python3 tfidf_indexer.py genreforms    # LCGFT genre/forms (~5 sec)
python3 tfidf_indexer.py --all         # Build all local indexes

# Run MARC field generation tests
cd .claude/skills/marc-6xx-synthesizer/scripts
python3 marc_synthesizer.py
```

## High-Level Architecture

### Modular Pipeline Design
The system implements a sequential workflow:
Input (Title/Abstract) → Concept Analysis → Quantitative Filtering → Authority Validation → MARC Generation → Output

Each module produces data consumed by the next module in the sequence.

### Authority Lookup: Two Methods
- **Subjects and Genre/Forms**: Local TF-IDF index built from NDJSON authority files (`.claude/skills/lc-authority/references/`). The index lives in `scripts/index/{subjects,genreforms}/` with four files: `config.json`, `vocabulary.json`, `idf.json`, `documents.ndjson`.
- **Names (LCNAF)**: LC Linked Data Service suggest2 API (`id.loc.gov/authorities/names/suggest2/`). No local index needed — avoids the 44GB LCNAF download. The client (`lcnaf_api.py`) auto-inverts personal names for prefix matching.

Both methods are accessed through `tfidf_search.py` which routes based on authority type.

### Library of Congress Standards Implementation
The following SHM instruction sheets have been integrated into the skills:
- **H 80**: Heading ordering by predominance → lcsh-quantitative-filtering
- **H 180**: Assigning and constructing subject headings (20% rule, Rule of Three/Four, specificity, depth of indexing, named entities, objectivity, LCGFT) → lcsh-quantitative-filtering, lcsh-conceptual-analysis
- **H 405**: Establishing entities in name vs subject authority file (Group 1/2 classification) → lc-authority, marc-6xx-synthesizer
- **H 430**: Name headings as subjects (validation criteria) → lc-authority
- **H 690**: Formulating geographic headings (jurisdictional vs. non-jurisdictional, BGN/GNIS/GNS sources, English vs. vernacular, name inversion, transliteration, conflicts) → lc-authority, marc-6xx-synthesizer
- **H 830**: Geographic subdivision (indirect method, exceptions for US/UK/Canada, two-level max, qualifier deletion) → lc-authority, marc-6xx-synthesizer
- **H 860**: Subdivisions further subdivided by place → marc-6xx-synthesizer
- **H 1075**: Subdivisions (four types, two basic orders, form→LCGFT transition, reverse reading test) → marc-6xx-synthesizer
- **J 110**: Assigning Genre/Form Terms (general rule, specificity, number of terms, no subdivisions) → lcsh-quantitative-filtering, marc-6xx-synthesizer
- **J 105**: MARC Coding of LC Genre/Form Terms (655 field coding, $3 for parts) → marc-6xx-synthesizer
- **J 107**: MARC Authority Records for LC Genre/Form Terms (155/455/555 structure, gf validation) → lc-authority

## Code Structure and Patterns

### No External Dependencies
All modules use Python standard library only. This design choice enables easy deployment in library environments. Both the indexer and search scripts include an inline Porter Stemmer implementation.

### Stream Processing for Large Files
The 1.5GB LCSH authority file is processed line-by-line (NDJSON format) to minimize memory usage:
```python
# Pattern used across the codebase
with open(authority_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f):
        if line.strip():
            record = json.loads(line)
            # Process single record
```

### Skill Module Pattern
Each Claude skill follows this structure:
- `SKILL.md` - Integration instructions and usage examples (with frontmatter: name, description)
- `scripts/` - Python implementation with command-line interface
- Basic functionality in single file (no complex package structure)

### MARC Field Generation
- **Supported tags**: 600, 610, 611, 630, 650, 651, 655
- **Subfield order (H 1075)**: $a → $z → $x → $y (form now in separate 655 field)
- **Geographic subdivisions**: Use indirect method format "Country -- Locality"
- **Second indicator**: Set to "0" for LCSH headings, "7" for LCGFT

### LCGFT Implementation (2026)
As of February 2, 2026, LC no longer uses form subdivisions ($v) in subject strings. Instead:
- Use **LCGFT** in 655 fields for genre/form
- See H 1075 sec. C.4 for details
- Old records are not retroactively converted

## Important Implementation Notes

### Common Pitfalls to Avoid
1. Don't load entire authority file into memory - it causes memory issues
2. Always check geographic subdivision permissions before adding $z
3. **Do NOT use form subdivisions ($v)** - use LCGFT 655 fields instead
4. When 4+ subtopics exist, assign one general heading (H 180 Rule of Three)
5. Named entities can bypass 20% rule if critical to the work
6. Subdivision order affects meaning - test by reading in reverse order
7. `search_authority.py` is the legacy linear-scan searcher; prefer `tfidf_search.py` for all lookups
8. Names authority requires network access (LC API) while subjects/genreforms are fully offline

### System Requirements
- Python 3 (tested with 3.11)
- No pip packages or virtual environments needed
- Network connection required only for LCNAF name lookups
- Authority files downloaded from https://id.loc.gov/download/ (subjects ~1.5GB, genreForms ~14MB)

### Error Handling Patterns
- Check if authority file exists before searching (FileNotFoundError)
- Handle JSON decode errors when processing corrupted NDJSON lines
- Default to "Not authorized" for geographic subdivision if unclear
- LCNAF API client handles network errors and JSON parse failures gracefully

## Working Examples

### Complete Cataloging Workflow
```python
# 1. Conceptual analysis (from skill documentation)
# Input: "Carrots Love Tomatoes: Secrets of Companion Planting"
# Output: Topics identified: ["Companion planting", "Vegetable gardening", "Organic gardening"]

# 2. Quantitative filtering
# Apply 20% rule and Rule of Three based on content analysis
# May reduce or expand the topic list

# 3. Authority validation
# Check if headings exist in LCSH authority file
# Verify if geographic subdivision is allowed

# 4. MARC generation (2026 LC Practice - no form subdivisions)
# Final output:
# 650  0 $aCompanion planting.
# 650  0 $aVegetable gardening.
# 650  0 $aOrganic gardening.
# 655  7 $aHandbooks and manuals.$2lcgft
```
