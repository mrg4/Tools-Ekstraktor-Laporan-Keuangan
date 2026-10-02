# Ekstraktor Laporan Keuangan BEI

Ekstrak data keuangan dari beberapa laporan Excel Bursa Efek Indonesia (BEI) sekaligus, lalu unduh rekap hasilnya sebagai satu file Excel (.xlsx).

## Fitur

- Unggah beberapa file Excel (.xlsx / .xls) laporan keuangan BEI secara bersamaan (drag-and-drop)
- Deteksi otomatis kode emiten (ticker 4 huruf) dan nama perusahaan dari header file
- Pilih metrik keuangan yang ingin diekstrak: Total Aset, Total Liabilitas, Total Ekuitas, Pendapatan, Laba Bersih
- Unduh hasil rekap dalam satu file Excel dengan format profesional

## Struktur Proyek

```
├── frontend/
│   ├── index.html        # Halaman utama
│   ├── style.css         # Stylesheet
│   └── script.js         # Logika klien
├── backend/
│   ├── app.py            # Flask server (endpoint API)
│   ├── extractor.py      # Logika parsing Excel dan pencarian metrik BEI
│   ├── excel_generator.py# Generator file Excel rekap
│   └── requirements.txt  # Dependensi Python
├── uploads/              # Direktori sementara (dibuat otomatis)
├── output/               # Direktori output Excel (dibuat otomatis)
└── README.md
```

## Dependensi

| Komponen  | Teknologi         | Versi Minimum |
|-----------|-------------------|---------------|
| Backend   | Python            | 3.10+         |
| Backend   | Flask             | 3.0+          |
| Backend   | openpyxl          | 3.1+          |
| Frontend  | Browser modern    | Chrome/Firefox/Edge terbaru |

## Setup Lokal

### 1. Siapkan Python virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependensi

```bash
pip install -r requirements.txt
```

### 3. Jalankan backend

```bash
python app.py
```

Server akan berjalan di `http://localhost:5000`.

### 4. Buka frontend

Buka file `frontend/index.html` langsung di browser, atau gunakan server statis:

```bash
cd frontend
python -m http.server 8080
```

Lalu buka `http://localhost:8080` di browser.

## Cara Pakai

1. Unduh laporan keuangan BEI versi Excel dari situs BEI atau sumber data saham
2. Seret file Excel ke area unggah, atau klik untuk memilih file
3. Centang metrik keuangan yang ingin diekstrak
4. Klik "Ekstrak & Unduh Excel"
5. File Excel rekap akan otomatis terunduh

## Catatan Teknis

- Parser dirancang untuk format laporan keuangan standar BEI (bahasa Indonesia dan Inggris)
- Deteksi ticker: pola "Kode Emiten: XXXX", format "(XXXX)", dan heuristik 4 huruf kapital
- Pencarian metrik: scan baris per baris, cocokkan label cell dengan keyword, ambil nilai numerik di cell sebelahnya
- Format angka Indonesia (titik sebagai pemisah ribuan, koma sebagai desimal) ditangani otomatis
- Semua sheet dalam satu file Excel akan dipindai (neraca, laba rugi, dll. mungkin ada di sheet berbeda)
