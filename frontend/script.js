const API_BASE = 'http://127.0.0.1:5000';

const form = document.getElementById('extractionForm');
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const submitBtn = document.getElementById('submitBtn');
const btnLabel = document.getElementById('btnLabel');
const btnSpinner = document.getElementById('btnSpinner');
const statusArea = document.getElementById('statusArea');
const metricsAccordionContainer = document.getElementById('metricsAccordionContainer');
const metricSearch = document.getElementById('metricSearch');
const selectAllBtn = document.getElementById('selectAllBtn');
const deselectAllBtn = document.getElementById('deselectAllBtn');

let selectedFiles = [];

// ──────────────────────────────────────────────────────────────────────
// DATA-DRIVEN UI CONFIGURATION — 42 CORE METRICS (BEI XBRL v2.0)
// ──────────────────────────────────────────────────────────────────────
const METRICS_CONFIG = [
    {
        category: "A. Laporan Posisi Keuangan (Neraca)",
        items: [
            { id: "kas_dan_setara_kas",                         label: "Kas dan setara kas" },
            { id: "piutang_usaha_pihak_ketiga",                 label: "Piutang usaha pihak ketiga" },
            { id: "persediaan_lancar",                          label: "Persediaan lancar" },
            { id: "jumlah_aset_lancar",                         label: "Jumlah aset lancar" },
            { id: "aset_tetap",                                 label: "Aset tetap" },
            { id: "aset_takberwujud",                           label: "Aset takberwujud" },
            { id: "jumlah_aset_tidak_lancar",                   label: "Jumlah aset tidak lancar" },
            { id: "jumlah_aset",                                label: "Jumlah aset" },
            { id: "utang_usaha_pihak_ketiga",                   label: "Utang usaha pihak ketiga" },
            { id: "pinjaman_bank_jangka_pendek",                label: "Pinjaman bank jangka pendek" },
            { id: "bagian_lancar_liabilitas_jangka_panjang",    label: "Bagian lancar atas liabilitas jangka panjang" },
            { id: "jumlah_liabilitas_jangka_pendek",            label: "Jumlah liabilitas jangka pendek" },
            { id: "pinjaman_bank_jangka_panjang",               label: "Pinjaman bank jangka panjang" },
            { id: "utang_obligasi",                             label: "Utang obligasi" },
            { id: "jumlah_liabilitas_jangka_panjang",           label: "Jumlah liabilitas jangka panjang" },
            { id: "jumlah_liabilitas",                          label: "Jumlah liabilitas" },
            { id: "saham_treasuri",                             label: "Saham treasuri" },
            { id: "jumlah_saldo_laba",                          label: "Jumlah saldo laba" },
            { id: "jumlah_ekuitas_pemilik_entitas_induk",       label: "Jumlah ekuitas yang diatribusikan kepada pemilik entitas induk" },
            { id: "kepentingan_non_pengendali",                 label: "Kepentingan non-pengendali" },
            { id: "jumlah_ekuitas",                             label: "Jumlah ekuitas" },
            { id: "jumlah_saham_beredar",                       label: "Jumlah saham beredar" },
        ]
    },
    {
        category: "B. Laporan Laba Rugi Komprehensif",
        items: [
            { id: "penjualan_dan_pendapatan_usaha",             label: "Penjualan dan pendapatan usaha" },
            { id: "beban_pokok_penjualan_dan_pendapatan",       label: "Beban pokok penjualan dan pendapatan" },
            { id: "jumlah_laba_bruto",                          label: "Jumlah laba bruto" },
            { id: "beban_penjualan",                            label: "Beban penjualan" },
            { id: "beban_umum_dan_administrasi",                label: "Beban umum dan administrasi" },
            { id: "laba_rugi_usaha",                            label: "Laba (rugi) usaha" },
            { id: "beban_keuangan",                             label: "Beban keuangan" },
            { id: "keuntungan_kerugian_selisih_kurs",           label: "Keuntungan (kerugian) selisih kurs mata uang asing" },
            { id: "jumlah_laba_rugi_sebelum_pajak",             label: "Jumlah laba (rugi) sebelum pajak penghasilan" },
            { id: "pendapatan_beban_pajak",                     label: "Pendapatan (beban) pajak" },
            { id: "jumlah_laba_rugi",                           label: "Jumlah laba (rugi)" },
            { id: "laba_rugi_entitas_induk",                    label: "Laba (rugi) yang dapat diatribusikan ke entitas induk" },
            { id: "laba_per_saham_dasar",                       label: "Laba per saham dasar diatribusikan kepada pemilik entitas induk" },
        ]
    },
    {
        category: "C. Laporan Arus Kas",
        items: [
            { id: "penerimaan_kas_dari_pelanggan",              label: "Penerimaan kas dari pelanggan" },
            { id: "kas_bersih_aktivitas_operasi",               label: "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas operasi" },
            { id: "pembayaran_perolehan_aset_tetap",            label: "Pembayaran untuk perolehan aset tetap" },
            { id: "kas_bersih_aktivitas_investasi",             label: "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas investasi" },
            { id: "pembayaran_dividen",                         label: "Pembayaran dividen" },
            { id: "kas_bersih_aktivitas_pendanaan",             label: "Jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas pendanaan" },
            { id: "jumlah_kenaikan_penurunan_kas",              label: "Jumlah kenaikan (penurunan) bersih kas dan setara kas" },
        ]
    }
];

