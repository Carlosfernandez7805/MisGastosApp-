import sqlite3
from openpyxl import Workbook

def export_excel(db_path, output_path):
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            'SELECT created_at, description, amount, category '
            'FROM expenses ORDER BY created_at ASC'
        ).fetchall()
    finally:
        conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = 'Gastos'

    header = ['Fecha', 'Descripción', 'Valor (COP)', 'Categoría']
    ws.append(header)

    total = 0
    for created_at, description, amount, category in rows:
        fecha = created_at[:19].replace('T', ' ')
        ws.append([fecha, description, int(amount), category])
        total += int(amount)

    ws.append([])
    ws.append(['', 'TOTAL', total, ''])

    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15

    wb.save(output_path)
    return output_path
