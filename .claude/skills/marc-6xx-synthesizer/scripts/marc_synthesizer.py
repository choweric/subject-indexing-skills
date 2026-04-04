#!/usr/bin/env python3
"""
MARC 21 Subject Access Synthesizer

Generates properly formatted MARC 21 subject access fields (6XX) for catalog records.
Follows Library of Congress Subject Cataloging Manual guidelines.

Supports:
- 600: Personal Name Subject
- 610: Corporate Name Subject
- 611: Meeting Name Subject
- 650: Topical Subject
- 651: Geographic Subject
- 655: Genre/Form (LCGFT)

Integrates with lc-authority skill for LCNAF name authority lookups.
"""

import re
from typing import Dict, List, Optional, Any, Tuple


class MARCSynthesizer:
    """
    MARC 21 Subject Field Synthesizer.

    Generates properly formatted 6XX fields from heading data,
    including integration with LCNAF API results for name subjects.
    """

    def __init__(self):
        self.subject_headings = []
        self.valid_tags = ['600', '610', '611', '650', '651', '655']

        # Mapping from 1XX authority tags to 6XX subject tags
        self.authority_to_subject_tag = {
            '100': '600',  # Personal name
            '110': '610',  # Corporate name
            '111': '611',  # Meeting name
            '130': '630',  # Uniform title (not fully supported yet)
        }

        # Name subfield order for 600/610/611 fields
        # These come before general subdivisions
        self.name_subfields = ['a', 'b', 'c', 'd', 'n', 'q', 't']

        # Subject subdivision order (H 1075)
        self.subdivision_subfields = ['z', 'x', 'y', 'v']

    def add_subject_heading(self, heading: Dict, tag: str = '650', indicators: str = ' 0'):
        """
        Add a subject heading with proper formatting.

        Args:
            heading: Dictionary with subfield codes as keys
            tag: MARC field tag (600, 610, 611, 650, 651, 655)
            indicators: Two-character indicator string
        """
        if heading is None:
            return

        # Ensure indicators are exactly 2 characters
        if len(indicators) == 1:
            indicators = indicators + '0'
        elif len(indicators) != 2:
            indicators = ' 0'

        self.subject_headings.append({
            'tag': tag,
            'indicators': indicators,
            'heading': heading
        })

    def add_name_subject(self, lcnaf_result: Dict, subdivisions: Dict = None,
                         second_indicator: str = '0'):
        """
        Add a name subject heading from LCNAF API result.

        Converts LCNAF authority data to a 600/610/611 subject field.

        Args:
            lcnaf_result: Result dictionary from lc-authority names search
            subdivisions: Optional dict with subdivision subfields (x, z, y, v)
            second_indicator: '0' for LCSH, '4' for source not specified

        Returns:
            The generated MARC field string

        Example:
            result = check_heading_authority("Shakespeare, William", authority_type="names")
            synth.add_name_subject(result, subdivisions={'x': 'Criticism and interpretation'})
            # Generates: 600 10 $aShakespeare, William,$d1564-1616$xCriticism and interpretation
        """
        if not lcnaf_result:
            return None

        marc_field_str = lcnaf_result.get('marc_field', '')
        name_type = lcnaf_result.get('name_type', 'unknown')

        # Parse the MARC field from LCNAF
        parsed = self.parse_marc_field_string(marc_field_str)
        if not parsed:
            # Fallback: use authorized_heading as $a
            parsed = {
                'tag': '100',
                'indicators': '10',
                'subfields': {'a': lcnaf_result.get('authorized_heading', '')}
            }

        # Map 1XX tag to 6XX
        auth_tag = parsed.get('tag', '100')[:3]
        subject_tag = self.authority_to_subject_tag.get(auth_tag, '600')

        # Build heading dict from parsed subfields
        heading = parsed.get('subfields', {}).copy()

        # Add subdivisions if provided
        if subdivisions:
            for code in ['x', 'z', 'y', 'v']:
                if code in subdivisions and subdivisions[code]:
                    heading[code] = subdivisions[code]

        # Determine first indicator based on name type and tag
        first_indicator = self._determine_first_indicator(subject_tag, name_type, heading)
        indicators = first_indicator + second_indicator

        self.add_subject_heading(heading, subject_tag, indicators)
        return self.generate_marc_fields()[-1]

    def parse_marc_field_string(self, marc_string: str) -> Optional[Dict]:
        """
        Parse a MARC field string into components.

        Handles formats like:
        - "1001 $aShakespeare, William,$d1564-1616"
        - "1102 $aLibrary of Congress.$bCatalog Division"
        - "1112 $aConference Name$d(2009 :$cLocation)"

        Args:
            marc_string: MARC field string from LCNAF API

        Returns:
            Dict with 'tag', 'indicators', 'subfields' or None if parsing fails
        """
        if not marc_string:
            return None

        # Pattern: TAG + indicators + subfields
        # e.g., "1001 $aShakespeare..." or "110 2$aLibrary..."
        match = re.match(r'^(\d{3})\s*(\d{0,2})\s*(.*)$', marc_string.strip())
        if not match:
            return None

        tag = match.group(1)
        indicators = match.group(2).ljust(2)  # Pad to 2 chars
        subfield_str = match.group(3)

        # Parse subfields
        subfields = {}
        # Split on $ but keep the delimiter for parsing
        parts = re.split(r'(\$[a-z0-9])', subfield_str)

        current_code = None
        current_value = []

        for part in parts:
            if re.match(r'^\$[a-z0-9]$', part):
                # Save previous subfield
                if current_code and current_value:
                    value = ''.join(current_value).strip()
                    if value:
                        if current_code in subfields:
                            # Handle repeatable subfields
                            if isinstance(subfields[current_code], list):
                                subfields[current_code].append(value)
                            else:
                                subfields[current_code] = [subfields[current_code], value]
                        else:
                            subfields[current_code] = value
                current_code = part[1]  # Character after $
                current_value = []
            elif current_code:
                current_value.append(part)

        # Save last subfield
        if current_code and current_value:
            value = ''.join(current_value).strip()
            if value:
                if current_code in subfields:
                    if isinstance(subfields[current_code], list):
                        subfields[current_code].append(value)
                    else:
                        subfields[current_code] = [subfields[current_code], value]
                else:
                    subfields[current_code] = value

        return {
            'tag': tag,
            'indicators': indicators,
            'subfields': subfields
        }

    def _determine_first_indicator(self, tag: str, name_type: str, heading: Dict) -> str:
        """
        Determine the first indicator for name subject fields.

        600 first indicator:
            0 - Forename (e.g., John, Saint)
            1 - Surname (e.g., Shakespeare, William)
            3 - Family name

        610 first indicator:
            1 - Jurisdiction name
            2 - Name in direct order

        611 first indicator:
            0 - Inverted name
            1 - Jurisdiction name
            2 - Name in direct order
        """
        if tag == '600':
            # Check if name has comma (surname entry) or not (forename)
            name = heading.get('a', '')
            if ',' in name:
                return '1'  # Surname
            else:
                return '0'  # Forename

        elif tag == '610':
            # Most corporate names use indicator 2
            return '2'

        elif tag == '611':
            # Most meeting names use indicator 2
            return '2'

        return ' '

    def format_subfield(self, code: str, value) -> str:
        """Format a subfield with proper delimiter."""
        if value is None:
            return ""
        if isinstance(value, list):
            return ''.join(f"${code}{v}" for v in value if v)
        return f"${code}{value}"

    def build_subject_string(self, heading_dict: Dict, tag: str = '650') -> str:
        """
        Build complete subject string following proper subfield order.

        For topical subjects (650, 651, 655):
            $a → $z → $x → $y → $v

        For name subjects (600, 610, 611):
            $a → $b → $c → $d → $n → $q → $t → $z → $x → $y → $v
        """
        if not heading_dict:
            return ""

        if not isinstance(heading_dict, dict):
            raise TypeError("Heading must be a dictionary")

        parts = []

        # Determine subfield order based on tag
        if tag in ['600', '610', '611']:
            # Name subject: name subfields first, then subdivisions
            subfield_order = self.name_subfields + self.subdivision_subfields
        else:
            # Topical/geographic/genre: main heading then subdivisions
            subfield_order = ['a'] + self.subdivision_subfields

        for code in subfield_order:
            if code in heading_dict and heading_dict[code]:
                value = heading_dict[code]
                if isinstance(value, list):
                    for v in value:
                        if v:
                            parts.append(self.format_subfield(code, v))
                else:
                    parts.append(self.format_subfield(code, value))

        return ''.join(parts)

    def generate_marc_fields(self) -> List[str]:
        """Generate complete MARC fields ordered by predominance (H 80)."""
        marc_fields = []

        for heading_data in self.subject_headings:
            tag = heading_data['tag']
            indicators = heading_data['indicators']

            if tag not in self.valid_tags:
                tag = '650'

            if len(indicators) != 2:
                indicators = ' 0'

            subject_string = self.build_subject_string(heading_data['heading'], tag)
            marc_field = f"{tag} {indicators} {subject_string}"
            marc_fields.append(marc_field)

        return marc_fields

    def clear(self):
        """Clear all subject headings."""
        self.subject_headings = []

    @staticmethod
    def create_from_headings(headings_list: List[Dict]) -> List[str]:
        """
        Create MARC fields from a list of heading dictionaries.

        Args:
            headings_list: List of dicts with 'heading', 'tag', 'indicators'

        Returns:
            List of formatted MARC field strings
        """
        if not isinstance(headings_list, list):
            raise TypeError("headings_list must be a list")

        synthesizer = MARCSynthesizer()

        for heading_data in headings_list:
            if not isinstance(heading_data, dict):
                continue

            tag = heading_data.get('tag', '650')
            indicators = heading_data.get('indicators', ' 0')
            heading = heading_data.get('heading', {})

            synthesizer.add_subject_heading(heading, tag, indicators)

        return synthesizer.generate_marc_fields()

    @staticmethod
    def quick_marc(subject: str, subdivisions=None, geography=None,
                   chronology=None, form=None, tag: str = '650') -> str:
        """
        Quick MARC generation for simple subject headings.

        Args:
            subject: Main subject heading ($a)
            subdivisions: General subdivisions ($x)
            geography: Geographic subdivisions ($z)
            chronology: Chronological subdivision ($y)
            form: Form subdivision ($v)
            tag: MARC tag (default 650)

        Returns:
            Formatted MARC field string
        """
        if not subject:
            return ""

        heading = {'a': subject}

        if subdivisions:
            heading['x'] = subdivisions if isinstance(subdivisions, list) else [subdivisions]

        if geography:
            heading['z'] = geography if isinstance(geography, list) else [geography]

        if chronology:
            heading['y'] = chronology

        if form:
            heading['v'] = form

        synthesizer = MARCSynthesizer()
        synthesizer.add_subject_heading(heading, tag, ' 0')

        marc_fields = synthesizer.generate_marc_fields()
        return marc_fields[0] if marc_fields else ""

    @staticmethod
    def name_subject(name: str, dates: str = None, title: str = None,
                     subdivisions=None, geography=None, chronology=None,
                     form=None, name_type: str = 'personal') -> str:
        """
        Quick generation for name subject headings.

        Args:
            name: Name in authorized form (e.g., "Shakespeare, William")
            dates: Life dates (e.g., "1564-1616")
            title: Title of work for name-title subjects
            subdivisions: General subdivisions ($x)
            geography: Geographic subdivisions ($z)
            chronology: Chronological subdivision ($y)
            form: Form subdivision ($v)
            name_type: 'personal', 'corporate', or 'meeting'

        Returns:
            Formatted MARC field string

        Example:
            MARCSynthesizer.name_subject(
                "Shakespeare, William",
                dates="1564-1616",
                subdivisions="Criticism and interpretation"
            )
            # Returns: 600 10 $aShakespeare, William,$d1564-1616$xCriticism and interpretation
        """
        # Determine tag
        tag_map = {
            'personal': '600',
            'corporate': '610',
            'meeting': '611'
        }
        tag = tag_map.get(name_type, '600')

        # Build heading
        heading = {'a': name}

        if dates:
            heading['d'] = dates

        if title:
            heading['t'] = title

        if subdivisions:
            heading['x'] = subdivisions if isinstance(subdivisions, list) else [subdivisions]

        if geography:
            heading['z'] = geography if isinstance(geography, list) else [geography]

        if chronology:
            heading['y'] = chronology

        if form:
            heading['v'] = form

        # Determine first indicator
        if tag == '600':
            first_ind = '1' if ',' in name else '0'
        else:
            first_ind = '2'

        synthesizer = MARCSynthesizer()
        synthesizer.add_subject_heading(heading, tag, first_ind + '0')

        marc_fields = synthesizer.generate_marc_fields()
        return marc_fields[0] if marc_fields else ""

    @staticmethod
    def from_lcnaf(lcnaf_result: Dict, subdivisions: Dict = None) -> str:
        """
        Generate a subject field directly from LCNAF API result.

        Args:
            lcnaf_result: Result from lc-authority names search/check
            subdivisions: Optional dict with x, z, y, v subdivisions

        Returns:
            Formatted MARC 6XX field string

        Example:
            # In your cataloging workflow:
            from lcnaf_api import check_name_authority
            result = check_name_authority("Shakespeare, William")
            marc_field = MARCSynthesizer.from_lcnaf(
                result,
                subdivisions={'x': 'Criticism and interpretation'}
            )
            # Returns: 600 10 $aShakespeare, William,$d1564-1616$xCriticism and interpretation
        """
        synthesizer = MARCSynthesizer()
        return synthesizer.add_name_subject(lcnaf_result, subdivisions)


