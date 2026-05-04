"""
main.py — CLI entry point
รับ path ไฟล์ .docx แล้วแสดงผลใน terminal
"""

import sys
from checker import check_file


def print_report(all_errors: list[dict]) -> None:
    if not all_errors:
        print("ไม่พบคำผิด ✓")
        return

    print(f"\n{'='*55}")
    print(f"  พบคำที่อาจผิด {len(all_errors)} คำ")
    print(f"{'='*55}")

    for err in all_errors:
        print(f"\n  บรรทัดที่ {err['line']} | คำที่ {err['position']}")
        print(f"  บริบท   : ...{err['context']}...")
        print(f"  คำผิด   : \"{err['wrong']}\"")
        print(f"  แนะนำ   : \"{err['best']}\"")
        if len(err["suggestions"]) > 1:
            others = ", ".join(f'"{s}"' for s in err["suggestions"] if s != err["best"])
            if others:
                print(f"  ตัวเลือกอื่น: {others}")

    print(f"\n{'='*55}")


def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = input("ใส่ path ของไฟล์ Word (.docx): ").strip()

    print(f"\nกำลังอ่านไฟล์: {filepath}")

    try:
        all_errors, total_lines = check_file(filepath)
    except FileNotFoundError:
        print(f"ไม่พบไฟล์: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
        sys.exit(1)

    print(f"พบ {total_lines} บรรทัดที่มีข้อความ\n")
    print("กำลังตรวจสอบคำผิด...")
    print_report(all_errors)


if __name__ == "__main__":
    main()
