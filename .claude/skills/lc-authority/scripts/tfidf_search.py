#!/usr/bin/env python3
"""
TF-IDF Search for Library of Congress Authority Headings

Searches pre-built TF-IDF indexes for similar LC authority headings,
returning full metadata including BT, NT, UF, and geographic subdivision info.

Supported authority types:
  - subjects: LCSH Subject Headings (for 650, 651 fields)
  - genreforms: LCGFT Genre/Form Terms (for 655 fields)
  - names: LCNAF Name Authority (for 600, 610 fields) [future]

Usage:
    python3 tfidf_search.py "companion planting"                    # Search subjects (default)
    python3 tfidf_search.py "Essays" -a genreforms                  # Search genre/forms
    python3 tfidf_search.py "vegetable garden" --top 5              # Limit results
    python3 tfidf_search.py "Tacos" --check                         # Check authority status
"""

import json
import math
import re
import sys
from pathlib import Path


# Authority type configurations
AUTHORITY_TYPES = {
    "subjects": {
        "index_dir": "subjects",
        "description": "LCSH Subject Headings (650, 651 fields)",
        "method": "local",
    },
    "genreforms": {
        "index_dir": "genreforms",
        "description": "LCGFT Genre/Form Terms (655 fields)",
        "method": "local",
    },
    "names": {
        "index_dir": "names",
        "description": "LCNAF Name Authority (600, 610, 611 fields)",
        "method": "api",  # Uses LC API instead of local index
    },
}


# Import or inline the Porter Stemmer (same as indexer)
class PorterStemmer:
    """Minimal Porter Stemmer for English words."""

    def __init__(self):
        self.vowels = set('aeiou')

    def _is_consonant(self, word, i):
        if word[i] in self.vowels:
            return False
        if word[i] == 'y':
            return i == 0 or not self._is_consonant(word, i - 1)
        return True

    def _measure(self, word):
        m = 0
        i = 0
        n = len(word)
        while i < n and self._is_consonant(word, i):
            i += 1
        while i < n:
            while i < n and not self._is_consonant(word, i):
                i += 1
            if i >= n:
                break
            m += 1
            while i < n and self._is_consonant(word, i):
                i += 1
        return m

    def stem(self, word):
        if len(word) < 3:
            return word
        word = word.lower()

        if word.endswith('sses'):
            word = word[:-2]
        elif word.endswith('ies'):
            word = word[:-2]
        elif word.endswith('ss'):
            pass
        elif word.endswith('s'):
            word = word[:-1]

        if word.endswith('eed'):
            if self._measure(word[:-3]) > 0:
                word = word[:-1]
        elif word.endswith('ed'):
            stem = word[:-2]
            if any(c in self.vowels for c in stem):
                word = stem
                if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
                    word += 'e'
        elif word.endswith('ing'):
            stem = word[:-3]
            if any(c in self.vowels for c in stem):
                word = stem
                if word.endswith('at') or word.endswith('bl') or word.endswith('iz'):
                    word += 'e'

        if word.endswith('y') and len(word) > 2:
            if any(c in self.vowels for c in word[:-1]):
                word = word[:-1] + 'i'

        suffixes_step2 = [
            ('ational', 'ate'), ('tional', 'tion'), ('enci', 'ence'),
            ('anci', 'ance'), ('izer', 'ize'), ('isation', 'ize'),
            ('ization', 'ize'), ('ation', 'ate'), ('ator', 'ate'),
            ('alism', 'al'), ('iveness', 'ive'), ('fulness', 'ful'),
            ('ousness', 'ous'), ('aliti', 'al'), ('iviti', 'ive'),
            ('biliti', 'ble'), ('logi', 'log')
        ]
        for suffix, replacement in suffixes_step2:
            if word.endswith(suffix):
                stem = word[:-len(suffix)]
                if self._measure(stem) > 0:
                    word = stem + replacement
                break

        suffixes_step3 = [
            ('icate', 'ic'), ('ative', ''), ('alize', 'al'),
            ('iciti', 'ic'), ('ical', 'ic'), ('ful', ''), ('ness', '')
        ]
        for suffix, replacement in suffixes_step3:
            if word.endswith(suffix):
                stem = word[:-len(suffix)]
                if self._measure(stem) > 0:
                    word = stem + replacement
                break

        suffixes_step4 = [
            'al', 'ance', 'ence', 'er', 'ic', 'able', 'ible', 'ant',
            'ement', 'ment', 'ent', 'ion', 'ou', 'ism', 'ate', 'iti',
            'ous', 'ive', 'ize'
        ]
        for suffix in suffixes_step4:
            if word.endswith(suffix):
                stem = word[:-len(suffix)]
                if self._measure(stem) > 1:
                    if suffix == 'ion' and stem and stem[-1] in 'st':
                        word = stem
                    elif suffix != 'ion':
                        word = stem
                break

        if word.endswith('e'):
            stem = word[:-1]
            if self._measure(stem) > 1:
                word = stem
            elif self._measure(stem) == 1:
                if len(stem) >= 3:
                    n = len(stem)
                    if (self._is_consonant(stem, n - 3) and
                        not self._is_consonant(stem, n - 2) and
                        self._is_consonant(stem, n - 1) and
                        stem[-1] not in 'wxy'):
                        pass
                    else:
                        word = stem

        if word.endswith('ll') and self._measure(word[:-1]) > 1:
            word = word[:-1]

        return word


