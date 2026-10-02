import os
import re

EXTRACTOR_PATH = r"d:\Belajar Antigravity\Tools Ekstraktor Laporan Keuangan\backend\extractor.py"
SCRIPT_JS_PATH = r"d:\Belajar Antigravity\Tools Ekstraktor Laporan Keuangan\frontend\script.js"

MAPPING = {
    # A
    "Kas dan Setara Kas": "Kas dan setara kas",
    "Piutang Usaha Pihak Ketiga": "Piutang usaha pihak ketiga",
    "Piutang Usaha Pihak Berelasi": "Piutang usaha pihak berelasi",
    "Persediaan Bersih": "Persediaan lancar",
    "Uang Muka Pembelian": "Uang muka lancar",
    "Biaya Dibayar di Muka": "Biaya dibayar dimuka lancar",
    "Pajak Dibayar di Muka": "Pajak dibayar dimuka lancar",
    "Total Aset Lancar": "Jumlah aset lancar",
    "Aset Tetap Neto": "Aset tetap",
    "Properti Investasi": "Properti investasi",
    "Aset Tak Berwujud": "Aset takberwujud",
    "Aset Hak Guna": "Aset hak guna",
    "Investasi pada Entitas Asosiasi / Ventura Bersama": "Investasi yang dicatat dengan menggunakan metode ekuitas",
    "Aset Pajak Tangguhan": "Aset pajak tangguhan",
    "Piutang Jangka Panjang": "Piutang tidak lancar",
    "Total Aset Tidak Lancar": "Jumlah aset tidak lancar",
    "Total Aset Keseluruhan": "Jumlah aset",
    "Utang Usaha Pihak Ketiga": "Utang usaha pihak ketiga",
    "Utang Usaha Pihak Berelasi": "Utang usaha pihak berelasi",
    "Pinjaman Bank Jangka Pendek": "Pinjaman bank jangka pendek",
    "Beban Akrual / Beban yang Masih Harus Dibayar": "Beban akrual jangka pendek",
    "Utang Bunga": "Utang bunga",
    "Utang Pajak": "Utang pajak",
    "Utang Dividen": "Utang dividen",
    "Pinjaman Jangka Panjang Jatuh Tempo dalam 1 Tahun": "Bagian lancar atas liabilitas jangka panjang",
    "Liabilitas Sewa Jangka Pendek": "Bagian lancar atas liabilitas sewa",
    "Kewajiban Diestimasi Jangka Pendek": "Kewajiban diestimasi jangka pendek",
    "Total Liabilitas Lancar": "Jumlah liabilitas jangka pendek",
    "Pinjaman Bank Jangka Panjang": "Pinjaman bank jangka panjang",
    "Utang Obligasi": "Utang obligasi",
    "Liabilitas Sewa Jangka Panjang": "Liabilitas sewa jangka panjang",
    "Liabilitas Imbalan Pascakerja": "Kewajiban imbalan pascakerja jangka panjang",
    "Liabilitas Pajak Tangguhan": "Liabilitas pajak tangguhan",
    "Total Liabilitas Jangka Panjang": "Jumlah liabilitas jangka panjang",
    "Total Liabilitas Keseluruhan": "Jumlah liabilitas",
    "Modal Saham Ditempatkan dan Disetor Penuh": "Modal saham ditempatkan dan disetor penuh",
    "Tambahan Modal Disetor": "Tambahan modal disetor",
    "Saham Treasuri": "Saham treasuri",
    "Saldo Laba Belum Dicadangkan": "Saldo laba yang belum dicadangkan",
    "Saldo Laba Telah Dicadangkan": "Saldo laba yang telah dicadangkan",
    "Total Saldo Laba": "Jumlah saldo laba",
    "Komponen Ekuitas Lainnya": "Komponen ekuitas lainnya",
    "Ekuitas yang Dapat Diatribusikan kepada Pemilik Entitas Induk": "Jumlah ekuitas yang diatribusikan kepada pemilik entitas induk",
    "Kepentingan Non-Pengendali": "Kepentingan non-pengendali",
    "Total Ekuitas Keseluruhan": "Jumlah ekuitas",
    "Jumlah Saham Beredar": "Jumlah saham beredar",
    
    # B
    "Penjualan dan Pendapatan Usaha": "Penjualan dan pendapatan usaha",
    "Beban Pokok Penjualan": "Beban pokok penjualan dan pendapatan",
    "Laba Kotor": "Jumlah laba bruto",
    "Beban Penjualan": "Beban penjualan",
    "Beban Umum dan Administrasi": "Beban umum dan administrasi",
    "Pendapatan Operasi Lainnya": "Pendapatan operasi lainnya",
    "Beban Operasi Lainnya": "Beban operasi lainnya",
    "Laba Usaha / Laba Operasi": "Laba (rugi) usaha",
    "Pendapatan Keuangan / Bunga": "Pendapatan keuangan",
    "Beban Keuangan / Bunga": "Beban keuangan",
    "Keuntungan (Kerugian) Selisih Kurs": "Keuntungan (kerugian) selisih kurs mata uang asing",
    "Bagian Laba (Rugi) Bersih Entitas Asosiasi": "Bagian atas laba (rugi) entitas asosiasi yang dicatat dengan menggunakan metode ekuitas",
    "Laba Sebelum Pajak Penghasilan": "Jumlah laba (rugi) sebelum pajak penghasilan",
    "Beban (Manfaat) Pajak Penghasilan": "Pendapatan (beban) pajak",
    "Laba Bersih Tahun Berjalan": "Jumlah laba (rugi)",
    "Laba Bersih yang Diatribusikan kepada Pemilik Entitas Induk": "Laba (rugi) yang dapat diatribusikan ke entitas induk",
    "Laba Bersih yang Diatribusikan kepada Kepentingan Non-Pengendali": "Laba (rugi) yang dapat diatribusikan ke kepentingan non-pengendali",
    "Pendapatan Komprehensif Lain Tahun Berjalan": "Jumlah pendapatan komprehensif lainnya, setelah pajak",
    "Total Penghasilan Komprehensif Tahun Berjalan": "Jumlah laba rugi komprehensif",
    "Laba Per Saham Dasar": "Laba per saham dasar diatribusikan kepada pemilik entitas induk",
    "Laba Per Saham Dilusian": "Laba per saham dilusian diatribusikan kepada pemilik entitas induk",
    
    # C
    "Penerimaan Kas dari Pelanggan": "Penerimaan kas dari pelanggan",
    "Pembayaran Kas kepada Pemasok": "Pembayaran kas kepada pemasok atas barang dan jasa",
    "Pembayaran Kas kepada Karyawan": "Pembayaran kas kepada karyawan",
    "Pembayaran (atau Penerimaan) Restitusi Pajak Penghasilan": "Pembayaran pajak penghasilan",
    "Pembayaran Bunga": "Pembayaran bunga",
    "Kas Bersih dari Aktivitas Operasi": "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas operasi",
    "Perolehan Aset Tetap": "Pembayaran untuk perolehan aset tetap",
    "Hasil Penjualan Aset Tetap": "Penerimaan dari penjualan aset tetap",
    "Perolehan Aset Tak Berwujud": "Pembayaran untuk perolehan aset takberwujud",
    "Penerimaan dari Penjualan Investasi": "Penerimaan dari penjualan investasi lainnya",
    "Kas Bersih dari Aktivitas Investasi": "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas investasi",
    "Penerimaan dari Utang Bank / Obligasi": "Penerimaan pinjaman bank",
    "Pembayaran Pokok Utang Bank / Obligasi": "Pembayaran pinjaman bank",
    "Pembayaran Liabilitas Sewa": "Pembayaran liabilitas sewa",
    "Pembayaran Dividen Tunai kepada Pemegang Saham": "Pembayaran dividen",
    "Kas Bersih dari Aktivitas Pendanaan": "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas pendanaan",
    "Kenaikan (Penurunan) Bersih Kas dan Setara Kas": "Jumlah kenaikan (penurunan) bersih kas dan setara kas",
    "Dampak Perubahan Nilai Tukar terhadap Kas": "Dampak perubahan nilai tukar pada kas dan setara kas"
}

