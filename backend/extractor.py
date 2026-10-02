import re
import os
from openpyxl import load_workbook


# "PT ... Tbk" pattern for company name detection.
# All BEI-listed companies use this naming convention.
COMPANY_NAME_PATTERN = re.compile(
    r'(PT\.?\s+.{3,80}?\s+Tbk\.?)',
    re.IGNORECASE
)

# ──────────────────────────────────────────────────────────────────────
# SHEET NAME CONSTANTS — BEI XBRL NUMERIC & TEXT IDENTIFIERS
# ──────────────────────────────────────────────────────────────────────
# Konstanta untuk identifikasi sheet informasi umum / identitas perusahaan
IDENTITY_SHEET_NAMES = ["1000000", "general information", "informasi umum", "general info", "info umum"]

# Konstanta untuk sheet laporan posisi keuangan (neraca)
BALANCE_SHEET_NAMES = ["1210000", "1220000", "posisi keuangan"]

# Konstanta untuk sheet laba rugi
INCOME_STATEMENT_NAMES = ["1311000", "1321000", "1312000", "laba rugi"]

# Cell labels that precede the ticker value in the identity sheet.
# Matched case-insensitively against the full cell text.
TICKER_LABEL_PATTERNS = [
    re.compile(r'^\s*kode\s+entitas\s*$', re.IGNORECASE),
    re.compile(r'^\s*entity\s+ticker\s+symbol\s*$', re.IGNORECASE),
    re.compile(r'^\s*kode\s+(?:emiten|saham|perusahaan|efek)\s*$', re.IGNORECASE),
    re.compile(r'^\s*ticker\s+(?:symbol|code)\s*$', re.IGNORECASE),
    re.compile(r'^\s*stock\s+(?:code|ticker)\s*$', re.IGNORECASE),
]

# Cell labels that precede the company name in the identity sheet.
COMPANY_NAME_LABEL_PATTERNS = [
    re.compile(r'^\s*nama\s+entitas\s*$', re.IGNORECASE),
    re.compile(r'^\s*entity\s+name\s*$', re.IGNORECASE),
    re.compile(r'^\s*nama\s+(?:emiten|perusahaan)\s*$', re.IGNORECASE),
    re.compile(r'^\s*company\s+name\s*$', re.IGNORECASE),
]

# Fallback: if ticker label cell contains the value inline,
# e.g. "Kode entitas: ACES" or "Kode Emiten : BBCA"
TICKER_INLINE_PATTERN = re.compile(
    r'(?:kode\s+(?:entitas|emiten|saham|perusahaan|efek)|entity\s+ticker\s+symbol|ticker\s+(?:symbol|code)|stock\s+(?:code|ticker))'
    r'\s*[:\-]\s*([A-Z]{4})\b',
    re.IGNORECASE
)

# Validates that a candidate ticker is exactly 4 uppercase letters
TICKER_VALUE_PATTERN = re.compile(r'^[A-Z]{4}$')


def _sheet_has_code(sheet_name: str, code: str) -> bool:
    """Return True if *code* appears as a substring of *sheet_name*."""
    return code in sheet_name


def find_value_in_row(row, start_col_idx: int) -> str | None:
    """Scan cells to the right of *start_col_idx* and return the first
    non-empty, non-NaN string value found.

    BEI XBRL identity sheets sometimes place the actual value in column C
    (index 2) or D (index 3) rather than immediately adjacent to the label
    in column B (index 1). This helper scans the entire remainder of the row
    so the caller does not need to know the exact column position.

    Returns the stripped string value, or None if nothing usable is found.
    """
    for cell in row[start_col_idx:]:
        val = cell.value
        if val is None:
            continue
        text = str(val).strip()
        if text and text.lower() not in ('nan', 'none', '-', ''):
            return text
    return None


