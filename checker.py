"""
checker.py — logic ตรวจสอบคำผิดภาษาไทยทั้งหมด
ไฟล์นี้ไม่มี UI ใดๆ เพื่อให้ CLI และ UI import ใช้ร่วมกันได้

แนวทางการตรวจสอบ (Two-pass):
  Pass 1 — Word level
    word tokenize ด้วย newmm + THAI_DICT
    คำไหนไม่อยู่ใน THAI_DICT → flag ทันที
    จับได้: คำผิดที่ tokenizer รวมออกมาเป็น unknown token เดี่ยว

  Pass 2 — Syllable level
    ตัดข้อความเป็นพยางค์ด้วย newmm + SYLLABLE_DICT
    พยางค์ไหนไม่อยู่ใน SYLLABLE_DICT → flag
    จับได้เพิ่ม: คำผิดที่ Pass 1 พลาดเพราะ tokenizer แตกเป็น valid word
                 แต่สร้างพยางค์ที่ไม่ valid เช่น "กาารทดสอบ" → "ารทด"

  ข้อจำกัด: คำผิดที่แตกเป็นทั้ง valid word และ valid syllable ทุกตัว
             เช่น "พัทนา" → "พัท"+"นา" จะยังพลาด
             ต้องใช้ Language Model เพื่อแก้ปัญหานี้ได้จริง
"""

from docx import Document
from pythainlp.tokenize import Tokenizer
from pythainlp.spell import spell, correct
from pythainlp.corpus import thai_syllables, thai_words

# ── Dictionaries โหลดครั้งเดียวตอน import ────────────────────────────────────
THAI_DICT     = thai_words()
SYLLABLE_DICT = thai_syllables()

# Tokenizer ทั้งสองใช้ newmm engine แต่ต่าง custom_dict
# ทำให้ tokenization และ membership check ใช้ dictionary ชุดเดียวกันเสมอ
word_tokenizer     = Tokenizer(custom_dict=THAI_DICT,     engine="newmm")
syllable_tokenizer = Tokenizer(custom_dict=SYLLABLE_DICT, engine="newmm")

# cache ผล spell()/correct() — ทั้งสองฟังก์ชัน O(dict_size) ต่อการเรียก
# คำเดียวกันที่ผิดซ้ำหลายบรรทัดจะไม่ถูกคำนวณซ้ำ
_spell_cache: dict[str, tuple[str, list[str]]] = {}


def read_docx(filepath: str) -> list[tuple[int, str]]:
    """อ่านไฟล์ .docx คืน list ของ (เลขบรรทัด, ข้อความ)"""
    doc = Document(filepath)
    return [
        (i, para.text.strip())
        for i, para in enumerate(doc.paragraphs, start=1)
        if para.text.strip()
    ]


def is_likely_thai(text: str) -> bool:
    """คืน True ถ้าข้อความประกอบด้วยอักษรไทยล้วน (U+0E00–U+0E7F)"""
    return bool(text) and all("฀" <= ch <= "๿" for ch in text)


def split_thai_chunks(text: str) -> list[str]:
    """
    แบ่ง text เป็น chunk ไทย / ไม่ใช่ไทย
    ใช้ list buffer แทน string concat เพื่อหลีกเลี่ยง O(n²) copy

    ตัวอย่าง: "ส่ง report ภายใน 3 วัน"
              → ["ส่ง ", "report", " ภายใน ", "3", " วัน"]
    """
    if not text:
        return []

    chunks: list[str] = []
    buf: list[str] = []
    current_is_thai = "฀" <= text[0] <= "๿"

    for ch in text:
        ch_is_thai = "฀" <= ch <= "๿"
        if ch_is_thai != current_is_thai:
            chunks.append("".join(buf))
            buf = [ch]
            current_is_thai = ch_is_thai
        else:
            buf.append(ch)

    if buf:
        chunks.append("".join(buf))
    return chunks


def _make_error(wrong: str, line: int, position: int, context: str) -> dict:
    """
    สร้าง dict ผลการตรวจเป็นรูปแบบกลาง ใช้ร่วมกันทั้งสอง pass
    ผล spell()/correct() ถูก cache ตาม wrong word เพื่อไม่คำนวณซ้ำ
    """
    if wrong not in _spell_cache:
        _spell_cache[wrong] = (correct(wrong), spell(wrong)[:5])
    best, suggestions = _spell_cache[wrong]
    return {
        "wrong":       wrong,
        "best":        best,
        "suggestions": suggestions,
        "line":        line,
        "position":    position,
        "context":     context,
    }


def pass1_word(line_num: int, text: str) -> tuple[list[dict], set[str]]:
    """
    Pass 1: word tokenize → เช็คแต่ละคำกับ THAI_DICT
    คืน (errors, flagged_words) โดย flagged_words ส่งให้ Pass 2 ใช้ dedup
    """
    tokens = word_tokenizer.word_tokenize(text)
    errors: list[dict] = []
    flagged: set[str] = set()

    for idx, word in enumerate(tokens):
        if is_likely_thai(word) and word not in THAI_DICT:
            errors.append(_make_error(word, line_num, idx + 1, text))
            flagged.add(word)

    return errors, flagged


def pass2_syllable(line_num: int, text: str, skip_words: set[str]) -> list[dict]:
    """
    Pass 2: syllable tokenize → เช็คแต่ละพยางค์กับ SYLLABLE_DICT
    ทำงานทีละ chunk ไทย เพื่อกัน ตัวเลข/อังกฤษ รบกวนการตัด
    skip_words คือคำที่ Pass 1 จับแล้ว ใช้ป้องกันผลซ้ำ
    """
    errors: list[dict] = []
    global_pos = 0

    for chunk in split_thai_chunks(text):
        if not is_likely_thai(chunk):
            # เพิ่ม position ตาม len จริงของ chunk ไม่ใช่แค่ 1
            global_pos += len(chunk)
            continue

        for syl in syllable_tokenizer.word_tokenize(chunk):
            if is_likely_thai(syl) and syl not in skip_words and syl not in SYLLABLE_DICT:
                errors.append(_make_error(syl, line_num, global_pos + 1, text))
            global_pos += len(syl)

    return errors


def check_paragraph(line_num: int, text: str) -> list[dict]:
    """รัน Two-pass แล้วรวมผลลัพธ์"""
    p1_errors, flagged_words = pass1_word(line_num, text)
    p2_errors = pass2_syllable(line_num, text, flagged_words)
    return p1_errors + p2_errors


def check_file(filepath: str) -> tuple[list[dict], int]:
    """
    ตรวจสอบทั้งไฟล์ คืน (list ของ error ทั้งหมด, จำนวนบรรทัดที่มีข้อความ)
    entry point หลักที่ทั้ง CLI และ UI เรียกใช้
    """
    paragraphs = read_docx(filepath)
    all_errors = []
    for line_num, text in paragraphs:
        all_errors.extend(check_paragraph(line_num, text))
    return all_errors, len(paragraphs)
