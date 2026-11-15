#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "pymupdf",
# ]
# ///

import os
import pymupdf # pyrefly: ignore [missing-import]

def extract_text(filename):
    with pymupdf.open(filename) as document:
        return "\n".join(page.get_text() for page in document)


def get_pdf_list(dir_name):
    filename_list = []
    for x in os.listdir(dir_name):
        if x.endswith(".pdf"):
            filename_list.append(x)
    return filename_list

if __name__ == "__main__":
    pdfs_to_compare = get_pdf_list("output_files")

    for filename in pdfs_to_compare:
        text1 = extract_text(f"output_files/{filename}")
        text2 = extract_text(f"output_files-for-compare/{filename}")
        result = "equal" if text1 == text2 else "not equal"
        print(f"{filename} are {result}")
