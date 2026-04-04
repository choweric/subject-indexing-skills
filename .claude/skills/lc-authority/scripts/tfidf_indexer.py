#!/usr/bin/env python3
"""
TF-IDF Index Builder for Library of Congress Authority Files

Builds searchable TF-IDF indexes from LC authority NDJSON files (MADS/RDF format),
preserving all hierarchical metadata (BT, NT, UF, geographic subdivision).

Supported authority types:
  - subjects: LCSH Subject Headings (for 650, 651 fields)
  - genreforms: LCGFT Genre/Form Terms (for 655 fields)
  - names: LCNAF Name Authority (for 600, 610 fields) [future]

Usage:
    python3 tfidf_indexer.py subjects      # Build LCSH index
    python3 tfidf_indexer.py genreforms    # Build LCGFT index
    python3 tfidf_indexer.py --all         # Build all indexes
"""

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path


# Simple Porter Stemmer implementation (pure Python, no dependencies)
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
        """Count VC sequences (consonant-vowel patterns)."""
        m = 0
        i = 0
        n = len(word)

        # Skip initial consonants
        while i < n and self._is_consonant(word, i):
            i += 1

        while i < n:
            # Count vowel sequence
            while i < n and not self._is_consonant(word, i):
                i += 1
            if i >= n:
                break
            m += 1
            # Count consonant sequence
            while i < n and self._is_consonant(word, i):
                i += 1

        return m

    def _ends_with(self, word, suffix):
        return word.endswith(suffix)

    def _replace_suffix(self, word, suffix, replacement):
        if word.endswith(suffix):
            return word[:-len(suffix)] + replacement
        return word

    def stem(self, word):
        """Stem a single word."""
        if len(word) < 3:
            return word

        word = word.lower()

        # Step 1a: plurals
        if word.endswith('sses'):
            word = word[:-2]
        elif word.endswith('ies'):
            word = word[:-2]
        elif word.endswith('ss'):
            pass
        elif word.endswith('s'):
            word = word[:-1]

        # Step 1b: -ed, -ing
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

        # Step 1c: y -> i
        if word.endswith('y') and len(word) > 2:
            if any(c in self.vowels for c in word[:-1]):
                word = word[:-1] + 'i'

        # Step 2: common suffixes
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

        # Step 3
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

        # Step 4: remove common endings
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

        # Step 5a: remove trailing 'e'
        if word.endswith('e'):
            stem = word[:-1]
            if self._measure(stem) > 1:
                word = stem
            elif self._measure(stem) == 1:
                # Check if stem ends with CVC where last C is not w, x, y
                if len(stem) >= 3:
                    # Use positive indices to avoid issues
                    n = len(stem)
                    if (self._is_consonant(stem, n - 3) and
                        not self._is_consonant(stem, n - 2) and
                        self._is_consonant(stem, n - 1) and
                        stem[-1] not in 'wxy'):
                        pass  # Keep the 'e'
                    else:
                        word = stem

        # Step 5b: remove double consonant
        if word.endswith('ll') and self._measure(word[:-1]) > 1:
            word = word[:-1]

        return word