def extract_ticker_symbol(wb) -> str | None:
    """Extract the 4-letter BEI ticker from the workbook's identity sheet.

    BEI XBRL Excel files place the ticker in a dedicated sheet
    (e.g. "Informasi Umum") next to a label like "Kode entitas".

    Search order:
    1. Sheets whose name matches known identity sheet names
    2. The first sheet (index 0) as a fallback location
    3. Within each sheet, scan rows for a label cell that matches
       TICKER_LABEL_PATTERNS, then read the adjacent cell's value

    Returns the 4-letter ticker string, or None if not found.
    """
    sheets_to_check = []

    # Prioritize sheets whose names match known identity patterns
    for sheet_name in wb.sheetnames:
        if sheet_name.strip().lower() in IDENTITY_SHEET_NAMES:
            sheets_to_check.append(sheet_name)

    # Always include the first sheet as a fallback,
    # but avoid duplicating if it was already added
    first_sheet = wb.sheetnames[0]
    if first_sheet not in sheets_to_check:
        sheets_to_check.append(first_sheet)

    for sheet_name in sheets_to_check:
        ws = wb[sheet_name]
        for row in ws.iter_rows(min_row=1, max_row=50, values_only=False):
            for cell_idx, cell in enumerate(row):
                cell_val = cell.value
                if cell_val is None:
                    continue

                cell_text = str(cell_val).strip()
                if not cell_text:
                    continue

                # Check if this cell is a ticker label
                is_label = any(p.match(cell_text) for p in TICKER_LABEL_PATTERNS)

                if is_label:
                    # Scan seluruh kolom di sebelah kanan label untuk mencari nilai
                    candidate_val = find_value_in_row(row, cell_idx + 1)
                    if candidate_val:
                        candidate = candidate_val.upper()
                        if TICKER_VALUE_PATTERN.match(candidate):
                            return candidate

                # Check for inline format: "Kode entitas: ACES"
                inline_match = TICKER_INLINE_PATTERN.search(cell_text)
                if inline_match:
                    candidate = inline_match.group(1).upper()
                    if TICKER_VALUE_PATTERN.match(candidate):
                        return candidate

    return None


def extract_company_name(wb) -> str | None:
    """Extract 'PT ... Tbk' company name from the workbook.

    Searches identity sheets first, then the first sheet's header rows.
    Returns the company name string, or None if not found.
    """
    sheets_to_check = []

    for sheet_name in wb.sheetnames:
        if sheet_name.strip().lower() in IDENTITY_SHEET_NAMES:
            sheets_to_check.append(sheet_name)

    first_sheet = wb.sheetnames[0]
    if first_sheet not in sheets_to_check:
        sheets_to_check.append(first_sheet)

    for sheet_name in sheets_to_check:
        ws = wb[sheet_name]
        for row in ws.iter_rows(min_row=1, max_row=50, values_only=False):
            for cell_idx, cell in enumerate(row):
                cell_val = cell.value
                if cell_val is None:
                    continue
                    
                cell_text = str(cell_val).strip()
                if not cell_text:
                    continue

                # Cek apakah cell ini adalah label nama perusahaan
                is_label = any(p.match(cell_text) for p in COMPANY_NAME_LABEL_PATTERNS)
                if is_label:
                    # Scan seluruh kolom di sebelah kanan label untuk mencari nilai
                    candidate_val = find_value_in_row(row, cell_idx + 1)
                    if candidate_val:
                        return re.sub(r'\s+', ' ', candidate_val)

                # Fallback: Cari menggunakan pattern "PT ... Tbk" jika label tidak ketemu
                match = COMPANY_NAME_PATTERN.search(cell_text)
                if match:
                    name = match.group(1).strip()
                    return re.sub(r'\s+', ' ', name)

    return None


import difflib

# ──────────────────────────────────────────────────────────────────────
# CONFIG-DRIVEN MAPPING DICTIONARIES — 42 CORE METRICS (BEI XBRL v2.0)
# ──────────────────────────────────────────────────────────────────────
# Format: {"Header Output Excel (Taksonomi Resmi BEI)": ["target xbrl 1", "target xbrl 2", ...]}
# Logika pencarian: Exact Match (prioritas 1) -> Substring (prioritas 2, dengan guardrail) -> Fuzzy (prioritas 3)

