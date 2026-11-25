import os, json, threading
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from openpyxl import load_workbook
from procesar import procesar

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(16)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

DATA_DIR = os.environ.get("DATA_DIR", "/data")
ARCHIVO = os.path.join(DATA_DIR, "ultimo_procesado.xlsx")
META = os.path.join(DATA_DIR, "ultimo.json")
TZ = ZoneInfo(os.environ.get("TZ", "America/Argentina/Buenos_Aires"))
os.makedirs(DATA_DIR, exist_ok=True)
_lock = threading.Lock()


def _leer_actual():
    """Devuelve (meta, filas) del último reporte guardado, o (None, None)."""
    if not (os.path.exists(ARCHIVO) and os.path.exists(META)):
        return None, None
    with open(META, encoding="utf-8") as f:
        meta = json.load(f)
    ws = load_workbook(ARCHIVO, read_only=True)[meta["hoja"]]
    filas = [list(r) for r in ws.iter_rows(values_only=True)]
    return meta, filas


@app.route("/")
def index():
    meta, filas = _leer_actual()
    return render_template("index.html", meta=meta, filas=filas)


@app.post("/subir")
def subir():
    f = request.files.get("archivo")
    if not f or not f.filename.lower().endswith(".xlsx"):
        flash("Subí un archivo .xlsx")
        return redirect(url_for("index"))
    try:
        datos, filas, resumen, hoja = procesar(f.read())
    except Exception as e:
        flash(f"No se pudo procesar el archivo: {e}")
        return redirect(url_for("index"))
    meta = {
        "original": f.filename,
        "nombre": f.filename.rsplit(".", 1)[0] + "_procesado.xlsx",
        "hoja": hoja,
        "total": len(filas) - 1,
        "eliminadas": sum(resumen.values()),
        "resumen": resumen,
        "fecha": datetime.now(TZ).strftime("%d/%m/%Y %H:%M"),
    }
    # escribe en temporales y reemplaza: el reporte nuevo pisa al anterior
    with _lock:
        with open(ARCHIVO + ".tmp", "wb") as out:
            out.write(datos)
        with open(META + ".tmp", "w", encoding="utf-8") as out:
            json.dump(meta, out, ensure_ascii=False)
        os.replace(ARCHIVO + ".tmp", ARCHIVO)
        os.replace(META + ".tmp", META)
    return redirect(url_for("index"))


@app.get("/descargar")
def descargar():
    meta, _ = _leer_actual()
    if not meta:
        flash("Todavía no se subió ningún reporte.")
        return redirect(url_for("index"))
    return send_file(ARCHIVO, as_attachment=True, download_name=meta["nombre"],
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     max_age=0)


@app.get("/health")
def health():
    return "ok"
