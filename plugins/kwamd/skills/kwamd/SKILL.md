---
name: kwamd
description: Convert PDF ↔ Markdown with the kwamd command. Use when reading, summarising or quoting a PDF's text, or when producing a PDF from a Markdown file.
---

# kwamd

`kwamd <source> [target]` converts a **Source** into a **Target** in the other format. A PDF Source (recognised by its content) becomes Markdown; a `.md`/`.markdown` Source becomes a PDF. kwamd never overwrites: when the Target exists it writes `name (1).md`, `name (2).md`, … That numbered name is the intended result; leave existing files exactly as they are.

## Steps

1. **Check it's installed.** Run `command -v kwamd`. If nothing prints, stop and tell the user to install it from a clone of https://github.com/MarceloFossRJ/kwamd with `uv tool install .`. Installing is the user's call: run only the `kwamd` already on `PATH`, never a copy fetched with `uvx`, `pip` or a download.

2. **Choose the Target.**
   - The user wants the file: pass the path they named, or omit `target` (kwamd then writes `<name>.md` or `<name>.pdf` in the current folder).
   - You only need to read the result: pass a target inside your scratchpad directory (or a `mktemp -d` folder), so the user's project stays clean.

3. **Run it** and read the outcome by exit code:

   | Exit | Meaning | What you do |
   | ---- | ------- | ----------- |
   | `0` | Written. stdout is the Target's absolute path, one line. | Use exactly that path: read it, or report it to the user. It may be a numbered `(n)` name. |
   | `1` | Source or Target problem. stderr has one `kwamd: error: …` line. | Report the error. If it says the Source is **password-protected**, tell the user to run `! kwamd <source> [target]` themselves: kwamd then asks them for the password at the terminal, and the password stays out of this conversation. |
   | `2` | Wrong usage. | Fix the command line and run again. |
   | `130` | Interrupted. | Report it and stop. |

4. **Relay every `kwamd: warning:` line**, even on exit 0:
   - **Scanned Source** ("Source looks scanned"): the PDF's pages are images and kwamd has no OCR, so the Markdown may be nearly empty. Tell the user this before using the Markdown, and present what you read as partial.
   - **Markdown → PDF image warnings** (remote, missing or unusable images): the PDF was still written with alt text in their place. Give the user the PDF path together with the warnings.