# A. LAPORAN POSISI KEUANGAN / NERACA (22 metrik)
BALANCE_SHEET_MAPPING = {
    "Kas dan setara kas":                                                    ["kas dan setara kas", "kas dan bank"],
    "Piutang usaha pihak ketiga":                                            ["piutang usaha pihak ketiga", "piutang usaha - pihak ketiga", "piutang dagang pihak ketiga"],
    "Persediaan lancar":                                                     ["persediaan lancar", "persediaan bersih", "persediaan"],
    "Jumlah aset lancar":                                                    ["jumlah aset lancar", "total aset lancar"],
    "Aset tetap":                                                            ["aset tetap", "aset tetap neto", "aktiva tetap"],
    "Aset takberwujud":                                                      ["aset takberwujud", "aset tak berwujud"],
    "Jumlah aset tidak lancar":                                              ["jumlah aset tidak lancar", "total aset tidak lancar"],
    "Jumlah aset":                                                           ["jumlah aset"],
    "Utang usaha pihak ketiga":                                              ["utang usaha pihak ketiga", "utang dagang pihak ketiga"],
    "Pinjaman bank jangka pendek":                                           ["pinjaman bank jangka pendek", "utang bank jangka pendek"],
    "Bagian lancar atas liabilitas jangka panjang":                          ["pinjaman jangka panjang yang jatuh tempo", "bagian lancar atas liabilitas jangka panjang", "utang bank jangka panjang yang jatuh tempo"],
    "Jumlah liabilitas jangka pendek":                                       ["jumlah liabilitas jangka pendek", "jumlah liabilitas lancar", "total liabilitas lancar"],
    "Pinjaman bank jangka panjang":                                          ["pinjaman bank jangka panjang", "utang bank jangka panjang"],
    "Utang obligasi":                                                        ["utang obligasi", "penerbitan obligasi", "hutang obligasi"],
    "Jumlah liabilitas jangka panjang":                                      ["jumlah liabilitas jangka panjang", "total liabilitas jangka panjang", "jumlah liabilitas tidak lancar"],
    "Jumlah liabilitas":                                                     ["jumlah liabilitas"],
    "Saham treasuri":                                                        ["saham treasuri", "saham perbendaharaan"],
    "Jumlah saldo laba":                                                     ["jumlah saldo laba", "total saldo laba", "laba ditahan"],
    "Jumlah ekuitas yang diatribusikan kepada pemilik entitas induk":        ["ekuitas yang dapat diatribusikan kepada pemilik entitas induk", "jumlah ekuitas yang diatribusikan kepada pemilik entitas induk"],
    "Kepentingan non-pengendali":                                            ["kepentingan non-pengendali", "kepentingan minoritas"],
    "Jumlah ekuitas":                                                        ["jumlah ekuitas", "total ekuitas"],
    "Jumlah saham beredar":                                                  ["jumlah saham beredar", "saham beredar"],
}