class TFIDFIndexer:
    """Builds TF-IDF index from LCSH authority file."""

    def __init__(self, use_stemming=True):
        self.stemmer = PorterStemmer() if use_stemming else None
        self.use_stemming = use_stemming

        # Index data structures
        self.vocabulary = {}  # term -> index
        self.idf = []  # IDF values
        self.documents = []  # List of {heading, vector, metadata, is_variant}

        # Temporary structures for building
        self._doc_freq = defaultdict(int)  # term -> document frequency
        self._all_docs = []  # Temporary storage during first pass

    def tokenize(self, text):
        """Tokenize and optionally stem text."""
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())

        if self.use_stemming:
            tokens = [self.stemmer.stem(t) for t in tokens]

        return tokens

    def _extract_label(self, label_obj):
        """Extract English label from MADS label object."""
        if isinstance(label_obj, dict):
            if label_obj.get("@language") == "en":
                return label_obj.get("@value", "")
        elif isinstance(label_obj, str):
            return label_obj
        return ""

    def _extract_metadata(self, item):
        """Extract all metadata from an authority record."""
        metadata = {
            "geographic_subdivision": "Not authorized",
            "marc_field": None,
            "broader_terms": [],
            "narrower_terms": [],
            "used_for": []
        }

        # MARC key
        marc_key = item.get("bflc:marcKey", "")
        if marc_key:
            metadata["marc_field"] = marc_key

        # Geographic subdivision
        collections = item.get("madsrdf:isMemberOfMADSCollection", [])
        for coll in collections:
            coll_id = coll.get("@id", "") if isinstance(coll, dict) else str(coll)
            if "collection_SubdivideGeographically" in coll_id:
                metadata["geographic_subdivision"] = "May subdivide geographically"
                break

        # Broader terms
        broader = item.get("madsrdf:hasBroaderAuthority", [])
        if not isinstance(broader, list):
            broader = [broader]
        for b in broader:
            if isinstance(b, dict):
                metadata["broader_terms"].append(b.get("@id", ""))
            else:
                metadata["broader_terms"].append(str(b))

        # Narrower terms
        narrower = item.get("madsrdf:hasNarrowerAuthority", [])
        if not isinstance(narrower, list):
            narrower = [narrower]
        for n in narrower:
            if isinstance(n, dict):
                metadata["narrower_terms"].append(n.get("@id", ""))
            else:
                metadata["narrower_terms"].append(str(n))

        # Variant labels are extracted in parse_authority_file using graph lookup
        # (madsrdf:hasVariant contains blank node references, not direct labels)

        return metadata

    def _extract_variants_from_graph(self, graph, variant_ids):
        """Look up variant labels from graph by their blank node IDs."""
        variant_labels = []

        # Build lookup of @id -> item
        id_to_item = {item.get("@id"): item for item in graph if "@id" in item}

        for vid in variant_ids:
            vid_str = vid.get("@id") if isinstance(vid, dict) else str(vid)
            if vid_str in id_to_item:
                variant_item = id_to_item[vid_str]
                # Check if this is a Variant type
                item_types = variant_item.get("@type", [])
                if "madsrdf:Variant" in item_types:
                    vlabel = variant_item.get("madsrdf:variantLabel", {})
                    label_text = self._extract_label(vlabel)
                    if label_text:
                        variant_labels.append(label_text)

        return variant_labels

    def parse_authority_file(self, authority_file_path):
        """First pass: parse authority file and collect document frequencies."""
        print(f"Parsing authority file: {authority_file_path}")

        line_count = 0
        authority_count = 0
        variant_count = 0

        with open(authority_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue

                line_count += 1
                if line_count % 50000 == 0:
                    print(f"  Processed {line_count} lines...")

                try:
                    record = json.loads(line)
                    graph = record.get("@graph", [])

                    for item in graph:
                        # Only process Authority records with authoritative labels
                        if "madsrdf:authoritativeLabel" not in item:
                            continue
                        if "madsrdf:Authority" not in item.get("@type", []):
                            continue

                        label = item.get("madsrdf:authoritativeLabel", {})
                        pref_label = self._extract_label(label)

                        if not pref_label:
                            continue

                        # Extract metadata
                        metadata = self._extract_metadata(item)
                        metadata["authorized_heading"] = pref_label

                        # Extract variant labels (UF references) from graph
                        variant_refs = item.get("madsrdf:hasVariant", [])
                        if not isinstance(variant_refs, list):
                            variant_refs = [variant_refs]
                        metadata["used_for"] = self._extract_variants_from_graph(graph, variant_refs)

                        # Tokenize main heading
                        tokens = self.tokenize(pref_label)

                        # Update document frequency
                        unique_tokens = set(tokens)
                        for token in unique_tokens:
                            self._doc_freq[token] += 1

                        # Store document
                        self._all_docs.append({
                            "heading": pref_label,
                            "tokens": tokens,
                            "metadata": metadata,
                            "is_variant": False
                        })
                        authority_count += 1

                        # Also index variant labels (UF references)
                        for variant_label in metadata["used_for"]:
                            variant_tokens = self.tokenize(variant_label)
                            unique_variant_tokens = set(variant_tokens)
                            for token in unique_variant_tokens:
                                self._doc_freq[token] += 1

                            # Variant points to the authorized heading
                            variant_metadata = {
                                "authorized_heading": pref_label,
                                "geographic_subdivision": metadata["geographic_subdivision"],
                                "marc_field": metadata["marc_field"],
                                "broader_terms": metadata["broader_terms"],
                                "narrower_terms": metadata["narrower_terms"],
                                "used_for": [],
                                "is_use_reference": True
                            }

                            self._all_docs.append({
                                "heading": variant_label,
                                "tokens": variant_tokens,
                                "metadata": variant_metadata,
                                "is_variant": True
                            })
                            variant_count += 1

                except json.JSONDecodeError:
                    continue

        print(f"  Total lines: {line_count}")
        print(f"  Authority records: {authority_count}")
        print(f"  Variant entries (UF): {variant_count}")
        print(f"  Unique terms: {len(self._doc_freq)}")

    def build_index(self):
        """Second pass: compute IDF and TF-IDF vectors."""
        print("Building TF-IDF index...")

        n_docs = len(self._all_docs)

        # Build vocabulary (sorted for consistency)
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(self._doc_freq.keys()))}

        # Compute IDF values
        self.idf = [0.0] * len(self.vocabulary)
        for term, idx in self.vocabulary.items():
            df = self._doc_freq[term]
            self.idf[idx] = math.log(n_docs / df) if df > 0 else 0.0

        # Compute TF-IDF vectors for each document
        for i, doc in enumerate(self._all_docs):
            if (i + 1) % 100000 == 0:
                print(f"  Vectorized {i + 1}/{n_docs} documents...")

            tokens = doc["tokens"]

            # Compute term frequencies
            tf = defaultdict(int)
            for token in tokens:
                tf[token] += 1

            # Compute TF-IDF (sparse representation)
            vector = {}
            doc_len = len(tokens) if tokens else 1

            for token, count in tf.items():
                if token in self.vocabulary:
                    idx = self.vocabulary[token]
                    tf_val = count / doc_len
                    tfidf_val = tf_val * self.idf[idx]
                    if tfidf_val > 0:
                        vector[idx] = tfidf_val

            # Normalize vector (for cosine similarity)
            magnitude = math.sqrt(sum(v * v for v in vector.values())) if vector else 1.0
            if magnitude > 0:
                vector = {k: v / magnitude for k, v in vector.items()}

            self.documents.append({
                "heading": doc["heading"],
                "vector": vector,
                "metadata": doc["metadata"],
                "is_variant": doc["is_variant"]
            })

        # Clear temporary structures
        self._doc_freq.clear()
        self._all_docs.clear()

        print(f"  Index built with {len(self.documents)} documents")

    def save_index(self, output_dir):
        """Save index to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Saving index to {output_path}...")

        # Save vocabulary
        vocab_path = output_path / "vocabulary.json"
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f)
        print(f"  Vocabulary: {vocab_path} ({vocab_path.stat().st_size / 1024 / 1024:.1f} MB)")

        # Save IDF values
        idf_path = output_path / "idf.json"
        with open(idf_path, 'w', encoding='utf-8') as f:
            json.dump(self.idf, f)
        print(f"  IDF: {idf_path} ({idf_path.stat().st_size / 1024 / 1024:.1f} MB)")

        # Save documents (vectors + metadata)
        # Use NDJSON for streaming load
        docs_path = output_path / "documents.ndjson"
        with open(docs_path, 'w', encoding='utf-8') as f:
            for doc in self.documents:
                # Convert vector keys to strings for JSON
                doc_out = {
                    "heading": doc["heading"],
                    "vector": {str(k): v for k, v in doc["vector"].items()},
                    "metadata": doc["metadata"],
                    "is_variant": doc["is_variant"]
                }
                f.write(json.dumps(doc_out, ensure_ascii=False) + "\n")
        print(f"  Documents: {docs_path} ({docs_path.stat().st_size / 1024 / 1024:.1f} MB)")

        # Save config
        config_path = output_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                "use_stemming": self.use_stemming,
                "n_documents": len(self.documents),
                "n_terms": len(self.vocabulary)
            }, f, indent=2)
        print(f"  Config: {config_path}")

        print("Index saved successfully!")


# Authority type configurations
AUTHORITY_TYPES = {
    "subjects": {
        "file": "subjects.madsrdf.jsonld",
        "description": "LCSH Subject Headings (650, 651 fields)",
    },
    "genreforms": {
        "file": "genreForms.madsrdf.jsonld",
        "description": "LCGFT Genre/Form Terms (655 fields)",
    },
    "names": {
        "file": "names.madsrdf.jsonld",
        "description": "LCNAF Name Authority (600, 610 fields)",
    },
}


def build_authority_index(authority_type, script_dir, no_stemming=False):
    """Build index for a specific authority type."""
    if authority_type not in AUTHORITY_TYPES:
        print(f"Error: Unknown authority type '{authority_type}'", file=sys.stderr)
        print(f"Available types: {', '.join(AUTHORITY_TYPES.keys())}", file=sys.stderr)
        return False

    config = AUTHORITY_TYPES[authority_type]
    authority_file = script_dir.parent / "references" / config["file"]
    output_dir = script_dir / "index" / authority_type

    print(f"\n{'='*60}")
    print(f"Building index: {authority_type}")
    print(f"Description: {config['description']}")
    print(f"{'='*60}")

    if not authority_file.exists():
        print(f"Error: Authority file not found: {authority_file}", file=sys.stderr)
        print(f"Please download from: https://id.loc.gov/download/", file=sys.stderr)
        return False

    # Build index
    indexer = TFIDFIndexer(use_stemming=not no_stemming)
    indexer.parse_authority_file(authority_file)
    indexer.build_index()
    indexer.save_index(output_dir)
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build TF-IDF index from Library of Congress authority files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authority types:
  subjects    LCSH Subject Headings (for 650, 651 fields)
  genreforms  LCGFT Genre/Form Terms (for 655 fields)
  names       LCNAF Name Authority (for 600, 610 fields)

Examples:
  python3 tfidf_indexer.py subjects       # Build LCSH index only
  python3 tfidf_indexer.py genreforms     # Build LCGFT index only
  python3 tfidf_indexer.py --all          # Build all available indexes
        """
    )
    parser.add_argument("authority_type", nargs="?", default=None,
                       help="Authority type to index (subjects, genreforms, names)")
    parser.add_argument("--all", action="store_true",
                       help="Build indexes for all available authority files")
    parser.add_argument("--no-stemming", action="store_true",
                       help="Disable Porter stemming")

    args = parser.parse_args()

    script_dir = Path(__file__).parent

    if args.all:
        # Build all available indexes
        success_count = 0
        for auth_type in AUTHORITY_TYPES:
            auth_file = script_dir.parent / "references" / AUTHORITY_TYPES[auth_type]["file"]
            if auth_file.exists():
                if build_authority_index(auth_type, script_dir, args.no_stemming):
                    success_count += 1
            else:
                print(f"\nSkipping {auth_type}: file not found ({AUTHORITY_TYPES[auth_type]['file']})")
        print(f"\n{'='*60}")
        print(f"Completed: {success_count} index(es) built")
    elif args.authority_type:
        # Build specific index
        if not build_authority_index(args.authority_type, script_dir, args.no_stemming):
            sys.exit(1)
    else:
        # No arguments - show help
        parser.print_help()
        print("\nAvailable authority files:")
        for auth_type, config in AUTHORITY_TYPES.items():
            auth_file = script_dir.parent / "references" / config["file"]
            status = "✓ Found" if auth_file.exists() else "✗ Not found"
            print(f"  {auth_type:12} {status:15} {config['description']}")


if __name__ == "__main__":
    main()
