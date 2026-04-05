"""
pdf_analyzer.py
---------------
PDF dosyasını analiz eden yardımcı sınıf.
pdfplumber ile metin ve tablo çıkarımı yapar.
"""

import io
import pdfplumber
from typing import Optional


class PDFAnalyzer:
    def __init__(self, file_bytes: bytes, file_name: str = ""):
        self.file_bytes = file_bytes
        self.file_name = file_name
        self._analyze()

    # ──────────────────────────────────────────────────────────────────────────
    def _analyze(self):
        """PDF'i açıp temel metadata + içeriği çıkar."""
        self.pages_text: list[str] = []
        self.tables: list[list] = []
        self.page_count = 0
        self.word_count = 0
        self.has_tables = False
        self.metadata: dict = {}

        with pdfplumber.open(io.BytesIO(self.file_bytes)) as pdf:
            self.page_count = len(pdf.pages)
            self.metadata = pdf.metadata or {}

            for page in pdf.pages:
                # Text
                text = page.extract_text() or ""
                self.pages_text.append(text)

                # Tables
                page_tables = page.extract_tables() or []
                if page_tables:
                    self.has_tables = True
                    self.tables.extend(page_tables)

        full_text = "\n".join(self.pages_text)
        self.word_count = len(full_text.split())
        self.char_count = len(full_text)

        # Preview: first ~3000 chars for context
        self._preview = full_text[:3000].strip()
        # Full text capped at 20k chars for AI context
        self._full_text_capped = full_text[:20_000]

    # ──────────────────────────────────────────────────────────────────────────
    def full_text(self) -> str:
        return self._full_text_capped

    def preview(self) -> str:
        return self._preview

    # ──────────────────────────────────────────────────────────────────────────
    def get_context_summary(self) -> str:
        """LLM'e gönderilecek bağlam özeti."""
        lines = [
            f"Dosya: {self.file_name}",
            f"Sayfa sayısı: {self.page_count}",
            f"Kelime sayısı: {self.word_count:,}",
            f"Karakter sayısı: {self.char_count:,}",
            f"Tablolar: {'Var (' + str(len(self.tables)) + ' adet)' if self.has_tables else 'Yok'}",
        ]

        # Meta
        if self.metadata:
            for key in ("Title", "Author", "Subject", "Creator"):
                val = self.metadata.get(key, "")
                if val:
                    lines.append(f"{key}: {val}")

        lines.append(f"\n--- PDF İçeriği (ilk 4000 karakter) ---")
        lines.append(self._full_text_capped[:4000])

        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    def generate_welcome_message(self) -> str:
        """Dosya yüklendiğinde gösterilecek karşılama mesajı."""
        lines = [
            f"✅ **{self.file_name}** başarıyla yüklendi!\n",
            f"📋 **Genel Bilgiler:**",
            f"- **{self.page_count}** sayfa",
            f"- **{self.word_count:,}** kelime, **{self.char_count:,}** karakter",
        ]

        if self.has_tables:
            lines.append(f"- 📊 **{len(self.tables)}** tablo tespit edildi")

        # PDF meta
        title = self.metadata.get("Title", "")
        author = self.metadata.get("Author", "")
        if title:
            lines.append(f"- 📌 Başlık: {title}")
        if author:
            lines.append(f"- ✍️ Yazar: {author}")

        lines.append(
            "\nPDF içeriği hakkında ne öğrenmek istersiniz? "
            "Sol paneldeki hızlı sorgulardan birini seçebilir ya da "
            "kendi sorunuzu yazabilirsiniz! 🚀"
        )
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    def get_page_text(self, page_num: int) -> str:
        """0-indexed sayfa metni."""
        if 0 <= page_num < len(self.pages_text):
            return self.pages_text[page_num]
        return ""