function renderMetricsUI() {
    metricsAccordionContainer.innerHTML = '';

    METRICS_CONFIG.forEach((cat, index) => {
        // Accordion Section
        const section = document.createElement('div');
        section.className = 'accordion-section';

        // Header
        const header = document.createElement('div');
        header.className = 'accordion-header';
        
        const titleArea = document.createElement('div');
        titleArea.className = 'accordion-title-area';
        
        const toggleIcon = `<svg class="accordion-icon" viewBox="0 0 24 24" fill="none"><path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
        titleArea.innerHTML = `${toggleIcon} <span class="accordion-title">${escapeHtml(cat.category)}</span> <span class="badge" id="badge_${index}">0</span>`;
        
        // Category Bulk Actions (Select All / Deselect All for this category)
        const catActions = document.createElement('div');
        catActions.className = 'accordion-cat-actions';
        catActions.innerHTML = `
            <button type="button" class="btn-text-small btn-cat-all" data-target="${index}">Semua</button>
            <button type="button" class="btn-text-small btn-cat-none" data-target="${index}">Kosongkan</button>
        `;

        header.appendChild(titleArea);
        header.appendChild(catActions);

        // Content (Grid)
        const content = document.createElement('div');
        content.className = 'accordion-content';
        content.id = `content_${index}`;
        // Buka kategori pertama secara default
        if (index === 0) content.classList.add('open');
        if (index === 0) header.classList.add('active');

        // Toggle Accordion (click on title area only so it doesn't trigger when clicking buttons)
        titleArea.addEventListener('click', () => {
            header.classList.toggle('active');
            content.classList.toggle('open');
        });

        const grid = document.createElement('div');
        grid.className = 'metrics-grid-modern';

        cat.items.forEach(item => {
            const label = document.createElement('label');
            label.className = 'metric-checkbox modern';
            label.setAttribute('data-label', item.label.toLowerCase());
            
            // Value is precisely the exact label so it matches backend extraction mapping
            label.innerHTML = `
                <input type="checkbox" name="metrics" value="${escapeHtml(item.label)}" class="metric-input" data-category="${index}">
                <span class="checkbox-visual" aria-hidden="true">
                    <svg viewBox="0 0 16 16" fill="none"><path d="M3 8L7 12L13 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </span>
                <span class="metric-label">${escapeHtml(item.label)}</span>
            `;
            
            grid.appendChild(label);
        });

        content.appendChild(grid);
        section.appendChild(header);
        section.appendChild(content);
        metricsAccordionContainer.appendChild(section);
    });

    // Re-attach change listeners to new checkboxes
    document.querySelectorAll('input[name="metrics"]').forEach(cb => {
        cb.addEventListener('change', () => {
            updateSubmitState();
            updateCategoryBadges();
        });
    });

    // Bulk actions per category
    document.querySelectorAll('.btn-cat-all').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const target = btn.getAttribute('data-target');
            document.querySelectorAll(`input[data-category="${target}"]`).forEach(cb => {
                if (cb.closest('label').style.display !== 'none') cb.checked = true;
            });
            updateSubmitState();
            updateCategoryBadges();
        });
    });

    document.querySelectorAll('.btn-cat-none').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const target = btn.getAttribute('data-target');
            document.querySelectorAll(`input[data-category="${target}"]`).forEach(cb => {
                if (cb.closest('label').style.display !== 'none') cb.checked = false;
            });
            updateSubmitState();
            updateCategoryBadges();
        });
    });
}

function updateCategoryBadges() {
    METRICS_CONFIG.forEach((cat, index) => {
        const checkedCount = document.querySelectorAll(`input[data-category="${index}"]:checked`).length;
        const badge = document.getElementById(`badge_${index}`);
        if (badge) {
            badge.textContent = checkedCount;
            if (checkedCount > 0) {
                badge.classList.add('has-selections');
            } else {
                badge.classList.remove('has-selections');
            }
        }
    });
}

// Search / Filter Logic
metricSearch.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase().trim();
    document.querySelectorAll('.metric-checkbox').forEach(label => {
        const text = label.getAttribute('data-label');
        if (text.includes(term)) {
            label.style.display = 'flex';
        } else {
            label.style.display = 'none';
        }
    });
});

// Global Bulk Actions
selectAllBtn.addEventListener('click', () => {
    document.querySelectorAll('input[name="metrics"]').forEach(cb => {
        if (cb.closest('label').style.display !== 'none') cb.checked = true;
    });
    updateSubmitState();
    updateCategoryBadges();
});

deselectAllBtn.addEventListener('click', () => {
    document.querySelectorAll('input[name="metrics"]').forEach(cb => {
        if (cb.closest('label').style.display !== 'none') cb.checked = false;
    });
    updateSubmitState();
    updateCategoryBadges();
});

// Initialize UI
renderMetricsUI();

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateSubmitState() {
    const hasFiles = selectedFiles.length > 0;
    const hasMetrics = document.querySelectorAll('input[name="metrics"]:checked').length > 0;
    submitBtn.disabled = !hasFiles || !hasMetrics;
}

function addFiles(incoming) {
    const maxSizeBytes = 50 * 1024 * 1024;

    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
    ];
    const allowedExtensions = ['.xlsx', '.xls'];

    for (const file of incoming) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const typeOk = allowedTypes.includes(file.type) || allowedExtensions.includes(ext);
        if (!typeOk) {
            showStatus(`"${file.name}" bukan file Excel. Hanya file .xlsx atau .xls yang diterima.`, 'error');
            continue;
        }
        if (file.size > maxSizeBytes) {
            showStatus(`"${file.name}" melebihi batas 50 MB.`, 'error');
            continue;
        }
        // Skip duplicates by name+size
        const isDuplicate = selectedFiles.some(
            f => f.name === file.name && f.size === file.size
        );
        if (!isDuplicate) {
            selectedFiles.push(file);
        }
    }

    renderFileList();
    updateSubmitState();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFileList();
    updateSubmitState();
}

function renderFileList() {
    fileList.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';

        item.innerHTML = `
            <div class="file-item-info">
                <svg class="file-item-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 2V8H20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="file-item-name">${escapeHtml(file.name)}</span>
            </div>
            <span class="file-item-size">${formatFileSize(file.size)}</span>
            <button type="button" class="file-item-remove" aria-label="Hapus ${escapeHtml(file.name)}" data-index="${index}">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path d="M2 2L12 12M12 2L2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        `;

        const removeBtn = item.querySelector('.file-item-remove');
        removeBtn.addEventListener('click', () => removeFile(index));

        fileList.appendChild(item);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showStatus(message, type) {
    statusArea.innerHTML = `<div class="status-message ${type}">${escapeHtml(message)}</div>`;
}

function clearStatus() {
    statusArea.innerHTML = '';
}

function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        btnLabel.textContent = 'Memproses...';
    } else {
        submitBtn.classList.remove('loading');
        btnLabel.textContent = 'Ekstrak & Unduh Excel';
        updateSubmitState();
    }
}

function getSelectedMetrics() {
    const checked = document.querySelectorAll('input[name="metrics"]:checked');
    return Array.from(checked).map(cb => cb.value);
}

// Drag-and-drop handlers
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('drag-over');
});

