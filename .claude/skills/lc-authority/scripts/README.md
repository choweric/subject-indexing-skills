# LCSH Authority Skill

This skill provides efficient searching capabilities for the Library of Congress Subject Headings (LCSH) authority file.

## Installation

The skill runs searches against a local copy of the LCSH authority file located at:
`references/subjects.madsrdf.jsonld`

## Usage

### Command Line
```bash
# Search a single heading
python3 search_authority.py "Companion planting"

# Search multiple headings
python3 search_authority.py "Vegetable gardening" "Organic gardening"
```

### Python API
```python
from search_authority import search_authority_headings, check_heading_authority, suggest_authorized_heading

# Check a single heading
authority_info = check_heading_authority("Gardening")

# Search multiple headings
results = search_authority_headings(["Companion planting", "Vegetable gardening"])

# Get authorized form suggestion
authorized = suggest_authorized_heading("Companion crops")
```

## Return Data

Each search returns a dictionary with:
- `authorized_heading`: The authorized LCSH heading
- `exact_match`: Boolean indicating exact match
- `found_in_line`: Line number in the authority file
- `geographic_subdivision`: "May subdivide geographically" or "Not authorized"
- `marc_field`: MARC field indicator (e.g., "150  $aTacos")
- `authority_type`: Array containing the authority types
- `broader_terms`: Array of broader authority IDs (if applicable)
- `narrower_terms`: Array of narrower authority IDs (if applicable)
- `used_for`: Array of variant labels (alternate terms)