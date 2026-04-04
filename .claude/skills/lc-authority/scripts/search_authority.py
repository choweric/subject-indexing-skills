#!/usr/bin/env python3
"""
LCSH authority file searcher for lcsh-authority skill.
Efficiently searches for any subject candidate against the authority file.
"""

import json
import re
import sys
from pathlib import Path

def search_authority_headings(headings_to_check, authority_file_path=None):
    """
    Search the LCSH authority file for specific headings.

    Args:
        headings_to_check: List of heading strings to search for, or single string
        authority_file_path: Optional path to authority file (uses default if None)

    Returns:
        Dictionary of results for each heading with authority information
    """
    # Default authority file location
    if authority_file_path is None:
        skill_dir = Path(__file__).parent
        authority_file_path = skill_dir.parent / "references" / "subjects.madsrdf.jsonld"

    # Handle single string input
    if isinstance(headings_to_check, str):
        headings_to_check = [headings_to_check]

    results = {}
    headings_lower = [h.lower().strip() for h in headings_to_check]

    # Track what's been found
    found_headings = set()

    try:
        with open(authority_file_path, 'r', encoding='utf-8') as f:
            # Process line by line - each line is a JSON object (NDJSON format)
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse each line as JSON
                    record = json.loads(line)
                    graph = record.get("@graph", [])

                    # Process each item in the graph
                    for item in graph:
                        # Check if this is an authority record with authoritativeLabel
                        if "madsrdf:authoritativeLabel" in item and "madsrdf:Authority" in item.get("@type", []):
                            label = item.get("madsrdf:authoritativeLabel", {})

                            # Get the English label
                            if isinstance(label, dict) and label.get("@language") == "en":
                                pref_label = label.get("@value", "")
                            elif isinstance(label, str):
                                pref_label = label
                            else:
                                continue

                            if pref_label:
                                # Check against our search list
                                for i, search_heading in enumerate(headings_lower):
                                    original_heading = headings_to_check[i]

                                    # Check for exact match only (for better precision)
                                    if search_heading == pref_label.lower():

                                        # Found a match
                                        if original_heading not in results:
                                            results[original_heading] = {
                                                "authorized_heading": pref_label,
                                                "found_in_line": line_num + 1,
                                                "exact_match": search_heading == pref_label.lower(),
                                                "geographic_subdivision": "Not authorized",
                                                "marc_field": None,
                                                "authority_type": item.get("@type", [])
                                            }

                                            # Look for MARC key
                                            marc_key = item.get("bflc:marcKey", "")
                                            if marc_key:
                                                results[original_heading]["marc_field"] = marc_key

                                            # Check for geographic subdivision capability
                                            # Check if it's part of the Geographic subdivision collection
                                            collections = item.get("madsrdf:isMemberOfMADSCollection", [])
                                            for coll in collections:
                                                if isinstance(coll, dict):
                                                    coll_id = coll.get("@id", "")
                                                else:
                                                    coll_id = str(coll)
                                                if "collection_SubdivideGeographically" in coll_id:
                                                    results[original_heading]["geographic_subdivision"] = "May subdivide geographically"

                                            # Look for broader terms
                                            broader = item.get("madsrdf:hasBroaderAuthority", [])
                                            if broader:
                                                broader_ids = []
                                                for b in broader:
                                                    if isinstance(b, dict):
                                                        broader_ids.append(b.get("@id", ""))
                                                    else:
                                                        broader_ids.append(str(b))
                                                if broader_ids:
                                                    results[original_heading]["broader_terms"] = broader_ids

                                            # Look for narrower terms
                                            narrower = item.get("madsrdf:hasNarrowerAuthority", [])
                                            if narrower:
                                                narrower_ids = []
                                                for n in narrower:
                                                    if isinstance(n, dict):
                                                        narrower_ids.append(n.get("@id", ""))
                                                    else:
                                                        narrower_ids.append(str(n))
                                                if narrower_ids:
                                                    results[original_heading]["narrower_terms"] = narrower_ids

                                            # Check for "Used For" references (alternate terms)
                                            variants = item.get("madsrdf:hasVariant", [])
                                            if variants:
                                                variant_labels = []
                                                for variant in variants:
                                                    if isinstance(variant, dict):
                                                        vlabel = variant.get("madsrdf:variantLabel", {})
                                                        if isinstance(vlabel, dict) and vlabel.get("@language") == "en":
                                                            variant_labels.append(vlabel.get("@value", ""))
                                                        elif isinstance(vlabel, str):
                                                            variant_labels.append(vlabel)
                                                if variant_labels:
                                                    results[original_heading]["used_for"] = variant_labels

                                            found_headings.add(original_heading)

                                        if len(found_headings) == len(headings_to_check):
                                            # Found all our headings, can stop early
                                            return results

                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue

    except FileNotFoundError:
        print(f"Error: Authority file not found at {authority_file_path}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"Error searching authority file: {e}", file=sys.stderr)
        return {}

    return results

def check_heading_authority(heading):
    """
    Check a single heading against the LCSH authority file.

    Args:
        heading: Single subject heading to check

    Returns:
        Dictionary with authority information or None if not found
    """
    results = search_authority_headings(heading)
    return results.get(heading, None)

def suggest_authorized_heading(search_term):
    """
    Find the authorized form of a heading, including "Used For" references.

    Args:
        search_term: Term to search for

    Returns:
        Tuple of (authorized_heading, is_authorized, note)
    """
    results = search_authority_headings(search_term)
    result = results.get(search_term)

    if not result:
        # Try word-by-word fuzzy matching
        if len(search_term.split()) > 1:
            words = search_term.split()
            for word in words:
                if len(word) > 3:  # Only check meaningful words
                    fuzzy_results = search_authority_headings([word])
                    if fuzzy_results and word in fuzzy_results:
                        found = fuzzy_results[word]
                        return (found['authorized_heading'],
                               False,
                               f"Consider using '{found['authorized_heading']}' instead of '{search_term}'")
        return (search_term, False, "Heading not found in LCSH authority file")

    # Check if there are "Used For" references
    note = ""
    if result.get("used_for"):
        if search_term in result["used_for"]:
            note = f"'{search_term}' is a 'Used For' reference for the authorized heading"

    return (result['authorized_heading'], result.get('exact_match', True), note)

# Example usage for testing
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line usage: python search_authority.py "Companion planting"
        search_terms = sys.argv[1:]
        results = search_authority_headings(search_terms)

        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        # Test with some example terms
        test_headings = ["Companion planting", "Vegetable gardening", "Nonexistent topic"]
        results = search_authority_headings(test_headings)

        print("Test Results:")
        print(json.dumps(results, indent=2, ensure_ascii=False))