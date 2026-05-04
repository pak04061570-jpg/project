"""
app.py — PySide6 UI สำหรับตรวจสอบคำผิดภาษาไทย
Layout แบบ master-detail: รายการคำผิด (ซ้าย) + รายละเอียด (ขวา)
ไม่มี business logic — import ทั้งหมดจาก checker.py และ theme.py
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QTextBrowser, QFrame, QFileDialog, QStatusBar, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QCursor

from checker import check_file
from theme import DARK, LIGHT, build_qss


# ── Background worker ─────────────────────────────────────────────────────────

class CheckWorker(QThread):
    """
    รัน check_file() ใน QThread แยก
    PySide6 ใช้ Signal เพื่อส่งผลกลับ main thread อย่าง thread-safe
    ห้าม update widget โดยตรงจาก thread นี้
    """
    finished       = Signal(list, int)
    error_occurred = Signal(str)

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            errors, total = check_file(self.filepath)
            self.finished.emit(errors, total)
        except FileNotFoundError:
            self.error_occurred.emit(f"ไม่พบไฟล์: {self.filepath}")
        except Exception as e:
            self.error_occurred.emit(str(e))


# ── Error card widget ─────────────────────────────────────────────────────────

class ErrorCard(QWidget):
    """
    Widget สำหรับแต่ละรายการในรายการคำผิด
    ใช้ QListWidget.setItemWidget() เพื่อ embed เข้าไปใน list item
    """
    def __init__(self, error: dict, c: dict, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Accent bar สีแดงซ้าย บ่งบอกว่าเป็น error item
        accent = QFrame()
        accent.setFixedWidth(3)
        accent.setStyleSheet(f"background: {c['error']}; border-radius: 2px;")

        info = QVBoxLayout()
        info.setSpacing(2)

        line_lbl = QLabel(f"บรรทัด {error['line']}")
        line_lbl.setStyleSheet(f"color: {c['subtext']}; font-size: 12px;")

        word_lbl = QLabel(error["wrong"])
        word_lbl.setStyleSheet(f"color: {c['error']}; font-weight: 600; font-size: 14px;")

        info.addWidget(line_lbl)
        info.addWidget(word_lbl)

        layout.addWidget(accent)
        layout.addLayout(info)
        layout.addStretch()


# ── Detail panel ──────────────────────────────────────────────────────────────

class DetailPanel(QFrame):
    """
    แสดงรายละเอียดของ error ที่เลือกจาก list:
      - คำผิด (แดง) → คำแนะนำที่ดีที่สุด (เขียว)
      - บริบทในเอกสารพร้อม highlight คำผิด
      - ปุ่มตัวเลือกอื่น
    """
    def __init__(self, c: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("detail_panel")
        self._c = c
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # คำผิด → แนะนำ
        top = QHBoxLayout()
        self.wrong_lbl = QLabel("—")
        self.wrong_lbl.setObjectName("wrong_word")
        arrow = QLabel("→")
        arrow.setObjectName("arrow_label")
        self.best_lbl = QLabel("—")
        self.best_lbl.setObjectName("best_word")
        top.addWidget(self.wrong_lbl)
        top.addWidget(arrow)
        top.addWidget(self.best_lbl)
        top.addStretch()

        div = QFrame()
        div.setObjectName("divider")
        div.setFixedHeight(1)

        ctx_label = QLabel("บริบท")
        ctx_label.setObjectName("section_label")

        # QTextBrowser รองรับ HTML เพื่อให้ highlight คำผิดด้วยสีได้
        self.ctx_box = QTextBrowser()
        self.ctx_box.setObjectName("ctx_box")
        self.ctx_box.setFixedHeight(90)
        self.ctx_box.setOpenLinks(False)

        sug_label = QLabel("ตัวเลือกอื่น")
        sug_label.setObjectName("section_label")

        # sug_row ใช้ addStretch() ปลายไว้เพื่อไม่ให้ปุ่มยืดเต็ม row
        self.sug_row = QHBoxLayout()
        self.sug_row.setSpacing(8)
        self.sug_row.addStretch()

        root.addLayout(top)
        root.addWidget(div)
        root.addWidget(ctx_label)
        root.addWidget(self.ctx_box)
        root.addWidget(sug_label)
        root.addLayout(self.sug_row)
        root.addStretch()

    def show_error(self, error: dict):
        self.wrong_lbl.setText(error["wrong"])
        self.best_lbl.setText(error["best"] or "—")

        # Highlight คำผิดในบริบทด้วย HTML — ใช้ hex สี + 33 (opacity ~20%)
        ctx   = error["context"]
        wrong = error["wrong"]
        highlighted = ctx.replace(
            wrong,
            f'<span style="background:{self._c["error"]}33;'
            f'color:{self._c["error"]};font-weight:bold;">{wrong}</span>',
        )
        self.ctx_box.setHtml(
            f'<div style="font-family:Segoe UI,Tahoma,sans-serif;'
            f'font-size:14px;color:{self._c["text"]};">{highlighted}</div>'
        )

        # ล้างปุ่ม suggestion เก่า (เก็บ stretch ที่ index สุดท้ายไว้)
        while self.sug_row.count() > 1:
            item = self.sug_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for sug in error.get("suggestions", []):
            if sug == error["best"]:
                continue
            btn = QPushButton(sug)
            btn.setObjectName("sug_btn")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.sug_row.insertWidget(self.sug_row.count() - 1, btn)


# ── Empty state panel ─────────────────────────────────────────────────────────

class EmptyPanel(QFrame):
    """แสดงเมื่อยังไม่ได้เลือก error หรือยังไม่ได้ตรวจสอบ"""
    def __init__(self, c: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("empty_panel")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        hint = QLabel("เลือกรายการทางซ้ายเพื่อดูรายละเอียด")
        hint.setObjectName("empty_hint")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._is_dark  = True
        self._c        = DARK
        self._errors:  list[dict]       = []
        self._worker:  CheckWorker|None = None
        self._filepath: str             = ""

        self.setWindowTitle("Thai Spell Checker")
        self.setMinimumSize(900, 580)
        self.resize(1100, 680)

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(12)

        # ── Top bar ──────────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(10)

        title = QLabel("Thai Spell Checker")
        title.setObjectName("app_title")

        self.browse_btn = QPushButton("📄   เลือกไฟล์ .docx")
        self.browse_btn.setObjectName("browse_btn")
        self.browse_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.browse_btn.setFixedHeight(42)
        self.browse_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_btn.clicked.connect(self._browse)

        self.check_btn = QPushButton("ตรวจสอบ")
        self.check_btn.setObjectName("check_btn")
        self.check_btn.setFixedHeight(42)
        self.check_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.check_btn.clicked.connect(self._run_check)

        self.theme_btn = QPushButton("☀")
        self.theme_btn.setObjectName("theme_btn")
        self.theme_btn.setFixedSize(42, 42)
        self.theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.theme_btn.clicked.connect(self._toggle_theme)

        top.addWidget(title)
        top.addSpacing(8)
        top.addWidget(self.browse_btn)
        top.addWidget(self.check_btn)
        top.addWidget(self.theme_btn)

        # ── Body: QSplitter ──────────────────────────────────────
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(1)

        # ซ้าย: รายการคำผิด
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(6)

        self.list_header = QLabel("รายการคำผิด")
        self.list_header.setObjectName("section_label")

        self.error_list = QListWidget()
        self.error_list.setSpacing(2)
        self.error_list.currentRowChanged.connect(self._on_select)

        left_layout.addWidget(self.list_header)
        left_layout.addWidget(self.error_list)

        # ขวา: wrapper สำหรับ swap ระหว่าง EmptyPanel และ DetailPanel
        self.right_wrapper = QWidget()
        self.right_layout  = QVBoxLayout(self.right_wrapper)
        self.right_layout.setContentsMargins(6, 0, 0, 0)
        self.right_layout.setSpacing(0)

        self.detail_panel = DetailPanel(self._c)
        self.empty_panel  = EmptyPanel(self._c)

        self.right_layout.addWidget(self.empty_panel)
        self.right_layout.addWidget(self.detail_panel)
        self.detail_panel.hide()

        self.splitter.addWidget(left)
        self.splitter.addWidget(self.right_wrapper)
        self.splitter.setSizes([280, 800])
        self.splitter.setStretchFactor(1, 1)

        # ── Status bar ────────────────────────────────────────────
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("เลือกไฟล์แล้วกด 'ตรวจสอบ'")

        root.addLayout(top)
        root.addWidget(self.splitter)

    # ── Slots ─────────────────────────────────────────────────────

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "เลือกไฟล์ Word", "",
            "Word Documents (*.docx);;All Files (*)"
        )
        if path:
            self._filepath = path
            name = path.replace("\\", "/").split("/")[-1]
            self.browse_btn.setText(f"📄   {name}")

    def _run_check(self):
        if not self._filepath:
            self.status.showMessage("⚠  กรุณาเลือกไฟล์ก่อน")
            return

        self.error_list.clear()
        self._show_empty()
        self.check_btn.setEnabled(False)
        self.status.showMessage("กำลังตรวจสอบ...")

        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        self._worker = CheckWorker(self._filepath)
        self._worker.finished.connect(self._on_done)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_done(self, errors: list, total: int):
        self._errors = errors
        self.check_btn.setEnabled(True)

        for err in errors:
            item = QListWidgetItem(self.error_list)
            card = ErrorCard(err, self._c)
            item.setSizeHint(card.sizeHint())
            self.error_list.setItemWidget(item, card)

        if errors:
            self.error_list.setCurrentRow(0)

        label = f"✓ {total} บรรทัด   ✗ {len(errors)} คำที่อาจผิด" if errors else \
                f"✓ {total} บรรทัด   ไม่พบคำผิด"
        self.status.showMessage(label)

    def _on_error(self, msg: str):
        self.check_btn.setEnabled(True)
        self.status.showMessage(f"⚠  {msg}")

    def _on_select(self, row: int):
        if 0 <= row < len(self._errors):
            self.detail_panel.show_error(self._errors[row])
            self._show_detail()

    def _show_detail(self):
        self.empty_panel.hide()
        self.detail_panel.show()

    def _show_empty(self):
        self.detail_panel.hide()
        self.empty_panel.show()

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        self._c = DARK if self._is_dark else LIGHT
        self.theme_btn.setText("☀" if self._is_dark else "🌙")
        self._rebuild_panels()
        self._apply_theme()

    def _rebuild_panels(self):
        """สร้าง panel และ error card ใหม่ทั้งหมดเมื่อ theme เปลี่ยน"""
        current_row = self.error_list.currentRow()

        new_detail = DetailPanel(self._c)
        new_empty  = EmptyPanel(self._c)
        self.right_layout.replaceWidget(self.detail_panel, new_detail)
        self.right_layout.replaceWidget(self.empty_panel,  new_empty)
        self.detail_panel.deleteLater()
        self.empty_panel.deleteLater()
        self.detail_panel = new_detail
        self.empty_panel  = new_empty

        for i, err in enumerate(self._errors):
            item = self.error_list.item(i)
            if item:
                card = ErrorCard(err, self._c)
                item.setSizeHint(card.sizeHint())
                self.error_list.setItemWidget(item, card)

        if 0 <= current_row < len(self._errors):
            self.detail_panel.show_error(self._errors[current_row])
            self._show_detail()
        else:
            self._show_empty()

    def _apply_theme(self):
        self.setStyleSheet(build_qss(self._c))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Fusion style รองรับ custom QSS ได้ดีที่สุดบน Windows
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
