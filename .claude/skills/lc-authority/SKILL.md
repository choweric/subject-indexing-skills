---
name: lc-authority
description: Check Library of Congress authority files (LCSH subjects, LCGFT genre/forms, LCNAF names) for valid headings, geographic subdivision authorization, and hierarchical relationships (BT/NT/UF).
---

# LC Authority Validator

Validates headings against Library of Congress authority files using TF-IDF semantic search.

## Supported Authority Types

| Type | File | MARC Fields | Method | Description |
|------|------|-------------|--------|-------------|
| `subjects` | LCSH | 650, 651 | Local index | Subject headings (topical, geographic) |
| `genreforms` | LCGFT | 655 | Local index | Genre/form terms |
| `names` | LCNAF | 600, 610, 611 | **LC API** | Personal names, corporate names, meeting names |

**Note:** Names use the LC Linked Data API instead of a local index. This provides always-current data without requiring the 44GB LCNAF file.

## Quick Start

### Command Line

```bash
cd scripts

# Search LCSH subjects (default)
python3 tfidf_search.py "companion planting"
python3 tfidf_search.py "vegetable garden" --top 5

# Search LCGFT genre/forms
python3 tfidf_search.py "Essays" -a genreforms
python3 tfidf_search.py "documentary films" -a genreforms

# Search LCNAF names (personal, corporate, meeting)
# Names auto-invert: "William Shakespeare" → finds "Shakespeare, William"
python3 tfidf_search.py "William Shakespeare" -a names
python3 tfidf_search.py "Mark Twain" -a names
python3 tfidf_search.py "Library of Congress" -a names

# Check authority status
python3 tfidf_search.py "Tacos" --check
python3 tfidf_search.py "Instructional films" -a genreforms --check
python3 tfidf_search.py "Mark Twain" -a names --check
```

### Python API

```python
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent / "scripts"))
from tfidf_search import search_headings, check_heading_authority, suggest_authorized_heading

# Search LCSH subjects (default)
results = search_headings("vegetable garden", top_k=5)

# Search LCGFT genre/forms
results = search_headings("Essays", authority_type="genreforms")

# Search LCNAF names
results = search_headings("Shakespeare", authority_type="names")

# Check authority status
heading_info = check_heading_authority("Organic gardening")
heading_info = check_heading_authority("Essays", authority_type="genreforms")
heading_info = check_heading_authority("Twain, Mark, 1835-1910", authority_type="names")

# Get authorized form (handles UF references)
authorized, is_exact, note = suggest_authorized_heading("Planting, Companion")
# Returns: ("Companion planting", False, "USE 'Companion planting' (searched term is a variant)")
```

## Validation Workflow

### Step 1: Search for Heading

Query the authority file for the preferred form of a term:

```python
result = check_heading_authority("Your heading here")
if result:
    print(f"Authorized heading: {result['authorized_heading']}")
    print(f"Similarity score: {result['similarity_score']}")
    print(f"MARC field: {result.get('marc_field', 'N/A')}")
```

If the term is found as a "Used For" (UF) reference, swap it for the authorized "USE" heading.

### Step 2: Check Geographic Authorization

For subject headings, check if geographic subdivision is permitted:

```python
if result['geographic_subdivision'] == 'May subdivide geographically':
    # Can add $z subfield (e.g., $zUnited States)
else:
    # DO NOT add geographic subdivision
```

### Step 3: Review Hierarchical Context

Use broader terms (BT) and narrower terms (NT) to verify heading appropriateness:

```python
print(f"Broader terms: {result['broader_terms']}")
print(f"Narrower terms: {result['narrower_terms']}")
print(f"Used for (variants): {result['used_for']}")
```

## Return Format

### Search Result

```json
{
  "heading": "Companion planting",
  "similarity_score": 1.0,
  "exact_match": true,
  "is_variant": false,
  "authority_type": "subjects",
  "authorized_heading": "Companion planting",
  "geographic_subdivision": "May subdivide geographically",
  "marc_field": "150 0$aCompanion planting",
  "broader_terms": ["http://id.loc.gov/authorities/subjects/sh85067221"],
  "narrower_terms": [],
  "used_for": ["Planting, Companion"]
}
```

### UF Reference Result

