import sqlite3
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

def export_excel(db_path, output_path):
    try:
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
        for col in range(1, len(header) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        total = 0
        for created_at, description, amount, category in rows:
            fecha = created_at[:19].replace('T', ' ')
            ws.append([fecha, description, int(amount), category])
            total += int(amount)

        ws.append([])
        ws.append(['', 'TOTAL', total, ''])

        last_row = ws.max_row
        ws.cell(row=last_row, column=2).font = Font(bold=True)
        ws.cell(row=last_row, column=3).font = Font(bold=True)

        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15

        wb.save(output_path)
        return output_path
        
    except Exception as e:
        raise Exception(f"Error en librería Openpyxl: {e}")
