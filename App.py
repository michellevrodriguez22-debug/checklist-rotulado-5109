import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# -----------------------------------------------------------
# CONFIGURACIÓN INICIAL
# -----------------------------------------------------------
st.set_page_config(page_title="Verificador de Etiquetado Nutricional", layout="wide")
st.title("Verificador de Etiquetado Nutricional — Resoluciones 5109, 810 y 2492")

# -----------------------------------------------------------
# DATOS GENERALES
# -----------------------------------------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
nombre_pdf = st.sidebar.text_input("Nombre del archivo PDF (sin .pdf)", f"informe_{datetime.now().strftime('%Y%m%d')}")
filter_no = st.sidebar.checkbox("Mostrar solo 'No cumple'", value=False)

# -----------------------------------------------------------
# CATEGORÍAS E ÍTEMS (resumido para brevedad)
# -----------------------------------------------------------
CATEGORIAS = {
    "5. Etiquetado frontal de advertencia (Sellos negros)": [
        ("Aplicabilidad", "Verificar si aplica por exceso de azúcares, grasas saturadas, sodio o edulcorantes.",
         "Evaluar composición para determinar necesidad de sellos.", "Art. 32 Resol. 810 modif. 2492/2022"),
        ("Forma y color", "Revisar que el sello sea octagonal negro con borde blanco y texto 'EXCESO EN'.",
         "Corregir forma o color según especificación oficial.", "Art. 32 Resol. 2492/2022"),
        ("Ubicación", "Comprobar que esté en el tercio superior del panel principal.",
         "Reubicar sello si no cumple posición.", "Art. 32 Resol. 2492/2022"),
        ("Tamaño del sello", "Verificar proporción con el área del envase según Tabla 17 de la Resolución 810 modificada por 2492/2022.",
         "Ajustar tamaño del sello según tabla normativa.", "Art. 32 Resol. 810 modif. 2492/2022"),
        ("Tipografía", "Verificar uso de fuente Arial Black, texto blanco sobre fondo negro.",
         "Corregir tipografía o contraste del sello.", "Art. 32 Resol. 810/2021"),
    ]
}

# -----------------------------------------------------------
# ESTADO INICIAL
# -----------------------------------------------------------
if "status" not in st.session_state:
    st.session_state.status = {i[0]: "none" for c in CATEGORIAS.values() for i in c}
if "note" not in st.session_state:
    st.session_state.note = {i[0]: "" for c in CATEGORIAS.values() for i in c}

# -----------------------------------------------------------
# INTERFAZ DE CHECKLIST
# -----------------------------------------------------------
st.header("Checklist normativo completo")
st.markdown("Cada criterio incluye **qué verificar**, su **recomendación** y **referencia normativa**.")

