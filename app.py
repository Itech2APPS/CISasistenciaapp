import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import re
import io
from zipfile import ZipFile

st.set_page_config(page_title="Divisor de Libros de Asistencia", page_icon="📄")

st.title("📄 Divisor de PDF de Asistencias")
st.write("Sube un archivo PDF con varias planillas de asistencia y la app creará un PDF por persona con el nombre correspondiente.")

uploaded_file = st.file_uploader("Subir PDF", type=["pdf"])

# Diccionario para convertir número de mes a nombre
meses = {
    "01": "ENERO",
    "02": "FEBRERO",
    "03": "MARZO",
    "04": "ABRIL",
    "05": "MAYO",
    "06": "JUNIO",
    "07": "JULIO",
    "08": "AGOSTO",
    "09": "SEPTIEMBRE",
    "10": "OCTUBRE",
    "11": "NOVIEMBRE",
    "12": "DICIEMBRE"
}

if uploaded_file:
    reader = PdfReader(uploaded_file)
    total_pages = len(reader.pages)
    st.info(f"El archivo tiene {total_pages} páginas.")

    # Expresiones regulares para extraer datos
    regex_periodo = re.compile(r"Periodo desde\s+\d{2}/(\d{2})/\d{4}")
    regex_trabajador = re.compile(r"Trabajador RUT:\s*([\d\.-Kk]+)\s*Nombre:\s*(.+)")

    zip_buffer = io.BytesIO()

    with ZipFile(zip_buffer, "w") as zipf:
        for i in range(0, total_pages, 2):  # Cada trabajador ocupa 2 páginas
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            if i + 1 < total_pages:
                writer.add_page(reader.pages[i + 1])

            # Extraer texto de ambas páginas
            text = ""
            for j in range(2):
                if i + j < total_pages:
                    text += reader.pages[i + j].extract_text() or ""

            # Extraer mes
            mes_match = regex_periodo.search(text)
            mes_num = mes_match.group(1) if mes_match else "XX"
            mes_nombre = meses.get(mes_num, "MES_DESCONOCIDO")

            # Extraer RUT y nombre
            trab_match = regex_trabajador.search(text)
            if trab_match:
                rut = trab_match.group(1).replace(".", "").upper()
                nombre = trab_match.group(2).strip().upper().replace(" ", "_")
            else:
                rut, nombre = f"RUT_DESCONOCIDO_{i}", f"NOMBRE_DESCONOCIDO_{i}"

            filename = f"ASISTENCIA_{mes_nombre}_{rut}_{nombre}.pdf"

            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            zipf.writestr(filename, buffer.read())

    st.success("✅ Archivos generados correctamente.")
    st.download_button(
        "Descargar ZIP con PDFs",
        data=zip_buffer.getvalue(),
        file_name="Asistencias_Separadas.zip",
        mime="application/zip"
    )