dropzone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-over');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
        addFiles(Array.from(e.dataTransfer.files));
    }
});

// Keyboard activation for dropzone
dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        addFiles(Array.from(fileInput.files));
        fileInput.value = '';
    }
});

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearStatus();

    const metrics = getSelectedMetrics();
    if (selectedFiles.length === 0) {
        showStatus('Unggah minimal satu file Excel (.xlsx / .xls).', 'error');
        return;
    }
    if (metrics.length === 0) {
        showStatus('Pilih minimal satu metrik keuangan.', 'error');
        return;
    }

    setLoading(true);

    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));
    formData.append('metrics', metrics.join(','));

    try {
        const response = await fetch(`${API_BASE}/api/extract`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            let errorMessage = 'Terjadi kesalahan saat memproses file.';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch {
                // response wasn't JSON
            }
            showStatus(errorMessage, 'error');
            setLoading(false);
            return;
        }

        // Trigger file download from the response blob
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const downloadLink = document.createElement('a');

        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'hasil_ekstraksi.xlsx';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (match && match[1]) {
                filename = match[1].replace(/['"]/g, '');
            }
        }

        downloadLink.href = url;
        downloadLink.download = filename;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        URL.revokeObjectURL(url);

        showStatus(
            `${selectedFiles.length} file berhasil diproses. File Excel sedang diunduh.`,
            'success'
        );

        selectedFiles = [];
        renderFileList();
        updateSubmitState();
    } catch (err) {
        // Fallback Error Handling: Log detail error network ke console untuk debugging
        console.log(err);
        
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            showStatus('Tidak dapat terhubung ke server. Pastikan backend berjalan di localhost:5000.', 'error');
        } else {
            showStatus(`Kesalahan: ${err.message}`, 'error');
        }
    } finally {
        setLoading(false);
    }
});

updateSubmitState();
