#!/usr/bin/env python3
"""
LCNAF API Client for Library of Congress Name Authority File

Uses the LC Linked Data Service suggest2 API for name authority lookups,
avoiding the need to download and index the 44GB LCNAF file.

The suggest2 API provides:
  - Rich metadata (MARC fields, variants, RDF types)
  - Variant label searching (misspellings, alternate forms)
  - Left-anchored prefix matching

This client adds smart query reformulation to handle the prefix-matching
limitation by trying multiple name formats (e.g., "William Shakespeare"
also tries "Shakespeare, William").

API Endpoint:
  - Suggest2: http://id.loc.gov/authorities/names/suggest2/?q=NAME

Usage:
    python3 lcnaf_api.py "Shakespeare, William"
    python3 lcnaf_api.py "William Shakespeare"           # Auto-inverts to find match
    python3 lcnaf_api.py "Library of Congress" --type corporate
    python3 lcnaf_api.py "American Library Association" --check
"""

import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, List, Dict, Any, Tuple


class LCNAFClient:
    """Client for LC Name Authority File API using suggest2 endpoint."""

    BASE_URL = "http://id.loc.gov"
    SUGGEST2_URL = f"{BASE_URL}/authorities/names/suggest2/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _fetch_json(self, url: str) -> Optional[Any]:
        """Fetch JSON from URL."""
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print(f"Network error: {e}", file=sys.stderr)
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}", file=sys.stderr)
            return None

    def _generate_query_variants(self, query: str) -> List[str]:
        """
        Generate query variants to handle prefix-matching limitations.

        The LC API uses left-anchored prefix matching, so:
        - "William Shakespeare" won't find "Shakespeare, William"
        - "Mark Twain" won't find "Twain, Mark"

        This method generates variants to try:
        1. For personal names: inverted form FIRST (LastName, FirstName)
        2. Original query as-is
        3. Additional variations

        Returns list of queries to try, most likely first.
        """
        query = query.strip()
        variants = []

        # Check if already in "LastName, FirstName" format
        if ", " in query:
            # Already inverted - use as-is first
            variants.append(query)
            # Also try non-inverted for corporate names that might be misformatted
            parts = query.split(", ", 1)
            if len(parts) == 2:
                # Try "FirstName LastName" format
                non_inverted = f"{parts[1]} {parts[0]}"
                # Don't add if it has dates (e.g., "1564-1616 Shakespeare")
                if not re.search(r'^\d{4}', parts[1]):
                    variants.append(non_inverted)
        else:
            # Not inverted - check if this looks like a personal name
            words = query.split()
            if len(words) >= 2:
                # Check if this looks like a personal name (not corporate)
                # Corporate names often have: Inc., Corp., University, Library, etc.
                corporate_indicators = [
                    'inc', 'corp', 'corporation', 'company', 'co.', 'ltd',
                    'university', 'college', 'library', 'museum', 'institute',
                    'association', 'society', 'foundation', 'organization',
                    'department', 'ministry', 'bureau', 'office', 'agency',
                    'committee', 'commission', 'council', 'board', 'center',
                    'theatre', 'theater', 'orchestra', 'ensemble', 'band',
                    'press', 'publishing', 'publishers', 'records', 'studios'
                ]
                query_lower = query.lower()
                is_likely_corporate = any(ind in query_lower for ind in corporate_indicators)

                if not is_likely_corporate:
                    # Likely a personal name - try "LastName, FirstName" format FIRST
                    # This is the standard LCNAF format for personal names
                    # Handle "First Middle Last" → "Last, First Middle"
                    last_name = words[-1]
                    first_parts = " ".join(words[:-1])
                    inverted = f"{last_name}, {first_parts}"
                    variants.append(inverted)

                    # Also try just "LastName, First" without middle names
                    if len(words) > 2:
                        inverted_short = f"{last_name}, {words[0]}"
                        variants.append(inverted_short)

            # Add original query after inverted forms
            variants.append(query)

        # Ensure we always have at least the original query
        if not variants:
            variants = [query]

        return variants

    def _parse_suggest2_hit(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single hit from suggest2 API into our result format."""
        more = hit.get("more", {})
        rdftypes = more.get("rdftypes", [])

        # Determine name type from RDF types
        name_type = "unknown"
        if "PersonalName" in rdftypes:
            name_type = "personal"
        elif "CorporateName" in rdftypes:
            name_type = "corporate"
        elif "ConferenceName" in rdftypes:
            name_type = "meeting"
        elif "Title" in rdftypes:
            name_type = "title"

        # Get MARC field from marcKeys
        marc_keys = more.get("marcKeys", [])
        marc_field = marc_keys[0] if marc_keys else None

        # Check if this was found via variant (sLabel = searched variant label)
        searched_label = hit.get("sLabel", "")
        is_variant_match = bool(searched_label)

        result = {
            "heading": hit.get("aLabel", ""),
            "authorized_heading": hit.get("aLabel", ""),
            "uri": hit.get("uri", ""),
            "authority_type": "names",
            "source": "lcnaf_api",
            "name_type": name_type,
            "marc_field": marc_field,
            "variant_labels": more.get("variantLabels", []),
            "broader_terms": more.get("broaders", []),
            "narrower_terms": [],  # suggest2 doesn't return narrowers directly
            "used_for": more.get("variantLabels", []),  # variants = used for
            "is_variant_match": is_variant_match,
        }

        if is_variant_match:
            result["searched_as"] = searched_label
            result["note"] = f"Found via variant: '{searched_label}'"

        return result

    def suggest(self, query: str, limit: int = 10, try_variants: bool = True) -> List[Dict[str, Any]]:
        """
        Get name suggestions using the suggest2 API.

        Automatically tries query variants to handle prefix-matching limitations.
        For example, "William Shakespeare" will also try "Shakespeare, William".

        Args:
            query: Search query (name to look up)
            limit: Maximum number of results
            try_variants: If True, try inverted/non-inverted name formats

        Returns:
            List of results with rich metadata (MARC fields, variants, types)
        """
        if try_variants:
            variants = self._generate_query_variants(query)
        else:
            variants = [query]

        seen_uris = set()
        all_results = []

        for variant_query in variants:
            params = urllib.parse.urlencode({'q': variant_query, 'count': limit})
            url = f"{self.SUGGEST2_URL}?{params}"

            data = self._fetch_json(url)
            if not data:
                continue

            for hit in data.get("hits", []):
                uri = hit.get("uri", "")
                if uri and uri not in seen_uris:
                    seen_uris.add(uri)
                    result = self._parse_suggest2_hit(hit)
                    result["query_used"] = variant_query
                    all_results.append(result)

                    if len(all_results) >= limit:
                        break

            if len(all_results) >= limit:
                break

        return all_results[:limit]

    def check_heading(self, heading: str) -> Optional[Dict[str, Any]]:
        """
        Check if a name heading exists in LCNAF.

        Tries multiple query variants and checks for exact matches.
        Returns authority info if found, None otherwise.

        Args:
            heading: Name heading to check (any format)

        Returns:
            Dictionary with authority info and match details, or None
        """
        results = self.suggest(heading, limit=10, try_variants=True)

        if not results:
            return None

        # Normalize for comparison
        heading_lower = heading.lower().strip()
        # Remove dates for comparison (e.g., "Shakespeare, William" matches "Shakespeare, William, 1564-1616")
        heading_base = re.sub(r',?\s*\d{4}.*$', '', heading_lower).strip()

        # Check for exact match
        for result in results:
            auth_heading = result["authorized_heading"].lower().strip()
            auth_base = re.sub(r',?\s*\d{4}.*$', '', auth_heading).strip()

            if auth_heading == heading_lower or auth_base == heading_base:
                result["exact_match"] = True
                result["similarity_score"] = 1.0
                return result

            # Check if matched via variant
            for variant in result.get("variant_labels", []):
                variant_lower = variant.lower().strip()
                variant_base = re.sub(r',?\s*\d{4}.*$', '', variant_lower).strip()
                if variant_lower == heading_lower or variant_base == heading_base:
                    result["exact_match"] = False
                    result["is_use_reference"] = True
                    result["similarity_score"] = 1.0
                    result["note"] = f"USE '{result['authorized_heading']}' (searched term is a variant)"
                    return result

        # Return best match with similarity note
        best = results[0]
        best["exact_match"] = False
        best["similarity_score"] = 0.8  # Approximate - not an exact match
        best["note"] = f"Closest match: '{best['authorized_heading']}'"
        return best

    def search_by_type(self, query: str, name_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search names filtered by type.

        Args:
            query: Search query
            name_type: Type filter (personal, corporate, meeting)
            limit: Maximum results

        Returns:
            List of matching names of the specified type
        """
        results = self.suggest(query, limit=limit * 2, try_variants=True)

        # Filter by type
        filtered = [r for r in results if r.get("name_type") == name_type]
        return filtered[:limit]


def search_names(query: str, top_k: int = 10, name_type: str = None) -> List[Dict[str, Any]]:
    """
    Convenience function to search LCNAF names.

    Automatically handles name format variations (e.g., "William Shakespeare"
    will find "Shakespeare, William, 1564-1616").

    Args:
        query: Search query (any name format)
        top_k: Number of results
        name_type: Optional filter by type (personal, corporate, meeting)

    Returns:
        List of matching names with metadata
    """
    client = LCNAFClient()
    if name_type:
        return client.search_by_type(query, name_type, limit=top_k)
    return client.suggest(query, limit=top_k)


def check_name_authority(heading: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to check a name's authority status.

    Handles various name formats and checks for exact matches
    including variant forms (e.g., "Samuel Clemens" → "Twain, Mark").

    Args:
        heading: Name heading to check (any format)

    Returns:
        Dictionary with authority info or None
    """
    client = LCNAFClient()
    return client.check_heading(heading)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Search LCNAF names using LC suggest2 API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Name Format Handling:
  The API uses left-anchored prefix matching, but this client automatically
  tries multiple formats. All of these will find Shakespeare:

    "Shakespeare, William"     → Direct match
    "William Shakespeare"      → Tries inverted form
    "Shakspeare, William"      → Matches via variant spelling

Examples:
  python3 lcnaf_api.py "Shakespeare, William"
  python3 lcnaf_api.py "William Shakespeare"          # Auto-inverts
  python3 lcnaf_api.py "Library of Congress" --type corporate
  python3 lcnaf_api.py "Twain, Mark" --check
  python3 lcnaf_api.py "Samuel Clemens" --check       # Finds Mark Twain
  python3 lcnaf_api.py "American Library Association" --top 5
        """
    )
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--top", "-k", type=int, default=10, help="Number of results")
    parser.add_argument("--type", "-t", choices=["personal", "corporate", "meeting"],
                       help="Filter by name type")
    parser.add_argument("--check", action="store_true", help="Check authority status only")
    parser.add_argument("--no-variants", action="store_true",
                       help="Don't try query variants (use exact query only)")

    args = parser.parse_args()
    query = " ".join(args.query)

    client = LCNAFClient()

    try:
        if args.check:
            result = client.check_heading(query)
            if result:
                print(json.dumps({query: result}, indent=2, ensure_ascii=False))
            else:
                print(json.dumps({query: None}, indent=2))
        elif args.type:
            results = client.search_by_type(query, args.type, limit=args.top)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            results = client.suggest(query, limit=args.top, try_variants=not args.no_variants)
            print(json.dumps(results, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
