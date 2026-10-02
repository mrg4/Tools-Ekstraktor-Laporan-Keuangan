import os
import uuid
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from extractor import extract_bei_report
from excel_generator import generate_excel

app = Flask(__name__)
# Enable CORS for all domains on all routes
CORS(app, resources={r"/*": {"origins": "*"}})
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE_MB = 50
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/extract', methods=['POST'])
def extract():
    """Accept multiple Excel files (.xlsx/.xls) and a list of selected metrics,
    extract financial data from each file, and return a summary Excel download."""

    if 'files' not in request.files:
        return jsonify({'error': 'Tidak ada file yang diunggah.'}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Tidak ada file yang dipilih.'}), 400

    metrics_raw = request.form.get('metrics', '')
    if not metrics_raw:
        return jsonify({'error': 'Pilih minimal satu metrik keuangan.'}), 400

    selected_metrics = [m.strip() for m in metrics_raw.split(',') if m.strip()]
    if not selected_metrics:
        return jsonify({'error': 'Pilih minimal satu metrik keuangan.'}), 400

    batch_id = uuid.uuid4().hex[:12]
    batch_dir = os.path.join(UPLOAD_DIR, batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    saved_paths = []
    for f in files:
        if not f or f.filename == '':
            continue
        if not allowed_file(f.filename):
            return jsonify({'error': f'Format tidak didukung: {f.filename}. Hanya file .xlsx atau .xls.'}), 400
        safe_name = secure_filename(f.filename)
        dest = os.path.join(batch_dir, safe_name)
        f.save(dest)
        saved_paths.append(dest)

    if not saved_paths:
        return jsonify({'error': 'Tidak ada file Excel valid yang diunggah.'}), 400

    results = []
    errors = []
    for file_path in saved_paths:
        try:
            data = extract_bei_report(file_path, selected_metrics)
            results.append(data)
        except Exception as exc:
            filename = os.path.basename(file_path)
            errors.append({
                'file': filename,
                'error': str(exc),
                'trace': traceback.format_exc()
            })

    if not results and errors:
        error_summary = '; '.join(f"{e['file']}: {e['error']}" for e in errors)
        return jsonify({'error': f'Gagal memproses semua file. {error_summary}'}), 422

    output_filename = f'hasil_ekstraksi_{batch_id}.xlsx'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    generate_excel(results, selected_metrics, output_path)

    # Clean up uploaded files after processing
    for p in saved_paths:
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        os.rmdir(batch_dir)
    except OSError:
        pass

    response_data = {
        'success': True,
        'processed': len(results),
        'failed': len(errors),
        'errors': [{'file': e['file'], 'error': e['error']} for e in errors]
    }

    return send_file(
        output_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=output_filename
    )


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
