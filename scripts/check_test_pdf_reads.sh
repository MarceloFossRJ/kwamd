#!/bin/sh
# Fail if a test reads a PDF's text with a bare get_text(), outside the helpers in
# tests/conftest.py that normalise it. Calls with an argument ("dict", "words")
# are layout reads and are allowed.
found=$(grep -rnE '\.get_text\(\)' tests --include='*.py' | grep -v '^tests/conftest\.py:')
if [ -n "$found" ]; then
  echo "$found" >&2
  echo "Read PDF text through the helpers in tests/conftest.py (pdf_text, page_of)." >&2
  exit 1
fi