# B. LAPORAN LABA RUGI KOMPREHENSIF (13 metrik)
INCOME_STATEMENT_MAPPING = {
    "Penjualan dan pendapatan usaha":                                        ["penjualan dan pendapatan usaha", "pendapatan usaha", "pendapatan neto", "penjualan neto"],
    "Beban pokok penjualan dan pendapatan":                                  ["beban pokok penjualan dan pendapatan", "beban pokok penjualan", "beban pokok pendapatan", "harga pokok penjualan"],
    "Jumlah laba bruto":                                                     ["jumlah laba bruto", "laba bruto", "laba kotor"],
    "Beban penjualan":                                                       ["beban penjualan", "biaya penjualan"],
    "Beban umum dan administrasi":                                           ["beban umum dan administrasi", "beban administrasi", "biaya umum dan administrasi"],
    "Laba (rugi) usaha":                                                     ["laba usaha", "rugi usaha", "laba operasi", "rugi operasi"],
    "Beban keuangan":                                                        ["beban keuangan", "biaya keuangan", "beban bunga"],
    "Keuntungan (kerugian) selisih kurs mata uang asing":                    ["laba selisih kurs", "rugi selisih kurs", "selisih kurs", "keuntungan (kerugian) selisih kurs"],
    "Jumlah laba (rugi) sebelum pajak penghasilan":                          ["jumlah laba sebelum pajak penghasilan", "laba sebelum pajak penghasilan", "laba sebelum pajak", "rugi sebelum pajak"],
    "Pendapatan (beban) pajak":                                              ["pendapatan (beban) pajak", "beban pajak penghasilan", "manfaat pajak penghasilan"],
    "Jumlah laba (rugi)":                                                    ["jumlah laba (rugi)", "jumlah laba (rugi) dari operasi yang dilanjutkan", "laba tahun berjalan", "rugi tahun berjalan", "laba periode berjalan"],
    "Laba (rugi) yang dapat diatribusikan ke entitas induk":                 ["laba (rugi) yang dapat diatribusikan ke entitas induk", "laba yang dapat diatribusikan kepada pemilik entitas induk"],
    "Laba per saham dasar diatribusikan kepada pemilik entitas induk":       ["laba per saham dasar diatribusikan kepada pemilik entitas induk", "laba per saham dasar", "rugi per saham dasar", "laba per saham"],
}

# C. LAPORAN ARUS KAS (7 metrik)
CASH_FLOW_MAPPING = {
    "Penerimaan kas dari pelanggan":                                                                  ["penerimaan kas dari pelanggan", "penerimaan dari pelanggan"],
    "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas operasi":                 ["jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas operasi", "kas bersih dari aktivitas operasi"],
    "Pembayaran untuk perolehan aset tetap":                                                          ["pembayaran untuk perolehan aset tetap", "perolehan aset tetap", "pembelian aset tetap"],
    "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas investasi":               ["jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas investasi", "kas bersih dari aktivitas investasi"],
    "Pembayaran dividen":                                                                              ["pembayaran dividen", "dividen dibayar"],
    "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas pendanaan":               ["jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas pendanaan", "kas bersih dari aktivitas pendanaan"],
    "Jumlah kenaikan (penurunan) bersih kas dan setara kas":                                          ["jumlah kenaikan (penurunan) bersih kas dan setara kas", "kenaikan bersih kas", "penurunan bersih kas"],
}

