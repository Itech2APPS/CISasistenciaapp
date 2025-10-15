# app.py
import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import re
import io
from zipfile import ZipFile
import pandas as pd

st.set_page_config(page_title="Divisor de Libros de Asistencia", page_icon="📄")
st.title("📄 Divisor de PDF de Asistencias")
st.write("Sube un PDF y se generará 1 PDF por trabajador con la nomenclatura solicitada.")

# Diccionario para convertir número de mes a nombre
meses = {
    "01": "ENERO", "02": "FEBRERO", "03": "MARZO", "04": "ABRIL",
    "05": "MAYO", "06": "JUNIO", "07": "JULIO", "08": "AGOSTO",
    "09": "SEPTIEMBRE", "10": "OCTUBRE", "11": "NOVIEMBRE", "12": "DICIEMBRE"
}

uploaded_file = st.file_uploader("Subir PDF", type=["pdf"])

# Expresiones auxiliares (más tolerantes)
re_periodo = re.compile(r"Periodo\s+desde\s+\d{2}/(\d{2})/\d{4}", re.IGNORECASE)
# RUT: e.g. 12.599.237-4 or 12599237-4
re_rut = re.compile(r"(\d{1,2}\.?\d{3}\.?\d{3}-[0-9Kk])")
# Nombre tras "Nombre:" (permite saltos y espacios)
re_nombre_label = re.compile(r"Nombre:\s*(.+?)(?:\n|$)", re.IGNORECASE)
# Intento conjunto (trabajador RUT: ... Nombre: ...)
re_conjunto = re.compile(r"Trabajador\s+RUT:\s*([\d\.\-Kk]+)\s*Nombre:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.DOTALL)

if uploaded_file:
    reader = PdfReader(uploaded_file)
    total_pages = len(reader.pages)
    st.info(f"El archivo tiene {total_pages} páginas.")

    registros = []  # para vista previa en orden
    outputs = []    # guardaremos (filename, bytes) para el zip

    for i in range(0, total_pages, 2):
        # Construir pdf por persona (2 páginas consecutivas)
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        if i + 1 < total_pages:
            writer.add_page(reader.pages[i + 1])

        # Extraer texto de ambas páginas
        text = ""
        for j in range(2):
            if i + j < total_pages:
                page_text = reader.pages[i + j].extract_text() or ""
                text += page_text + "\n"

        # --- EXTRAER MES ---
        mes_match = re_periodo.search(text)
        mes_num = mes_match.group(1) if mes_match else None
        mes_nombre = meses.get(mes_num, "MES_DESCONOCIDO")

        # --- EXTRAER RUT y NOMBRE (múltiples intentos) ---
        rut = None
        nombre = None

        # 1) intento conjunto (más directo)
        m = re_conjunto.search(text)
        if m:
            rut_raw = m.group(1).strip()
            nombre_raw = m.group(2).strip()
            rut = rut_raw
            nombre = nombre_raw

        # 2) si no, buscar RUT y Nombre por separado
        if not rut:
            m_rut = re_rut.search(text)
            if m_rut:
                rut = m_rut.group(1).strip()

        if not nombre:
            m_nom = re_nombre_label.search(text)
            if m_nom:
                # tomar hasta final de línea; limpiar espacios excesivos
                nombre = m_nom.group(1).strip()

        # 3) fallback: puede que "Trabajador RUT:" esté en una línea y "Nombre:" en la siguiente
        if (not rut or not nombre):
            # buscar la línea que contiene "Trabajador" y parsearla
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            for ln in lines:
                if "Trabajador" in ln and ("RUT" in ln or "Nombre" in ln):
                    # intentar separar por "Nombre:"
                    if "Nombre:" in ln:
                        parts = ln.split("Nombre:")
                        left = parts[0]
                        right = parts[1]
                        # extraer rut desde left
                        m_rut2 = re_rut.search(left)
                        if m_rut2 and not rut:
                            rut = m_rut2.group(1).strip()
                        if right and not nombre:
                            nombre = right.strip()
                    else:
                        # si no tiene Nombre:, buscar rut en la línea y buscar "Nombre:" en la siguiente
                        m_rut2 = re_rut.search(ln)
                        if m_rut2 and not rut:
                            rut = m_rut2.group(1).strip()
                        # buscar siguiente línea que contenga "Nombre:"
                        # (usar index)
                        try:
                            idx = lines.index(ln)
                            if idx + 1 < len(lines):
                                next_ln = lines[idx + 1]
                                if next_ln.lower().startswith("nombre"):
                                    # "Nombre: AAA"
                                    m_nom2 = re_nombre_label.search(next_ln)
                                    if m_nom2 and not nombre:
                                        nombre = m_nom2.group(1).strip()
                        except ValueError:
                            pass

        # Limpieza final y normalización
        if rut:
            # quitar puntos y dejar el guion
            rut = rut.replace(".", "").upper()
        else:
            rut = f"RUT_DESCONOCIDO_{i}"

        if nombre:
            # transformar a mayúsculas y reemplazar espacios por guiones bajos para el filename
            nombre_proc = re.sub(r"\s+", "_", nombre.strip().upper())
            # eliminar caracteres problemáticos en filename
            nombre_proc = re.sub(r'[\\/:"*?<>|]+', "", nombre_proc)
            nombre = nombre_proc
        else:
            nombre = f"NOMBRE_DESCONOCIDO_{i}"

        filename = f"ASISTENCIA_{mes_nombre}_{rut}_{nombre}.pdf"

        # escribir pdf a bytes
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        outputs.append((filename, buffer.read()))

        # guardar registro para vista previa (manteniendo orden)
        registros.append({"Página_inicio": i+1, "Mes": mes_nombre, "RUT": rut, "Nombre": nombre, "Archivo": filename})

    # Mostrar vista previa
    df = pd.DataFrame(registros)
    st.subheader("Vista previa (orden original)")
    st.dataframe(df[["Página_inicio", "Mes", "RUT", "Nombre", "Archivo"]], use_container_width=True)

    # Botón para generar ZIP (evita generar sin revisar)
    if st.button("Generar ZIP con los PDFs"):
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "w") as zipf:
            for fname, data in outputs:
                zipf.writestr(fname, data)
        st.success("✅ ZIP generado.")
        st.download_button("Descargar ZIP", data=zip_buffer.getvalue(), file_name="Asistencias_Separadas.zip", mime="application/zip")
