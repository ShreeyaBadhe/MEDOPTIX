#!/usr/bin/env python3
import argparse
import os
import re

INSERT_RE = re.compile(r"^\s*INSERT\s+INTO\s", re.IGNORECASE)

def split_values_block(sql_block: str, rows_per_insert: int):
    """
    Given one full INSERT ... VALUES (...),(...), ...; statement,
    return a list of smaller INSERT statements with <= rows_per_insert tuples.
    """
    # find the "VALUES" keyword (case-insensitive)
    m = re.search(r"\bVALUES\b", sql_block, re.IGNORECASE)
    if not m:
        return [sql_block]  # nothing to split

    head = sql_block[: m.end()]  # up to and including VALUES
    tail = sql_block[m.end():].strip().rstrip(";")

    # Split tail into tuples by scanning parentheses balance
    tuples = []
    start = 0
    depth = 0
    for i, ch in enumerate(tail):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                tuples.append(tail[start : i + 1])
        # commas inside tuples are ignored because depth > 0

    # Rebuild smaller INSERTs
    out = []
    for i in range(0, len(tuples), rows_per_insert):
        chunk = tuples[i : i + rows_per_insert]
        stmt = f"{head} {', '.join(chunk)};"
        out.append(stmt)
    return out


def process(in_path: str, out_path: str, rows_per_insert: int):
    with open(in_path, "r", encoding="utf-8", errors="ignore") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:

        buffer = []
        in_insert = False

        for line in fin:
            if not in_insert and INSERT_RE.match(line):
                # starting a new INSERT
                in_insert = True
                buffer = [line]
                # keep accumulating until we hit ';'
                if line.rstrip().endswith(";\n") or line.rstrip().endswith(";"):
                    # single-line INSERT
                    sql_block = "".join(buffer)
                    for stmt in split_values_block(sql_block, rows_per_insert):
                        fout.write(stmt + "\n")
                    in_insert = False
            elif in_insert:
                buffer.append(line)
                if ";" in line:
                    # end of INSERT
                    sql_block = "".join(buffer)
                    for stmt in split_values_block(sql_block, rows_per_insert):
                        fout.write(stmt + "\n")
                    in_insert = False
            else:
                # non-INSERT lines just pass through
                fout.write(line)

        # in case file ended inside an INSERT (malformed), flush it
        if in_insert and buffer:
            sql_block = "".join(buffer)
            for stmt in split_values_block(sql_block, rows_per_insert):
                fout.write(stmt + "\n")


def main():
    p = argparse.ArgumentParser(description="Split large multi-row INSERTs into smaller chunks.")
    p.add_argument("input", help="Path to original SQL dump (e.g., claims.sql)")
    p.add_argument("output", help="Path to write cleaned/split SQL (e.g., claims_split.sql)")
    p.add_argument("--rows-per-insert", type=int, default=500,
                   help="Max rows per INSERT statement (default: 500)")
    args = p.parse_args()

    process(args.input, args.output, args.rows_per_insert)
    print(f"✅ Done. Wrote: {args.output}")

if __name__ == "__main__":
    main()
