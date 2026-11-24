# 02: Images in a Markdown Source

Status: ready-for-agent
Blocked by: 01

## Problem

Images in a Markdown Source need handling. See `../spec.md` (stories 11–13).

## Acceptance criteria

- A local image (path relative to the Markdown file's folder, `../` included; raster or SVG) is embedded in the PDF.
- A remote image (`http://` or `https://`) appears as its alt text. There is one warning per run giving the count, the PDF is written, and the exit code is 0. No network call is made.
- A missing, unreadable or not-an-image local image appears as its alt text with one warning naming the path, and the exit code is 0.
- Warnings go to stderr only, so stdout is still just the Target path.
