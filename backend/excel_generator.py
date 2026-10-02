from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Human-readable labels for each metric key, matching BEI terminology
METRIC_LABELS = {
    'total_aset': 'Total Aset',
    'total_liabilitas': 'Total Liabilitas',
    'total_ekuitas': 'Total Ekuitas',
    'pendapatan': 'Pendapatan',
    'laba_bersih': 'Laba Bersih',
}


def generate_excel(
    results: list[dict],
    selected_metrics: list[str],
    output_path: str
) -> None:
    """Generate an Excel file from extracted BEI report data.

    Creates a formatted .xlsx with:
    - Column A: Nama Perusahaan
    - Column B: Kode Perusahaan (ticker)
    - Column C onwards: selected financial metrics

    Numbers are formatted with Indonesian thousand separators.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = 'Hasil Ekstraksi'

    header_font = Font(name='Calibri', bold=True, size=11, color='FFFFFF')
    header_fill = PatternFill(start_color='1B4F72', end_color='1B4F72', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    data_font = Font(name='Calibri', size=11)
    number_font = Font(name='Calibri', size=11)
    data_alignment = Alignment(vertical='center')
    number_alignment = Alignment(horizontal='right', vertical='center')

    thin_border = Border(
        left=Side(style='thin', color='D5D8DC'),
        right=Side(style='thin', color='D5D8DC'),
        top=Side(style='thin', color='D5D8DC'),
        bottom=Side(style='thin', color='D5D8DC'),
    )

    even_row_fill = PatternFill(start_color='EBF5FB', end_color='EBF5FB', fill_type='solid')

    headers = ['Nama Perusahaan', 'Kode Perusahaan']
    for metric_key in selected_metrics:
        headers.append(METRIC_LABELS.get(metric_key, metric_key))

    for col_idx, header_text in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header_text)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    for row_idx, record in enumerate(results, 2):
        name_cell = ws.cell(row=row_idx, column=1, value=record.get('company_name', ''))
        name_cell.font = data_font
        name_cell.alignment = data_alignment
        name_cell.border = thin_border

        ticker_cell = ws.cell(row=row_idx, column=2, value=record.get('ticker', ''))
        ticker_cell.font = Font(name='Calibri', size=11, bold=True)
        ticker_cell.alignment = Alignment(horizontal='center', vertical='center')
        ticker_cell.border = thin_border

        for metric_idx, metric_key in enumerate(selected_metrics, 3):
            value = record.get(metric_key)
            cell = ws.cell(row=row_idx, column=metric_idx)

            if value is not None:
                cell.value = value
                cell.number_format = '#,##0'
                cell.font = number_font
                cell.alignment = number_alignment
            else:
                cell.value = 'N/A'
                cell.font = Font(name='Calibri', size=11, italic=True, color='999999')
                cell.alignment = Alignment(horizontal='center', vertical='center')

            cell.border = thin_border

        # Alternate row shading for readability
        if row_idx % 2 == 0:
            for col in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=col).fill = even_row_fill

    # Auto-fit column widths
    ws.column_dimensions['A'].width = 40
    ws.column_dimensions['B'].width = 18
    for col_idx in range(3, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 22

    ws.freeze_panes = 'A2'

    ws.auto_filter.ref = f'A1:{get_column_letter(len(headers))}{len(results) + 1}'

    wb.save(output_path)