class TFIDFSearcher:
    """Search LC authority headings using pre-built TF-IDF index."""

    def __init__(self, index_dir=None, authority_type="subjects"):
        """
        Initialize searcher.

        Args:
            index_dir: Explicit path to index directory (overrides authority_type)
            authority_type: Type of authority to search (subjects, genreforms, names)
        """
        if index_dir:
            self.index_dir = Path(index_dir)
        else:
            script_dir = Path(__file__).parent
            if authority_type not in AUTHORITY_TYPES:
                raise ValueError(f"Unknown authority type: {authority_type}. "
                               f"Available: {', '.join(AUTHORITY_TYPES.keys())}")
            self.index_dir = script_dir / "index" / AUTHORITY_TYPES[authority_type]["index_dir"]

        self.authority_type = authority_type
        self.vocabulary = {}
        self.idf = []
        self.documents = []
        self.stemmer = None
        self.use_stemming = True

        self._load_index()

    def _load_index(self):
        """Load index files into memory."""
        if not self.index_dir.exists():
            raise FileNotFoundError(
                f"Index directory not found: {self.index_dir}\n"
                f"Run 'python3 tfidf_indexer.py {self.authority_type}' first to build the index."
            )

        # Load config
        config_path = self.index_dir / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.use_stemming = config.get("use_stemming", True)

        if self.use_stemming:
            self.stemmer = PorterStemmer()

        # Load vocabulary
        vocab_path = self.index_dir / "vocabulary.json"
        with open(vocab_path, 'r', encoding='utf-8') as f:
            self.vocabulary = json.load(f)

        # Load IDF values
        idf_path = self.index_dir / "idf.json"
        with open(idf_path, 'r', encoding='utf-8') as f:
            self.idf = json.load(f)

        # Load documents (streaming for memory efficiency)
        docs_path = self.index_dir / "documents.ndjson"
        with open(docs_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                # Convert vector keys back to integers
                doc["vector"] = {int(k): v for k, v in doc["vector"].items()}
                self.documents.append(doc)

    def tokenize(self, text):
        """Tokenize and optionally stem text (same as indexer)."""
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        if self.use_stemming and self.stemmer:
            tokens = [self.stemmer.stem(t) for t in tokens]
        return tokens

    def _compute_query_vector(self, query):
        """Convert query string to TF-IDF vector."""
        tokens = self.tokenize(query)

        if not tokens:
            return {}

        # Compute term frequencies
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1

        # Compute TF-IDF
        vector = {}
        doc_len = len(tokens)

        for token, count in tf.items():
            if token in self.vocabulary:
                idx = self.vocabulary[token]
                tf_val = count / doc_len
                tfidf_val = tf_val * self.idf[idx]
                if tfidf_val > 0:
                    vector[idx] = tfidf_val

        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector.values())) if vector else 1.0
        if magnitude > 0:
            vector = {k: v / magnitude for k, v in vector.items()}

        return vector

    def _cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two sparse vectors."""
        # Vectors are already normalized, so dot product = cosine similarity
        dot_product = 0.0
        for idx, val in vec1.items():
            if idx in vec2:
                dot_product += val * vec2[idx]
        return dot_product

    def search(self, query, top_k=10, threshold=0.0, include_variants=True):
        """
        Search for similar headings.

        Args:
            query: Search query string
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0.0-1.0)
            include_variants: Include UF/variant entries in results

        Returns:
            List of results sorted by similarity score
        """
        query_vector = self._compute_query_vector(query)

        if not query_vector:
            return []

        # Compute similarities
        results = []
        query_lower = query.lower().strip()

        for doc in self.documents:
            if not include_variants and doc.get("is_variant", False):
                continue

            similarity = self._cosine_similarity(query_vector, doc["vector"])

            if similarity >= threshold:
                # Check for exact match
                exact_match = doc["heading"].lower() == query_lower

                result = {
                    "heading": doc["heading"],
                    "similarity_score": round(similarity, 4),
                    "exact_match": exact_match,
                    "is_variant": doc.get("is_variant", False),
                    "authority_type": self.authority_type,
                    **doc["metadata"]
                }
                results.append(result)

        # Sort by similarity (descending), then by exact match
        results.sort(key=lambda x: (x["similarity_score"], x["exact_match"]), reverse=True)

        return results[:top_k]

    def check_heading_authority(self, heading, threshold=0.8):
        """
        Check if a heading exists in the authority file.
        Compatible API with search_authority.py.

        Args:
            heading: Heading to check
            threshold: Minimum similarity for a match

        Returns:
            Dictionary with authority info, or None if not found
        """
        results = self.search(heading, top_k=1, threshold=threshold)

        if not results:
            return None

        best_match = results[0]

        # Format for backwards compatibility
        return {
            "authorized_heading": best_match["authorized_heading"],
            "found_in_line": None,  # Not applicable for TF-IDF
            "exact_match": best_match["exact_match"],
            "similarity_score": best_match["similarity_score"],
            "geographic_subdivision": best_match["geographic_subdivision"],
            "marc_field": best_match["marc_field"],
            "authority_type": self.authority_type,
            "broader_terms": best_match.get("broader_terms", []),
            "narrower_terms": best_match.get("narrower_terms", []),
            "used_for": best_match.get("used_for", []),
            "is_use_reference": best_match.get("is_use_reference", False)
        }

    def suggest_authorized_heading(self, search_term, threshold=0.5):
        """
        Find the authorized form of a heading.
        Compatible API with search_authority.py.

        Args:
            search_term: Term to search for
            threshold: Minimum similarity

        Returns:
            Tuple of (authorized_heading, is_exact_match, note)
        """
        results = self.search(search_term, top_k=5, threshold=threshold)

        if not results:
            return (search_term, False, f"Heading not found in {self.authority_type} authority file")

        best = results[0]

        # Check if this is a USE reference
        if best.get("is_use_reference"):
            note = f"USE '{best['authorized_heading']}' (searched term is a variant)"
        elif best["exact_match"]:
            note = "Exact match found"
        else:
            note = f"Similar heading found (similarity: {best['similarity_score']:.2f})"

        return (best["authorized_heading"], best["exact_match"], note)


def search_headings(query, top_k=10, threshold=0.0, authority_type="subjects", index_dir=None):
    """
    Convenience function to search headings.

    Args:
        query: Search query
        top_k: Number of results
        threshold: Minimum similarity (ignored for API-based searches)
        authority_type: Type of authority (subjects, genreforms, names)
        index_dir: Path to index directory (overrides authority_type)

    Returns:
        List of matching headings with metadata
    """
    # Use API for names authority
    if authority_type == "names" and not index_dir:
        from lcnaf_api import search_names
        return search_names(query, top_k=top_k)

    searcher = TFIDFSearcher(index_dir=index_dir, authority_type=authority_type)
    return searcher.search(query, top_k=top_k, threshold=threshold)


def check_heading_authority(heading, authority_type="subjects", index_dir=None):
    """
    Convenience function to check a heading's authority status.
    Compatible with search_authority.py API.

    Args:
        heading: Heading to check
        authority_type: Type of authority (subjects, genreforms, names)
        index_dir: Path to index directory (overrides authority_type)

    Returns:
        Dictionary with authority info or None
    """
    # Use API for names authority
    if authority_type == "names" and not index_dir:
        from lcnaf_api import check_name_authority
        return check_name_authority(heading)

    searcher = TFIDFSearcher(index_dir=index_dir, authority_type=authority_type)
    return searcher.check_heading_authority(heading)


def suggest_authorized_heading(search_term, authority_type="subjects", index_dir=None):
    """
    Convenience function to suggest authorized heading.
    Compatible with search_authority.py API.

    Args:
        search_term: Term to search for
        authority_type: Type of authority (subjects, genreforms, names)
        index_dir: Path to index directory (overrides authority_type)

    Returns:
        Tuple of (authorized_heading, is_exact_match, note)
    """
    searcher = TFIDFSearcher(index_dir=index_dir, authority_type=authority_type)
    return searcher.suggest_authorized_heading(search_term)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Search Library of Congress authority headings using TF-IDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authority types:
  subjects    LCSH Subject Headings (for 650, 651 fields) [default]
  genreforms  LCGFT Genre/Form Terms (for 655 fields)
  names       LCNAF Name Authority (for 600, 610 fields)

Examples:
  python3 tfidf_search.py "companion planting"              # Search subjects
  python3 tfidf_search.py "Essays" -a genreforms            # Search genre/forms
  python3 tfidf_search.py "vegetable garden" --top 5        # Limit results
  python3 tfidf_search.py "Tacos" --check                   # Check authority
        """
    )
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("-a", "--authority-type", type=str, default="subjects",
                       choices=list(AUTHORITY_TYPES.keys()),
                       help="Authority type to search (default: subjects)")
    parser.add_argument("--top", "-k", type=int, default=10, help="Number of results")
    parser.add_argument("--threshold", "-t", type=float, default=0.0, help="Minimum similarity score")
    parser.add_argument("--index-dir", type=str, default=None, help="Path to index directory")
    parser.add_argument("--no-variants", action="store_true", help="Exclude variant/UF entries")
    parser.add_argument("--check", action="store_true", help="Check authority status only")

    args = parser.parse_args()
    query = " ".join(args.query)

    try:
        # Use API for names authority type
        if args.authority_type == "names" and not args.index_dir:
            from lcnaf_api import LCNAFClient
            client = LCNAFClient()

            if args.check:
                result = client.check_heading(query)
                if result:
                    print(json.dumps({query: result}, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps({query: None}, indent=2))
            else:
                results = client.suggest(query, limit=args.top)
                print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            # Use local TF-IDF index for subjects/genreforms
            searcher = TFIDFSearcher(index_dir=args.index_dir, authority_type=args.authority_type)

            if args.check:
                result = searcher.check_heading_authority(query)
                if result:
                    print(json.dumps({query: result}, indent=2, ensure_ascii=False))
                else:
                    print(json.dumps({query: None}, indent=2))
            else:
                results = searcher.search(
                    query,
                    top_k=args.top,
                    threshold=args.threshold,
                    include_variants=not args.no_variants
                )
                print(json.dumps(results, indent=2, ensure_ascii=False))

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
