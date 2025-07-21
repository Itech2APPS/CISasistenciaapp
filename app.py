import streamlit as st
import os
import re
import zipfile
import tempfile
from PyPDF2 import PdfReader, PdfWriter

def extraer_datos(texto, rut_empleador="65.191.111-1"):
    meses = {
        "01": "ENERO", "02": "FEBRERO", "03": "MARZO", "04": "ABRIL",
        "05": "MAYO", "06": "JUNIO", "07": "JULIO", "08": "AGOSTO",
        "09": "SEPTIEMBRE", "10": "OCTUBRE", "11": "NOVIEMBRE", "12": "DICIEMBRE"
    }

    mes_match = re.search(r'Periodo desde\s+\d{2}/(\d{2})/\d{4}', texto)
    mes_num = mes_match.group(1) if mes_match else "XX"
    mes = meses.get(mes_num, "MES")

    rut_matches = re.findall(r'RUT:\s*([\d\.]+\-\d)', texto)
    rut = next((r for r in rut_matches if r != rut_empleador), None)

    nombre = "SIN_NOMBRE"
    if rut:
        lines = texto.splitlines()
        nombre_lines = []
        for i, line in enumerate(lines):
            if rut.replace(".", "") in line.replace(".", ""):
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if re.search(r'(Sucursal|Departamento|Código|RUT|Fecha|Empleado)', next_line, re.IGNORECASE):
                        break
                    if re.match(r'^[A-ZÁÉÍÓÚÑ ]+$', next_line):
                        nombre_lines.append(next_line)
                break
        if nombre_lines:
            nombre = " ".join(nombre_lines).strip()

    nombre_limpio = re.sub(r"[^\w\s]", "", nombre)
    nombre_limpio = re.sub(r"\s+", " ", nombre_limpio).upper().strip()

    return mes, rut, nombre_limpio

def generar_pdfs_por_empleado(pdf_file):
    reader = PdfReader(pdf_file)
    rut_empleador = "65.191.111-1"
    pdf_count = 0

    with tempfile.TemporaryDirectory() as tempdir:
        zip_path = os.path.join(tempdir, "asistencias_individuales.zip")
        pdf_dir = os.path.join(tempdir, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue

            mes, rut, nombre = extraer_datos(text, rut_empleador)
            if not rut or not nombre:
                continue

            base_filename = f"ASISTENCIA_{mes}_{rut}_{nombre}"
            filename = base_filename + ".pdf"
            counter = 1
            while os.path.exists(os.path.join(pdf_dir, filename)):
                filename = f"{base_filename}_{counter}.pdf"
                counter += 1

            filepath = os.path.join(pdf_dir, filename)

            writer = PdfWriter()
            writer.add_page(page)
            with open(filepath, "wb") as f_out:
                writer.write(f_out)
            pdf_count += 1

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for file in os.listdir(pdf_dir):
                zipf.write(os.path.join(pdf_dir, file), arcname=file)

        with open(zip_path, "rb") as f:
            zip_bytes = f.read()

    return zip_bytes, pdf_count

# ---- INTERFAZ STREAMLIT ----

st.set_page_config(page_title="Asistencia por empleado", layout="centered")
st.title("📄 Generador de PDFs de Asistencia por Empleado")

st.markdown("""
Sube el archivo PDF generado por el sistema de asistencia. La aplicación procesará cada página, extraerá los datos del trabajador y generará un PDF individual por empleado.
""")

uploaded_file = st.file_uploader("📎 Sube el archivo PDF de asistencia", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Procesando páginas y generando archivos..."):
        zip_bytes, total = generar_pdfs_por_empleado(uploaded_file)

    st.success(f"✅ Se generaron {total} archivos PDF.")
    st.download_button(
        label="📥 Descargar ZIP con todos los PDFs",
        data=zip_bytes,
        file_name="asistencias_por_empleado.zip",
        mime="application/zip"
    )