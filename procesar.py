"""Reglas de limpieza del export de órdenes."""
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

# (letra de columna, encabezado esperado). Si el encabezado se movió, se busca por nombre.
COLUMNAS = {
    "tipo": ("EO", "Line: Type"),
    "cancelada": ("N", "Cancelled At"),
    "pago": ("CB", "Payment: Status"),
    "fulfillment": ("CC", "Order Fulfillment Status"),
    "gift": ("FP", "Line: Gift Card"),
}


def _texto(v):
    return "" if v is None else str(v).strip()


def _col(ws, letra, encabezado):
    for c in ws[1]:
        if _texto(c.value).lower() == encabezado.lower():
            return c.column
    return column_index_from_string(letra)


def motivo_eliminacion(fila, idx):
    tipo = _texto(fila[idx["tipo"]]).lower()
    if tipo not in ("line item", "shipping line"):
        return "Tipo de línea (EO)"
    if _texto(fila[idx["cancelada"]]):
        return "Cancelada (N)"
    if _texto(fila[idx["pago"]]).lower() != "paid":
        return "Pago pendiente (CB)"
    ff = _texto(fila[idx["fulfillment"]]).lower().replace("_", " ")
    if "on hold" in ff:
        return "On hold (CC)"
    gift = fila[idx["gift"]]
    if gift is True or _texto(gift).lower() in ("true", "verdadero"):
        return "Gift Card (FP)"
    return None


def procesar(contenido: bytes, hoja=None):
    wb = load_workbook(BytesIO(contenido))
    ws = wb[hoja] if hoja else wb.worksheets[0]
    idx = {k: _col(ws, *v) - 1 for k, v in COLUMNAS.items()}

    borrar, resumen = [], {}
    for n, fila in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if all(v is None for v in fila):
            continue
        m = motivo_eliminacion(fila, idx)
        if m:
            borrar.append(n)
            resumen[m] = resumen.get(m, 0) + 1

    # borrar de abajo hacia arriba, agrupando filas consecutivas
    i = len(borrar) - 1
    while i >= 0:
        fin = borrar[i]
        inicio = fin
        while i > 0 and borrar[i - 1] == inicio - 1:
            i -= 1
            inicio -= 1
        ws.delete_rows(inicio, fin - inicio + 1)
        i -= 1

    salida = BytesIO()
    wb.save(salida)
    filas = [list(r) for r in ws.iter_rows(values_only=True)]
    return salida.getvalue(), filas, resumen, ws.title