def parse_cell_number(value) -> float | None:
    """Extract a numeric value from an Excel cell (Handles formatting & parentheses negatives)."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip()
    if not raw:
        return None

    is_negative = raw.startswith('(') and raw.endswith(')')
    raw = raw.strip('()')
    raw = re.sub(r'[Rr][Pp]\.?\s*', '', raw).strip()

    if not raw or not re.search(r'\d', raw):
        return None

    last_dot = raw.rfind('.')
    last_comma = raw.rfind(',')

    if last_dot > last_comma:
        cleaned = raw.replace(',', '')
    elif last_comma > last_dot:
        cleaned = raw.replace('.', '').replace(',', '.')
    else:
        cleaned = raw.replace('.', '').replace(',', '')

    cleaned = re.sub(r'[^\d.\-]', '', cleaned)

    try:
        result = float(cleaned)
        return -result if is_negative else result
    except ValueError:
        return None

def extract_metrics_from_sheet(wb, target_sheet_codes: list[str], target_mapping_dict: dict) -> dict:
    """
    Fungsi universal untuk mengekstrak metrik berdasarkan kamus taksonomi (1:N).
    Termasuk logika Dynamic Fallback, String Normalization, dan Partial Matching.
    """
    # Keys dari dict sekarang adalah nama kolom output final
    unique_output_keys = list(target_mapping_dict.keys())
    result = {key: None for key in unique_output_keys}
    
    for code in target_sheet_codes:
        sheet_to_use = None
        for sheet_name in wb.sheetnames:
            if code in sheet_name:
                sheet_to_use = sheet_name
                break
                
        if not sheet_to_use:
            continue
            
        ws = wb[sheet_to_use]
        
        for row in ws.iter_rows(min_row=1, values_only=False):
            for cell_idx, cell in enumerate(row):
                if cell.value is None:
                    continue
                    
                cell_text = str(cell.value)
                
                # String Normalization: hapus \xa0, lowercase, strip, single-space
                normalized_text = " ".join(cell_text.replace('\xa0', ' ').strip().lower().split())
                
                # Iterasi seluruh pemetaan target taksonomi
                for output_key, targets in target_mapping_dict.items():
                    # Cegah overwrite jika metrik sudah didapat (menghindari salah ambil dari subtotal lanjutan)
                    if result[output_key] is not None:
                        continue
                        
                    is_match_found = False
                    for target in targets:
                        # 1. Exact Match (Prioritas Tertinggi)
                        if target == normalized_text:
                            is_match_found = True
                            break
                            
                        # Strict Override: Pajak Dibayar di Muka HANYA boleh exact match
                        if output_key == "Pajak dibayar dimuka lancar":
                            continue
                            
                        # 2. Partial String Matching (Substring) dengan Guardrails
                        elif target in normalized_text:
                            # Guardrail untuk mencegah "jumlah aset" salah mencaplok "jumlah aset lancar"
                            if target == "jumlah aset" and "lancar" in normalized_text:
                                continue
                            if target == "jumlah liabilitas" and ("lancar" in normalized_text or "pendek" in normalized_text or "panjang" in normalized_text):
                                continue
                            if target == "total aset" and "lancar" in normalized_text:
                                continue
                            if target == "total liabilitas" and ("lancar" in normalized_text or "pendek" in normalized_text or "panjang" in normalized_text):
                                continue
                            # Guardrail untuk mencegah "jumlah laba (rugi)" salah mencaplok "... sebelum pajak penghasilan"
                            if output_key == "Jumlah laba (rugi)" and "sebelum pajak" in normalized_text:
                                continue
                            is_match_found = True
                            break
                            
                        # 3. Toleransi Typo Minor (Fuzzy Matching Difflib)
                        # Mengakomodasi typo dari pihak pengunggah/emiten
                        elif difflib.SequenceMatcher(None, target, normalized_text).ratio() >= 0.85:
                            # Guardrail Kritis untuk Arus Kas: Mencegah duplikasi aktivitas akibat kemiripan kalimat XBRL yang panjang!
                            if "operasi" in target and "operasi" not in normalized_text:
                                continue
                            if "investasi" in target and "investasi" not in normalized_text:
                                continue
                            if "pendanaan" in target and "pendanaan" not in normalized_text:
                                continue
                            is_match_found = True
                            break
                            
                    if is_match_found:
                        # First Valid Numeric Extraction (Current Year)
                        for next_cell in row[cell_idx + 1:]:
                            val = parse_cell_number(next_cell.value)
                            if val is not None:
                                result[output_key] = val
                                break
                            
        # Dynamic Fallback Evaluation
        # Jika masih ada nilai None di result, looping otomatis berlanjut mengecek sheet (kode) berikutnya
        if all(val is not None for val in result.values()):
            break
            
    return result

# ──────────────────────────────────────────────────────────────────────
# SECTOR-SPECIFIC ROUTING TABLE (BEI XBRL TAXONOMY)
# ──────────────────────────────────────────────────────────────────────
# Masing-masing sektor memiliki kode sheet unik. Tabel ini memetakan
# prefix sektor -> daftar sheet target [utama, fallback].
# Kunci: "bs" = Balance Sheet, "is" = Income Statement, "cf" = Cash Flow
SECTOR_ROUTING = {
    "1": {  # Umum (ASII, UNVR, ACES, dll.)
        "bs": ["1210000", "1220000"],
        "is": ["1311000", "1321000", "1312000", "1322000"],
        "cf": ["1510000", "1520000"],
    },
    "2": {  # Properti
        "bs": ["2210000", "2220000"],
        "is": ["2311000", "2321000", "2312000", "2322000"],
        "cf": ["2510000", "2520000"],
    },
    "3": {  # Infrastruktur / Telco (TLKM, dll.)
        "bs": ["3210000", "3220000"],
        "is": ["3311000", "3321000", "3312000", "3322000"],
        "cf": ["3510000", "3520000"],
    },
    "4": {  # Perbankan / Keuangan / Syariah (BBCA, BMRI, dll.)
        "bs": ["4210000", "4220000"],
        "is": ["4312000", "4322000"],
        "cf": ["4510000", "4520000"],
    },
}

# Mapping khusus untuk Revenue Fallback sektor Perbankan/Keuangan/Asuransi.
# Jika "Penjualan dan Pendapatan Usaha" null, parser mencari label di bawah ini.
BANKING_REVENUE_TARGETS = [
    "pendapatan bunga",
    "pendapatan bunga dan syariah",
    "jumlah pendapatan bunga",
]
SHARIA_REVENUE_TARGETS = [
    "pendapatan syariah",
    "pendapatan pengelolaan dana oleh bank sebagai mudharib",
]
INSURANCE_REVENUE_TARGETS = [
    "pendapatan premi",
    "pendapatan premi neto",
    "pendapatan premi bruto",
]


def _detect_sector_prefix(wb) -> str:
    """Deteksi prefix sektor (1-9) dari nama sheet workbook.

    Mencari pola kode sheet Neraca (x210000/x220000) atau Arus Kas
    (x510000/x520000) untuk menentukan prefix sektor secara akurat.
    Default: "1" (Umum) jika tidak terdeteksi.
    """
    for name in wb.sheetnames:
        match = re.search(r'\b([1-9])(21|22|31|32|51|52)\d{4}\b', name)
        if match:
            return match.group(1)
    return "1"


def _extract_banking_revenue(wb, is_targets: list[str]) -> float | None:
    """Fallback khusus sektor Perbankan/Asuransi.

    Mencari Pendapatan Bunga + Pendapatan Syariah (dijumlahkan jika keduanya ada),
    atau Pendapatan Premi untuk perusahaan asuransi.
    """
    pendapatan_bunga = None
    pendapatan_syariah = None
    pendapatan_premi = None

    for code in is_targets:
        sheet_to_use = None
        for sheet_name in wb.sheetnames:
            if code in sheet_name:
                sheet_to_use = sheet_name
                break
        if not sheet_to_use:
            continue

        ws = wb[sheet_to_use]
        for row in ws.iter_rows(min_row=1, values_only=False):
            for cell_idx, cell in enumerate(row):
                if cell.value is None:
                    continue
                normalized = " ".join(str(cell.value).replace('\xa0', ' ').strip().lower().split())

                # Cari Pendapatan Bunga
                if pendapatan_bunga is None:
                    for t in BANKING_REVENUE_TARGETS:
                        if t == normalized or t in normalized:
                            for nc in row[cell_idx + 1:]:
                                val = parse_cell_number(nc.value)
                                if val is not None:
                                    pendapatan_bunga = val
                                    break
                            break

                # Cari Pendapatan Syariah
                if pendapatan_syariah is None:
                    for t in SHARIA_REVENUE_TARGETS:
                        if t == normalized or t in normalized:
                            for nc in row[cell_idx + 1:]:
                                val = parse_cell_number(nc.value)
                                if val is not None:
                                    pendapatan_syariah = val
                                    break
                            break

                # Cari Pendapatan Premi (Asuransi)
                if pendapatan_premi is None:
                    for t in INSURANCE_REVENUE_TARGETS:
                        if t == normalized or t in normalized:
                            for nc in row[cell_idx + 1:]:
                                val = parse_cell_number(nc.value)
                                if val is not None:
                                    pendapatan_premi = val
                                    break
                            break

        # Jika sudah dapat pendapatan bunga atau premi, stop fallback sheet
        if pendapatan_bunga is not None or pendapatan_premi is not None:
            break

    # Prioritas: Pendapatan Bunga (+ Syariah jika ada) > Pendapatan Premi
    if pendapatan_bunga is not None:
        total = pendapatan_bunga
        if pendapatan_syariah is not None:
            total += pendapatan_syariah
        return total
    if pendapatan_premi is not None:
        return pendapatan_premi

    return None


def _extract_banking_cash(wb, cf_targets: list[str]) -> float | None:
    """Fallback khusus sektor Perbankan/Keuangan untuk mengambil Kas dari sheet Arus Kas."""
    TARGETS = [
        "kas dan setara kas arus kas, akhir periode",
        "kas dan setara kas pada akhir tahun",
        "kas dan setara kas akhir periode"
    ]
    for code in cf_targets:
        sheet_to_use = None
        for sheet_name in wb.sheetnames:
            if code in sheet_name:
                sheet_to_use = sheet_name
                break
        if not sheet_to_use:
            continue

        ws = wb[sheet_to_use]
        for row in ws.iter_rows(min_row=1, values_only=False):
            for cell_idx, cell in enumerate(row):
                if cell.value is None:
                    continue
                normalized = " ".join(str(cell.value).replace('\xa0', ' ').strip().lower().split())
                
                for t in TARGETS:
                    if t == normalized or t in normalized:
                        for nc in row[cell_idx + 1:]:
                            val = parse_cell_number(nc.value)
                            if val is not None:
                                return val
    return None

# ──────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION ENTRY POINT
# ──────────────────────────────────────────────────────────────────────

def extract_bei_report(excel_path: str, selected_metrics: list[str]) -> dict:
    """Extract company identity and all 85+ comprehensive financial metrics."""
    filename = os.path.basename(excel_path)

    try:
        wb = load_workbook(excel_path, read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError(f'Gagal membuka file "{filename}": {exc}') from exc

    try:
        # 1. Fase Identifikasi Sektor (Root Check)
        sector_prefix = _detect_sector_prefix(wb)

        ticker = extract_ticker_symbol(wb)
        company_name = extract_company_name(wb)

        result = {
            'filename': filename,
            'company_name': company_name or 'Tidak Terdeteksi',
            'ticker': ticker or 'N/A',
        }

        # 2. Fase Routing Laporan Keuangan (Sector-Aware)
        routing = SECTOR_ROUTING.get(sector_prefix, SECTOR_ROUTING["1"])
        bs_targets = routing["bs"]
        is_targets = routing["is"]
        cf_targets = routing["cf"]

        # Ekstrak data Neraca
        bs_metrics = extract_metrics_from_sheet(wb, bs_targets, BALANCE_SHEET_MAPPING)
        result.update(bs_metrics)

        # Ekstrak data Laba Rugi
        is_metrics = extract_metrics_from_sheet(wb, is_targets, INCOME_STATEMENT_MAPPING)
        result.update(is_metrics)

        # 3. Revenue Fallback untuk Sektor Perbankan/Keuangan/Asuransi
        # Jika "Penjualan dan Pendapatan Usaha" masih null, cari Pendapatan Bunga/Syariah/Premi
        if result.get("Penjualan dan pendapatan usaha") is None and sector_prefix == "4":
            banking_revenue = _extract_banking_revenue(wb, is_targets)
            if banking_revenue is not None:
                result["Penjualan dan pendapatan usaha"] = banking_revenue

        # Ekstrak data Arus Kas
        cf_metrics = extract_metrics_from_sheet(wb, cf_targets, CASH_FLOW_MAPPING)
        result.update(cf_metrics)

        # 4. Fallback Kas Sektor Perbankan/Keuangan
        # JANGAN gunakan hasil Neraca, selalu ambil dari Arus Kas akhir periode
        if sector_prefix == "4":
            banking_cash = _extract_banking_cash(wb, cf_targets)
            if banking_cash is not None:
                result["Kas dan setara kas"] = banking_cash

    finally:
        wb.close()

    return result
