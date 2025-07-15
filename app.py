import streamlit as st
import fitz  # PyMuPDF
import os
import re
import zipfile
from io import BytesIO
from datetime import datetime

def procesar_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    output_dir = "pdfs_asistencia"
    os.makedirs(output_dir, exist_ok=True)
    archivos_generados = []

    for i in range(0, len(doc), 2):  # Solo páginas impares
        pagina = doc[i]
        texto = pagina.get_text("text")
        lineas = texto.splitlines()

        # Obtener mes desde línea "Periodo desde"
        mes = "Mes"
        for linea in lineas:
            match = re.search(r"Periodo desde (\d{2}/\d{2}/\d{4})", linea)
            if match:
                try:
                    fecha = datetime.strptime(match.group(1), "%d/%m/%Y")
                    meses_es = [
                        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                    ]
                    mes = meses_es[fecha.month - 1]
                    break
                except:
                    pass

        # Buscar línea después de "Empleado" para extraer RUT y nombre
        rut = "RUT"
        nombre = "NOMBRE"
        for idx, linea in enumerate(lineas):
            if linea.strip() == "Empleado" and idx + 1 < len(lineas):
                siguiente = lineas[idx + 1]
                match = re.match(r"([\d\.\-]+)\s*-\s*(.+)", siguiente)
                if match:
                    rut = match.group(1)
                    nombre = match.group(2).strip().upper()
                    break

        # Crear nombre de archivo
        nombre_archivo = f"ASISTENCIA_{mes}_{rut}_{nombre.replace(' ', '_')}.pdf"
        ruta_archivo = os.path.join(output_dir, nombre_archivo)

        # Guardar PDF individual
        nuevo_pdf = fitz.open()
        nuevo_pdf.insert_pdf(doc, from_page=i, to_page=i)
        nuevo_pdf.save(ruta_archivo)
        nuevo_pdf.close()

        archivos_generados.append(ruta_archivo)

    # Crear ZIP con todos los archivos
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for archivo in archivos_generados:
            zipf.write(archivo, os.path.basename(archivo))
    zip_buffer.seek(0)
    return zip_buffer

# Interfaz Streamlit
st.set_page_config(page_title="Dividir Asistencia PDF", layout="centered")
st.title("🧾 Dividir Planillas de Asistencia por Trabajador")

pdf_file = st.file_uploader("Sube el archivo PDF de asistencia", type="pdf")

if pdf_file:
    with st.spinner("Procesando PDF..."):
        zip_resultado = procesar_pdf(pdf_file.read())
        st.success("¡PDFs generados y comprimidos correctamente!")

        st.download_button(
            label="📦 Descargar archivo ZIP",
            data=zip_resultado,
            file_name="asistencias_divididas.zip",
            mime="application/zip"
        )