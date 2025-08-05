import streamlit as st
import fitz  # PyMuPDF
import re
import os
from zipfile import ZipFile
import tempfile

# --- FUNCIONES ---  - BY ISMAEL LEON

def extraer_datos_por_lineas(texto):
    lineas = texto.strip().splitlines()
    if len(lineas) < 10:
        return None, None, None

    # Línea 5: fecha en formato dd/mm/yyyy  - BY ISMAEL LEON
    linea_fecha = lineas[4].strip()
    match_mes = re.search(r'\d{2}/(\d{2})/2025', linea_fecha)
    mes_num = match_mes.group(1) if match_mes else None

    meses = {
        '01': 'ENERO', '02': 'FEBRERO', '03': 'MARZO', '04': 'ABRIL',
        '05': 'MAYO', '06': 'JUNIO', '07': 'JULIO', '08': 'AGOSTO',
        '09': 'SEPTIEMBRE', '10': 'OCTUBRE', '11': 'NOVIEMBRE', '12': 'DICIEMBRE'
    }
    mes = meses.get(mes_num, 'MES') if mes_num else None

    # Línea 8: RUT - BY ISMAEL LEON
    rut = lineas[7].strip()
    if rut.startswith("65.191"):
        return None, None, None

    # Línea 9: nombre completo - BY ISMAEL LEON
    nombre = lineas[8].strip()

    return mes, rut, nombre

def procesar_pdf(file, temp_dir, mostrar_texto=False):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    archivos = []
    vistas_previas = []

    for i in range(0, len(doc), 2):  # solo páginas impares - BY ISMAEL LEON
        pagina = doc.load_page(i)
        texto = pagina.get_text().upper()

        if mostrar_texto:
            vistas_previas.append((i + 1, texto))

        mes, rut, nombre = extraer_datos_por_lineas(texto)
        if not mes or not rut or not nombre:
            continue

        nombre_archivo = f"ASISTENCIA_{mes}_{rut}_{nombre}.pdf".replace(" ", "_")
        ruta_pdf = os.path.join(temp_dir, nombre_archivo)

        nuevo_pdf = fitz.open()
        nuevo_pdf.insert_pdf(doc, from_page=i, to_page=i)
        nuevo_pdf.save(ruta_pdf)
        nuevo_pdf.close()
        archivos.append(ruta_pdf)

    if not archivos:
        return None, vistas_previas

    zip_path = os.path.join(temp_dir, "ASISTENCIAS.zip")
    with ZipFile(zip_path, 'w') as zipf:
        for archivo in archivos:
            zipf.write(archivo, arcname=os.path.basename(archivo))

    return zip_path, vistas_previas

# --- INTERFAZ STREAMLIT ---- BY ISMAEL LEON

st.set_page_config(page_title="Separador de Asistencia", page_icon="🗂️")
st.title("🗂️ Separador de Asistencias por Persona")

st.write("""
Sube un archivo PDF con múltiples páginas de asistencia.  
Se generará un PDF individual por cada persona (sólo en páginas impares), con nombre:
`ASISTENCIA_MES_RUT_NOMBRE COMPLETO.pdf`
""")

uploaded_file = st.file_uploader("📤 Sube el archivo PDF", type="pdf")
ver_texto = st.checkbox("🔍 Mostrar texto extraído por página impar")

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        with st.spinner("🔍 Procesando PDF..."):
            zip_path, vistas_previas = procesar_pdf(uploaded_file, tmpdir, mostrar_texto=ver_texto)

        if zip_path:
            st.success("✅ ¡ZIP generado correctamente!")
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="📥 Descargar ZIP",
                    data=f,
                    file_name="asistencias.zip",
                    mime="application/zip"
                )
        else:
            st.error("❌ No se generó ningún archivo. Verifica que las páginas tengan al menos 10 líneas y datos válidos.")

        if ver_texto and vistas_previas:
            st.divider()
            st.subheader("🧾 Texto extraído por página impar (primeras 15 líneas)")
            for pagina, texto in vistas_previas:
                lineas = texto.strip().splitlines()
                st.markdown(f"### Página {pagina} — {len(lineas)} líneas detectadas")
                vista = "\n".join([f"{i+1:02d}: {linea}" for i, linea in enumerate(lineas[:15])])
                st.code(vista, language="text")

# 👣 Footer opcional - BY ISMAEL LEON
st.markdown("<hr style='margin-top:40px;'>", unsafe_allow_html=True)
st.markdown("Desarrollado por Ismael León – © 2025", unsafe_allow_html=True)