# Example usage functions
def example_library_book():
    """Example: Carrots Love Tomatoes Companion Planting Book"""
    print("Example: Carrots Love Tomatoes Companion Planting Book")
    print("=" * 60)

    synthesizer = MARCSynthesizer()

    synthesizer.add_subject_heading({
        'a': 'Companion planting',
        'v': 'Handbooks, manuals, etc.'
    }, '650', ' 0')

    synthesizer.add_subject_heading({
        'a': 'Vegetable gardening',
        'v': 'Handbooks, manuals, etc.'
    }, '650', ' 0')

    marc_fields = synthesizer.generate_marc_fields()

    print("\nGenerated MARC Fields:")
    for i, field in enumerate(marc_fields, 1):
        print(f"{i}. {field}")

    return marc_fields


def example_name_subjects():
    """Example: Books about people and organizations"""
    print("\nExample: Name Subject Headings")
    print("=" * 60)

    # Personal name subject
    field1 = MARCSynthesizer.name_subject(
        "Shakespeare, William",
        dates="1564-1616",
        subdivisions="Criticism and interpretation"
    )
    print(f"1. {field1}")

    # Personal name with form subdivision
    field2 = MARCSynthesizer.name_subject(
        "Austen, Jane",
        dates="1775-1817",
        form="Biography"
    )
    print(f"2. {field2}")

    # Corporate name subject
    field3 = MARCSynthesizer.name_subject(
        "Library of Congress",
        subdivisions="History",
        name_type="corporate"
    )
    print(f"3. {field3}")

    # Name-title subject
    field4 = MARCSynthesizer.name_subject(
        "Shakespeare, William",
        dates="1564-1616",
        title="Hamlet",
        subdivisions="Sources"
    )
    print(f"4. {field4}")

    return [field1, field2, field3, field4]


if __name__ == "__main__":
    example_library_book()
    example_name_subjects()
