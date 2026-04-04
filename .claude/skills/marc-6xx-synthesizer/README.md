# MARC 21 Subject Access Synthesizer

A Python script for generating properly formatted MARC 21 subject access fields (6XX) for catalog records, following Library of Congress Subject Cataloging Manual guidelines.

## Installation

No external dependencies required. Just ensure Python 3 is installed.

## Usage

### Command Line
```bash
# Run examples
python3 scripts/marc_synthesizer.py
```

### Python API
```python
from scripts.marc_synthesizer import MARCSynthesizer

# Create synthesizer
synth = MARCSynthesizer()

# Add subject heading
synth.add_subject_heading({
    'a': 'Companion planting',
    'x': 'United States',
    'v': 'Handbooks, manuals, etc.'
}, '650', ' 0')

# Generate MARC field
marc_fields = synth.generate_marc_fields()
```

## Features

- **Proper Subfield Order**: Follows H 1075 order ($a → $z → $x → $y → $v)
- **Multiple Tags**: Supports 600, 610, 650, 651, 655
- **Batch Processing**: Generate multiple fields at once
- **Flexible Input**: Accept dictionaries or use quick methods
- **H 80 Compliance**: Orders by subject predominance

## MARC Tag Reference

- **600**: Personal Name
- **610:** Corporate Name
- **650**: Topical Term
- **651**: Geographic Name
- **655**: Genre/Form (with $2 lcgft)

## Example

Input:
```python
MARCSynthesizer.quick_marc(
    "Vegetable gardening",
    geography="United States",
    subdivisions="Organic farming",
    form="Handbooks, manuals, etc."
)
```

Output:
```
650 0  $aVegetable gardening $zUnited States $xOrganic farming $vHandbooks, manuals, etc.
```