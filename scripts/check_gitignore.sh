#!/bin/sh
# Fail if the repo's .gitignore stops ignoring files that hold secrets or logs.
# Personal ignore files are switched off so only the repo's rules count.
status=0
for path in .pypirc .env debug.log other.log; do
  if ! git -c core.excludesFile=/dev/null check-ignore -q --no-index "$path"; then
    echo ".gitignore: '$path' is no longer ignored" >&2
    status=1
  fi
done
exit $status
