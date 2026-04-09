"""Text normalization for queries and vendor fields."""

import re
import unicodedata

# Zero-width / invisible formatting → space (word boundary); then whitespace collapse merges runs.
_ZERO_WIDTH_RE = re.compile(
    r"[\u200b\u200c\u200d\u2060\ufeff]",
)

# Runs of underscores → word boundary (same role as punctuation below).
_UNDERSCORE_RUN_RE = re.compile(r"_+")

# Any character that is not a Unicode “word” char or whitespace → space.
_NON_WORD_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)

# Collapse all Unicode whitespace (incl. NBSP, tabs, newlines) to a single ASCII space.
_WHITESPACE_RUN_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """
    Normalize text for embedding and retrieval.

    Steps (in order):

    1. **NFKC** — compatibility decomposition + canonical composition (full-width
       Latin digits/letters, ligatures, etc. map to usual ASCII forms where applicable).
    2. **Zero-width / invisible** characters (ZWSP, ZWJ, BOM-as-ZWNBSP, …) become a **space**
       so adjacent tokens do not glue together.
    3. **Lowercase** and trim ends.
    4. **Underscores** — each run of `_` becomes a single space (not part of a “word”).
    5. **Punctuation & symbols** — every other non-word, non-whitespace character becomes
       a space (so hyphens and commas act as *boundaries*, not hard deletes).
    6. **Whitespace** — collapse any run of whitespace (tabs, newlines, NBSP, …) to one space.

    Letters and digits are kept per ``\\w`` with ``UNICODE`` (includes letters outside ASCII).
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = _ZERO_WIDTH_RE.sub(" ", t)
    t = t.lower().strip()
    t = _UNDERSCORE_RUN_RE.sub(" ", t)
    t = _NON_WORD_RE.sub(" ", t)
    t = _WHITESPACE_RUN_RE.sub(" ", t)
    return t.strip()


def normalized_token_set(text: str) -> frozenset[str]:
    """
    Tokens for overlap checks after the same pipeline as embedding/retrieval.

    Safe to call on text that is already ``normalize_text`` output (idempotent for typical ASCII).
    """
    n = normalize_text(text)
    if not n:
        return frozenset()
    return frozenset(t for t in n.split() if t)


def compact_for_identifier_match(text: str) -> str:
    """
    Normalized string with spaces removed, for VAT / company-code substring checks
    against a query compacted the same way.
    """
    return normalize_text(text or "").replace(" ", "")
