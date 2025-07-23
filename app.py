import streamlit as st
import re
import calendar
import zipfile
from io import BytesIO
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

# Diccionario meses en español - Creado por Ismael Leon
meses_es = {
    "January": "Enero", "February": "Febrero", "March": "Marzo",
    "April": "Abril", "May": "Mayo", "June": "Junio",
    "July": "Julio", "August": "Agosto", "September": "Septiembre",
    "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

def extraer_mes(texto):
    match = re.search(r"Periodo desde\s+(\d{2})/(\d{2})/(\d{4})", texto)
    if match:
        mes_num = int(match.group(2))
        mes_en = calendar.month_name[mes_num]
        return meses_es.get(mes_en, "Mes")
    return "Mes"

def extraer_rut(texto):
    match = re.search(r"(\d{1,3}(?:\.\d{3}){2}-\d)", texto)
    if match:
        rut = match.group(1)
        if not rut.startswith("65.191"):
            return rut
    return None

def extraer_nombre(texto):
    match = re.search(r"\d{1,3}(?:\.\d{3}){2}-\d\s+([A-ZÁÉÍÓÚÑ ]+)", texto)
    if match:
        return match.group(1).strip().title()
    return "Nombre_Desconocido"

def procesar_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for i in range(0, len(reader.pages), 2):  # solo páginas impares
            page = reader.pages[i]
            text = page.extract_text()

            mes = extraer_mes(text)
            rut = extraer_rut(text)
            nombre = extraer_nombre(text)

            if rut:
                filename = f"ASISTENCIA_{mes}_{rut}_{nombre}.pdf".replace(" ", "_")
                pdf_bytes = BytesIO()
                writer = PdfWriter()
                writer.add_page(page)
                writer.write(pdf_bytes)
                pdf_bytes.seek(0)

                zipf.writestr(filename, pdf_bytes.read())

    zip_buffer.seek(0)
    return zip_buffer

# Streamlit UI - Creado por Ismael Leon
st.set_page_config(page_title="Generador de Asistencias", layout="centered")
st.title("Generador de Asistencias Individuales")
st.write("Sube el archivo PDF para generar los documentos individuales por empleado.")

uploaded_file = st.file_uploader("Selecciona el archivo PDF de asistencia:", type=["pdf"])

if uploaded_file:
    with st.spinner("Procesando archivo..."):
        zip_result = procesar_pdf(uploaded_file)
        st.success("Proceso completado. Descarga el archivo ZIP a continuación:")
        st.download_button(
            label="💾 Descargar ZIP",
            data=zip_result,
            file_name="ASISTENCIAS.zip",
            mime="application/zip"
        )
# 👣 Footer opcional
st.markdown("<hr style='margin-top:40px;'>", unsafe_allow_html=True)
st.markdown("Desarrollado por Ismael León – © 2025", unsafe_allow_html=True)