for categoria, items in CATEGORIAS.items():
    st.subheader(categoria)

    for item in items:
        titulo, que_verificar, recomendacion, referencia = item
        estado = st.session_state.status.get(titulo, "none")

        if filter_no and estado != "no":
            continue

        st.markdown(f"### {titulo}")
        st.markdown(f"**Qué verificar:** {que_verificar}")
        st.markdown(f"**Referencia:** {referencia}")

        # --- DESPLEGABLE INFORMATIVO SOLO PARA “Tamaño del sello” ---
        if titulo == "Tamaño del sello":
            st.markdown("**Referencia normativa: Tabla 17 — Tamaño mínimo del sello según el área principal del envase**")
            opciones_tabla17 = {
                "< 30 cm²": "1,5 cm de lado",
                "30 a < 60 cm²": "2,0 cm de lado",
                "60 a < 80 cm²": "2,5 cm de lado",
                "80 a < 100 cm²": "3,0 cm de lado",
                "100 a < 200 cm²": "3,5 cm de lado",
                "200 a < 300 cm²": "4,0 cm de lado",
                "300 a < 500 cm²": "5,0 cm de lado",
                "≥ 500 cm²": "6,0 cm de lado"
            }
            seleccion_tabla17 = st.selectbox(
                "Consulta informativa (no se guarda en el reporte):",
                options=list(opciones_tabla17.keys()),
                key=f"tabla17_{titulo}"
            )
            st.info(f"Tamaño mínimo del sello para envases de {seleccion_tabla17}: **{opciones_tabla17[seleccion_tabla17]}**")

        c1, c2, c3, _ = st.columns([0.12, 0.12, 0.12, 0.64])
        with c1:
            if st.button("✅ Cumple", key=f"{titulo}_yes"):
                st.session_state.status[titulo] = "yes"
        with c2:
            if st.button("❌ No cumple", key=f"{titulo}_no"):
                st.session_state.status[titulo] = "no"
        with c3:
            if st.button("⚪ No aplica", key=f"{titulo}_na"):
                st.session_state.status[titulo] = "na"

        estado = st.session_state.status[titulo]
        if estado == "yes":
            st.markdown("<div style='background:#e6ffed;padding:6px;border-radius:5px;'>✅ Cumple</div>", unsafe_allow_html=True)
        elif estado == "no":
            st.markdown(f"<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple — {recomendacion}</div>", unsafe_allow_html=True)
        elif estado == "na":
            st.markdown("<div style='background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

        nota = st.text_area("Observación (opcional)", value=st.session_state.note.get(titulo, ""), key=f"{titulo}_nota")
        st.session_state.note[titulo] = nota
        st.markdown("---")

# -----------------------------------------------------------
# CÁLCULO DE CUMPLIMIENTO
# -----------------------------------------------------------
yes_count = sum(1 for v in st.session_state.status.values() if v == "yes")
no_count = sum(1 for v in st.session_state.status.values() if v == "no")
answered = yes_count + no_count
percent = round((yes_count / answered * 100), 1) if answered > 0 else 0

st.metric("Cumplimiento total", f"{percent}%")

# -----------------------------------------------------------
# FUNCIONES AUXILIARES Y PDF
# -----------------------------------------------------------
def split_observation_text(text, chunk=100):
    if not text:
        return ""
    s = str(text)
    if len(s) <= chunk:
        return s
    return "\n".join([s[i:i+chunk] for i in range(0, len(s), chunk)])

def generar_pdf(df, producto, proveedor, responsable, porcentaje, nombre_archivo):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=8*mm, rightMargin=8*mm, topMargin=8*mm, bottomMargin=8*mm)
    styles = getSampleStyleSheet()
    style_header = ParagraphStyle("header", parent=styles["Normal"], fontSize=8, leading=10)
    style_cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=7.5, leading=9)
    story = []

    story.append(Paragraph("<b>Informe de verificación de etiquetado nutricional — Juan Valdez</b>", style_header))
    story.append(Spacer(1, 3*mm))
    fecha = datetime.now().strftime("%Y-%m-%d")
    story.append(Paragraph(f"<b>Fecha:</b> {fecha} &nbsp;&nbsp; <b>Producto:</b> {producto or '-'} &nbsp;&nbsp; "
                           f"<b>Proveedor:</b> {proveedor or '-'} &nbsp;&nbsp; "
                           f"<b>Responsable:</b> {responsable or '-'}", style_header))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"<b>Cumplimiento:</b> {porcentaje}%", style_header))
    story.append(Spacer(1, 5*mm))

    data = [["Ítem", "Estado", "Recomendación", "Referencia", "Observación"]]
    for k, v in st.session_state.status.items():
        obs = st.session_state.note.get(k, "") or "-"
        obs = split_observation_text(obs, chunk=100) if obs != "-" else obs
        row = next((i for c in CATEGORIAS.values() for i in c if i[0] == k), None)
        if row:
            data.append([Paragraph(row[0], style_cell),
                         Paragraph("Cumple" if v=="yes" else "No cumple" if v=="no" else "No aplica" if v=="na" else "Sin responder", style_cell),
                         Paragraph(row[2], style_cell),
                         Paragraph(row[3], style_cell),
                         Paragraph(obs, style_cell)])

    col_widths = [70*mm, 25*mm, 100*mm, 45*mm, 40*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------
# BOTÓN PDF
# -----------------------------------------------------------
st.subheader("Generar informe PDF (A4 horizontal)")
if st.button("Generar PDF"):
    pdf = generar_pdf(None, producto, proveedor, responsable, percent, nombre_pdf)
    st.download_button("Descargar PDF", data=pdf, file_name=f"{nombre_pdf}.pdf", mime="application/pdf")