```json
{
  "heading": "Planting, Companion",
  "similarity_score": 1.0,
  "exact_match": false,
  "is_variant": true,
  "authority_type": "subjects",
  "authorized_heading": "Companion planting",
  "is_use_reference": true,
  "geographic_subdivision": "May subdivide geographically",
  "marc_field": "150 0$aCompanion planting"
}
```

## Name Heading Validation (H 430)

When using a name heading as a subject, verify:
1. The heading is a valid **RDA or AACR2** heading (coded in field 008/10)
2. The heading is authorized for subject use (field 008/15 = "a")
3. The heading **does not conflict** with subject cataloging policies:
   - Use **personal name** form for government officials, not corporate form
   - For literary authors with multiple pseudonyms, use the **base heading** (the one with the complete set of references)
   - For uniform titles as subjects, omit language elements (cf. H 1435)
   - For jurisdictions, use the **latest name** only

## Entity Type Classification (H 405)

Named entities are classified into two groups that determine which authority file they belong to:

- **Group 1 (Name authority → 600/610/611/630):** Persons, corporate bodies, meetings, titles, jurisdictions — established via descriptive cataloging conventions
- **Group 2 (Subject authority → 650/651):** Geographic features, structures, events without formal names, awards, ethnic tribes — established via subject cataloging conventions

When validating a named entity, this determines both the MARC tag and the authority file to search:
- Group 1 entities → search LCNAF (names authority type)
- Group 2 entities → search LCSH (subjects authority type)

## Formulating Geographic Headings (H 690)

Geographic names fall into two categories, each with its own authority file:

| Category | Authority File | MARC Tag | Examples |
|----------|---------------|----------|----------|
| **Jurisdictions** (political entities) | Name authority (LCNAF) | 651 | France, California, Tokyo |
| **Non-jurisdictional** (geographic features) | Subject authority (LCSH) | 651 | Fuji, Mount (Japan); Yellow River (China) |

Consult H 405 for guidance on which authority file an entity belongs to. Non-jurisdictional geographic headings are established according to the guidelines below.

### D.1. Sources of Approved Names

Obtain the approved form of name from these required reference sources:

| Scope | Source | URL |
|-------|--------|-----|
| **United States** | GNIS (Geographic Names Information System) | https://edits.nationalmap.gov/apps/gaz-domestic/public/search/names |
| **Foreign (except NZ)** | GNS (Geographic Names Server) | https://geonames.nga.mil/geonames/GeographicNamesSearch/ |
| **New Zealand** | NZ Gazetteer | https://gazetteer.linz.govt.nz/ |

Always use the BGN (Board on Geographic Names) approved name as the basis for the heading. For GNS, prefer names in this order: (1) conventional name, (2) approved name, (3) approved English name if multiple exist.