with open(EXTRACTOR_PATH, 'r', encoding='utf-8') as f:
    extractor_content = f.read()

with open(SCRIPT_JS_PATH, 'r', encoding='utf-8') as f:
    script_content = f.read()

# Replace keys in extractor.py dicts and logic
for old_key, new_key in MAPPING.items():
    # Update dict keys: "Old Key": [ -> "New Key": [
    extractor_content = extractor_content.replace(f'"{old_key}": [', f'"{new_key}": [')
    
    # Update guardrail strings
    if old_key == "Pajak Dibayar di Muka":
        extractor_content = extractor_content.replace(f'output_key == "{old_key}"', f'output_key == "{new_key}"')
    if old_key == "Laba Bersih Tahun Berjalan":
        extractor_content = extractor_content.replace(f'output_key == "{old_key}"', f'output_key == "{new_key}"')
    if old_key == "Penjualan dan Pendapatan Usaha":
        extractor_content = extractor_content.replace(f'get("{old_key}")', f'get("{new_key}")')
        extractor_content = extractor_content.replace(f'result["{old_key}"]', f'result["{new_key}"]')

# Replace keys in script.js METRICS_CONFIG values
for old_key, new_key in MAPPING.items():
    # Example: "label": "Kas dan Setara Kas", "value": "Kas dan Setara Kas"
    script_content = script_content.replace(f'"{old_key}"', f'"{new_key}"')

with open(EXTRACTOR_PATH, 'w', encoding='utf-8') as f:
    f.write(extractor_content)

with open(SCRIPT_JS_PATH, 'w', encoding='utf-8') as f:
    f.write(script_content)

print("Files updated successfully!")
