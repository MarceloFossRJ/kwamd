#!/bin/sh
# Fail if .gitignore stops ignoring files that hold secrets or logs.
status=0
for path in .pypirc .env debug.log; do
  if ! git check-ignore -q --no-index "$path"; then
    echo ".gitignore: '$path' is no longer ignored" >&2
    status=1
  fi
done
exit $status