If no BGN decision exists, select the form found in predominant usage in standard reference sources (Merriam-Webster's Geographical Dictionary, Columbia Gazetteer, national gazetteers, standard encyclopedias, atlases).

### D.3. Selecting the Form of Name

**D.3.b.i. English vs. vernacular form:** Select the English form whenever possible.

| Vernacular | English (preferred) |
|-----------|-------------------|
| Fujiyama | Mount Fuji |
| Øresund | The Sound |
| Peipsi järv | Lake Peipus |
| Passo del San Gottardo | Saint Gotthard Pass |

If no English form exists, translate the generic term into English. Use the noun form in the nominative case for inflected languages.

**D.3.b.ii. When to use the vernacular form:**
- When the generic term is integral and inseparable (e.g., Kilpisjärvi — "järvi" = lake)
- For parks, reserves, gardens, trails, streets, and roads (see H 1925, H 2098)
- When the entity is best known by its vernacular name (e.g., Rio Grande; Blanc, Mont)
- If the vernacular includes the generic term, do NOT add the English generic (e.g., Tien Shan already means "mountains")

**D.3.b.iii. Arrangement of elements:** Put the distinctive portion in the initial position.

For English names, invert if needed:

| Original | Inverted (heading form) |
|----------|----------------------|
| Lake Erie | Erie, Lake |
| Mount Fuji | Fuji, Mount (Japan) |
| Firth of Forth | Forth, Firth of (Scotland) |
| Strait of Gibraltar | Gibraltar, Strait of |

For foreign names, translate the generic and place distinctive first (no comma):

| Vernacular | Heading form |
|-----------|-------------|
| Río Jiloca | Jiloca River (Spain) |
| Bahía Mazarredo | Mazarredo Bay (Chile) |

**D.3.b.iv. Abbreviations:** Spell out all words in the name portion (e.g., "Saint Andrew Sound" not "St. Andrew Sound"). Abbreviations may appear in qualifiers per H 810.

**D.3.b.v. Initial articles:**
- **Foreign non-English-speaking countries:** Drop the article, add English generic (La Huasteca → Huasteca Region; Les Cévennes → Cévennes Mountains)
- **English-speaking countries:** Retain the article (Los Olmos Creek)
- **English "The":** Retain and invert (The Fens → Fens, The (England))

**D.3.b.vi. Transliteration:** Use LC transliteration tables. If BGN romanization conflicts with LC policy, convert to LC form — unless the non-LC form is more commonly used in English-language sources. **Chinese names:** LC uses pinyin romanization (including for Taiwan, since May 2012).

**D.3.b.vii. Conflicts:** Resolve by (1) incorporating the generic term into the name (preferred), or (2) adding a category designator in the qualifier after a colon (e.g., `Skovfjorden (Greenland : Fjord)`). For regions conflicting with cities, include "Region" in qualifier.

### E. References for Geographic Headings

**UF references:** Add variants from BGN, vernacular forms, LC-romanized equivalents, other official languages, abbreviated forms, and forms with/without initial articles.

**BT references:** Add up to three broader terms with the generic heading for the feature type subdivided by country (e.g., `550 $w g $a Mountains $z Japan`). Also add BT for the named group the feature belongs to (e.g., Blue Ridge Mountains as BT for Black Mountains).

### Extended Examples

```
151 ## $a Fuji, Mount (Japan)
451 ## $a Fujiyama (Japan)
451 ## $a Mount Fuji (Japan)
550 ## $w g $a Mountains $z Japan
550 ## $w g $a Volcanoes $z Japan

151 ## $a Yellow River (China)
451 ## $a Huang He (China)
451 ## $a Hwang Ho (China)
550 ## $w g $a Rivers $z China

151 ## $a Sound, The (Denmark and Sweden)
451 ## $a Øresund (Denmark and Sweden)
550 ## $w g $a Sounds (Geomorphology) $z Denmark
550 ## $w g $a Sounds (Geomorphology) $z Sweden

151 ## $a Saint Gotthard Pass (Switzerland)
451 ## $a Passo del San Gottardo (Switzerland)
451 ## $a Sankt Gotthardpass (Switzerland)
550 ## $w g $a Mountain passes $z Switzerland
```

### Representative Non-Jurisdictional Geographic Entities

Archaeological sites, areas/regions, canals, dams, extinct cities (pre-1500), farms/ranches/gardens, forests/grasslands, geographic features (caves, deserts, islands, lakes, mountains, ocean currents, plains, rivers, seas, steppes, undersea features), geologic basins/formations, mines, parks/reserves/refuges, reservoirs, roads/streets/trails, valleys.

## Geographic Subdivision Authorization (H 830)

The `geographic_subdivision` field in search results indicates whether a heading may be subdivided by place:
- **"May subdivide geographically"** (008/06 = i): Heading can receive $z subfields
- **"Not authorized"** (008/06 = #): Do NOT add geographic subdivisions

When applying geographic subdivisions, use the **indirect method** (H 830 sec. C.1):
- Interpose the country between the heading and the locality: `$aMusic$zSwitzerland$zGeneva`
- **Exception:** US states, Canadian provinces, and GB constituent countries are used directly without the country: `$aMusic$zOntario$zToronto`
- Maximum **two levels** of geographic subdivision
- Always use the **latest name** and **present sovereignty**

## LCGFT Authority Records (J 107)

When searching the genreforms authority type, results come from LCGFT authority records:

| Field | Content |
|-------|---------|
| 155 | Authorized genre/form term |
| 455 | Used For (UF) references |
| 555 | Broader Terms (BT) and Related Terms (RT) |
| 680 | Scope notes |

**Validation:** A valid LCGFT term has a control number with the **gf** prefix (e.g., `gf2014026085`). Terms with only a **gp** prefix are proposals not yet approved — do not assign them.

LCGFT terms are **never subdivided**. They appear in bibliographic records as simple 655 fields: `655 #7 $a[Term].$2lcgft`

## Features

- **Semantic matching**: Finds morphological variations (e.g., "garden" matches "gardening")
- **Similarity scores**: Results ranked by TF-IDF cosine similarity (0.0-1.0)
- **UF reference search**: Variant terms indexed and searchable
- **Multiple authority types**: Search subjects, genre/forms, and names from single interface
- **Smart name handling**: Auto-inverts personal names ("Mark Twain" → "Twain, Mark")
- **Variant spelling support**: Finds names via misspellings and alternate forms
- **Full metadata**: Returns BT, NT, UF, geographic subdivision, MARC field

## Index Management

### Building/Rebuilding Indexes

```bash
cd scripts

# Build specific index (subjects and genreforms only)
python3 tfidf_indexer.py subjects      # LCSH subjects (~3-5 min)
python3 tfidf_indexer.py genreforms    # LCGFT genre/forms (~5 sec)

# Build all available indexes
python3 tfidf_indexer.py --all

# Check available authority files
python3 tfidf_indexer.py
```

**Note:** Names authority uses the LC API - no local index required.

### Index Statistics

| Authority | Documents | Terms | Index Size | Build Time |
|-----------|-----------|-------|------------|------------|
| subjects | ~1,010,000 | ~214,000 | ~480 MB | ~3-5 min |
| genreforms | ~8,600 | ~4,200 | ~5 MB | ~5 sec |
| names | N/A | N/A | N/A | **Uses API** |

### Index Structure

```
scripts/index/
├── subjects/
│   ├── config.json
│   ├── vocabulary.json
│   ├── idf.json
│   └── documents.ndjson
└── genreforms/
    ├── config.json
    ├── vocabulary.json
    ├── idf.json
    └── documents.ndjson
```

### LCNAF API

Names are looked up via the LC Linked Data Service suggest2 API:
- **Suggest2 API**: `http://id.loc.gov/authorities/names/suggest2/?q=NAME`

The suggest2 API provides:
- Rich metadata (MARC fields, variant labels, RDF types)
- Variant label searching (misspellings, alternate name forms)
- Left-anchored prefix matching

#### Smart Query Reformulation

The LC API uses **prefix matching** (left-anchored), which means "William Shakespeare" won't directly find "Shakespeare, William". The client automatically handles this by:

1. **Inverting personal names**: "Mark Twain" → tries "Twain, Mark" first
2. **Detecting corporate names**: "Library of Congress" is NOT inverted
3. **Trying multiple variants**: Maximizes chance of finding the correct record

**Examples that work:**
```bash
# All find "Shakespeare, William, 1564-1616"
python3 lcnaf_api.py "Shakespeare, William"      # Direct match
python3 lcnaf_api.py "William Shakespeare"       # Auto-inverted
python3 lcnaf_api.py "Shakspeare, William"       # Variant spelling

# All find "Twain, Mark, 1835-1910"
python3 lcnaf_api.py "Twain, Mark"               # Direct match
python3 lcnaf_api.py "Mark Twain"                # Auto-inverted

# Corporate names work as-is
python3 lcnaf_api.py "Library of Congress"       # No inversion needed
```

#### Benefits
- Always current (no stale data)
- No 44GB download required
- No index build time
- Minimal storage
- Variant spellings searchable

#### Limitations
- **Not true semantic search**: Unlike subjects/genreforms, names use prefix matching
- **Name format matters**: Works best with inverted form "LastName, FirstName"
- **Network required**: Requires internet connection

The API client is in `scripts/lcnaf_api.py` and is automatically used when searching names.

## Authority Files

Place authority files in the `references/` folder:

| File | Required | Source |
|------|----------|--------|
| `subjects.madsrdf.jsonld` | Yes | https://id.loc.gov/download/authorities/subjects.madsrdf.jsonld.gz |
| `genreForms.madsrdf.jsonld` | Yes | https://id.loc.gov/download/authorities/genreForms.madsrdf.jsonld.gz |
| `names.madsrdf.jsonld` | **No** | API used instead (44GB file not needed) |
