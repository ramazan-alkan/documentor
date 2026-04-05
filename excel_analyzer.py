"""
excel_analyzer.py
-----------------
Excel dosyasını analiz eden ve LLM'e bağlam özeti sağlayan yardımcı sınıf.
"""

import pandas as pd
from typing import Optional


class ExcelAnalyzer:
    def __init__(self, df: pd.DataFrame, file_name: str = ""):
        self.df = df
        self.file_name = file_name
        self._analyze()

    # ──────────────────────────────────────────────────────────────────────────
    def _analyze(self):
        """İlk analiz – temel metadata'yı hesapla."""
        self.row_count = len(self.df)
        self.col_count = len(self.df.columns)
        self.columns = list(self.df.columns)
        self.dtypes = self.df.dtypes.to_dict()

        self.numeric_cols = self.df.select_dtypes(include="number").columns.tolist()
        self.text_cols = self.df.select_dtypes(include="object").columns.tolist()
        self.date_cols = self.df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

        # Missing values
        self.missing = self.df.isnull().sum()
        self.missing_pct = (self.missing / self.row_count * 100).round(2)

        # Numeric stats
        self.numeric_stats: Optional[pd.DataFrame] = None
        if self.numeric_cols:
            self.numeric_stats = self.df[self.numeric_cols].describe().round(4)

    # ──────────────────────────────────────────────────────────────────────────
    def get_context_summary(self) -> str:
        """LLM'e gönderilecek kısa bağlam özeti."""
        lines = [
            f"Dosya: {self.file_name}",
            f"Boyut: {self.row_count} satır × {self.col_count} sütun",
            f"Sütunlar: {', '.join(self.columns)}",
            f"Sayısal sütunlar: {', '.join(self.numeric_cols) or 'Yok'}",
            f"Metin sütunlar: {', '.join(self.text_cols) or 'Yok'}",
            f"Tarih sütunlar: {', '.join(self.date_cols) or 'Yok'}",
        ]

        # Missing data
        missing_cols = [c for c in self.columns if self.missing[c] > 0]
        if missing_cols:
            missing_info = ", ".join(
                f"{c} (%{self.missing_pct[c]})"
                for c in missing_cols
            )
            lines.append(f"Eksik veri olan sütunlar: {missing_info}")
        else:
            lines.append("Eksik veri: Yok")

        # Numeric stats (brief)
        if self.numeric_stats is not None:
            lines.append("\nSayısal İstatistikler:")
            for col in self.numeric_cols[:6]:  # cap at 6 cols to avoid huge prompts
                row = self.numeric_stats[col]
                lines.append(
                    f"  {col}: min={row['min']}, max={row['max']}, "
                    f"ortalama={row['mean']:.2f}, std={row['std']:.2f}"
                )

        # Sample rows (first 3)
        lines.append("\nİlk 3 Satır (örnek):")
        lines.append(self.df.head(3).to_string(index=False))

        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    def generate_welcome_message(self) -> str:
        """Dosya yüklendiğinde AI'nın gönderdiği karşılama mesajı."""
        missing_count = (self.missing > 0).sum()

        msg_lines = [
            f"✅ **{self.file_name}** başarıyla yüklendi!\n",
            f"📋 **Genel Bilgiler:**",
            f"- **{self.row_count:,}** satır, **{self.col_count}** sütun",
            f"- Sayısal sütunlar: {len(self.numeric_cols)} adet",
            f"- Metin sütunlar: {len(self.text_cols)} adet",
        ]

        if self.date_cols:
            msg_lines.append(f"- Tarih sütunları: {', '.join(self.date_cols)}")

        if missing_count > 0:
            msg_lines.append(
                f"- ⚠️ {missing_count} sütunda eksik veri bulunuyor"
            )
        else:
            msg_lines.append("- ✔️ Eksik veri yok")

        if self.numeric_cols:
            msg_lines.append(f"\n📊 **Sütunlar:** {', '.join(self.columns)}")

        msg_lines.append(
            "\nVeriniz hakkında ne öğrenmek istersiniz? "
            "Sol paneldeki hızlı sorgulardan birini seçebilir ya da "
            "kendi sorunuzu yazabilirsiniz! 🚀"
        )

        return "\n".join(msg_lines)

    # ──────────────────────────────────────────────────────────────────────────
    def get_quick_stats(self) -> dict:
        """UI'da göstermek için temel istatistik sözlüğü."""
        return {
            "rows": self.row_count,
            "cols": self.col_count,
            "numeric": len(self.numeric_cols),
            "missing_cols": int((self.missing > 0).sum()),
        }
