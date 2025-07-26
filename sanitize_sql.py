#!/usr/bin/env python3
"""
sanitize_sql.py  input.sql  [output.sql]

Strips BOMs, NULL bytes, and other control chars that can break MySQL imports.
Keeps tabs/newlines/CR. Defaults to writing <input>_clean.sql if output not given.
"""

import sys
import codecs
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python sanitize_sql.py dump.sql [dump_clean.sql]")
        sys.exit(1)

    infile = Path(sys.argv[1])
    outfile = Path(sys.argv[2]) if len(sys.argv) >= 3 else infile.with_name(infile.stem + "_clean.sql")

    raw = infile.read_bytes()

    # Strip common BOMs if present
    for bom in (
        codecs.BOM_UTF8,
        codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE,
        codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE
    ):
        if raw.startswith(bom):
            raw = raw[len(bom):]
            break

    # Decode as UTF‑8, drop undecodable bytes
    txt = raw.decode("utf-8", errors="ignore")

    # Remove NULLs and control chars except \t \n \r
    txt = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", txt)

    # Normalize newlines to \n (optional)
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")

    outfile.write_text(txt, encoding="utf-8")
    print(f"✅ Cleaned file written to: {outfile}")

if __name__ == "__main__":
    main()
