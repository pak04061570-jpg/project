"""
debug.py — วินิจฉัย Two-pass แสดงผลแยกรายบรรทัด
รัน: python debug.py <path_to_docx>
"""

import sys
from checker import (
    read_docx, pass1_word, pass2_syllable,
    word_tokenizer, syllable_tokenizer,
    is_likely_thai, split_thai_chunks,
    THAI_DICT, SYLLABLE_DICT,
)


def diagnose(filepath: str):
    paragraphs = read_docx(filepath)

    for line_num, text in paragraphs:
        print(f"\n{'─'*65}")
        print(f"บรรทัด {line_num}: {text}")

        # ── Pass 1 ──────────────────────────────────────────────────
        p1_errors, flagged = pass1_word(line_num, text)
        all_words = [w for w in word_tokenizer.word_tokenize(text) if is_likely_thai(w)]
        print(f"\n  [Pass 1 - Word]")
        print(f"  tokens              : {all_words}")
        print(f"  ✗ ไม่อยู่ใน word dict : {[e['wrong'] for e in p1_errors]}")

        # ── Pass 2 ──────────────────────────────────────────────────
        p2_errors = pass2_syllable(line_num, text, flagged)
        all_syls = []
        for chunk in split_thai_chunks(text):
            if is_likely_thai(chunk):
                all_syls.extend(syllable_tokenizer.word_tokenize(chunk))

        print(f"\n  [Pass 2 - Syllable]")
        print(f"  syllables                          : {all_syls}")
        print(f"  ✗ ไม่อยู่ใน syllable dict (ใหม่)  : {[e['wrong'] for e in p2_errors]}")

        print(f"\n  รวมจับได้บรรทัดนี้ : {len(p1_errors) + len(p2_errors)} รายการ")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        filepath = input("ใส่ path ของไฟล์: ").strip()
    else:
        filepath = sys.argv[1]
    diagnose(filepath)
