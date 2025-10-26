import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
st.set_page_config(page_title="Verificador de Etiquetado Nutricional", layout="wide")
st.title("Verificador de Etiquetado Nutricional — Resoluciones 5109, 810 y 2492")

# -----------------------------
# DATOS DE VERIFICACIÓN
# -----------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
nombre_pdf = st.sidebar.text_input("Nombre del archivo PDF (sin .pdf)", f"informe_{datetime.now().strftime('%Y%m%d')}")
filter_no = st.sidebar.checkbox("Mostrar solo 'No cumple'", value=False)

# -----------------------------
# LISTA DE ÍTEMS
# -----------------------------
CHECK_ITEMS = [
    ("Denominación del producto correcta", "Modificar la denominación para reflejar el tipo de alimento según ingredientes principales.", "Resol. 5109 Art. 4"),
    ("Lista de ingredientes en orden decreciente", "Agregar lista completa de ingredientes y verificar su orden.", "Resol. 5109 Art. 6"),
    ("Contenido neto declarado en unidades SI", "Corregir etiqueta para usar unidades del Sistema Internacional.", "Resol. 5109 Art. 7"),
    ("Datos del fabricante o importador visibles", "Incluir datos completos del responsable del producto.", "Resol. 5109 Art. 8"),
    ("Lote y fecha de vencimiento legibles", "Asegurar impresión legible y formato correcto (día/mes/año).", "Resol. 5109 Art. 10–11"),
    ("Idioma español obligatorio", "Agregar rótulo complementario en español si aplica.", "Resol. 5109 Art. 18"),
    ("Tabla de información nutricional presente", "Incluir tabla de información nutricional con borde negro visible.", "Resol. 810 Art. 27"),
    ("Columnas 'Por 100 g/mL' y 'Por porción'", "Agregar o corregir las columnas según la norma.", "Resol. 810 Art. 30"),
    ("Orden de nutrientes obligatorio", "Ajustar el orden y unidades según la norma.", "Resol. 810 Art. 28"),
    ("Vitaminas y minerales declarados correctamente", "Corregir unidades o formato según la resolución.", "Resol. 810 Art. 28.3"),
    ("Frase 'No es fuente significativa de…' (si aplica)", "Agregar la frase cuando haya nutrientes en cantidades no significativas.", "Resol. 810 Art. 27.1.2"),
    ("Presencia de sellos frontales cuando aplica", "Agregar o retirar sellos conforme a los valores declarados.", "Resol. 810/2492"),
    ("Forma y color del sello", "Rediseñar sellos conforme a especificaciones oficiales.", "Resol. 810/2492"),
    ("Tamaño proporcional del sello", "Ajustar tamaño para cumplir proporción mínima.", "Resol. 810/2492"),
    ("Ubicación del sello frontal", "Reubicar sello en área principal visible.", "Resol. 810/2492"),
    ("Declaración de alérgenos visible", "Agregar declaración de alérgenos en lugar visible.", "Resol. 5109/810"),
    ("Advertencias especiales (edulcorantes, cafeína, etc.)", "Incluir advertencias obligatorias conforme a la norma.", "Resol. 810"),
    ("Claims nutricionales o saludables verificables", "Retirar claims no verificables o añadir respaldo técnico.", "Resol. 333/2011 y 810"),
    ("Contraste y legibilidad del texto", "Mejorar contraste o posición del texto.", "Resol. 5109/810"),
    ("Etiqueta complementaria para productos importados", "Agregar etiqueta conforme a la normativa colombiana.", "Resol. 5109 Parágrafo"),
]

if "status" not in st.session_state:
    st.session_state.status = {i[0]: "none" for i in CHECK_ITEMS}
if "note" not in st.session_state:
    st.session_state.note = {i[0]: "" for i in CHECK_ITEMS}

# -----------------------------
# CHECKLIST INTERACTIVO
# -----------------------------
st.header("Checklist normativo")
for item in CHECK_ITEMS:
    nombre, recomendacion, referencia = item
    estado = st.session_state.status.get(nombre, "none")

    if filter_no and estado != "no":
        continue

    st.markdown(f"### {nombre}")
    c1, c2, c3, _ = st.columns([0.12, 0.12, 0.12, 0.64])
    with c1:
        if st.button("✅ Cumple", key=f"{nombre}_yes"):
            st.session_state.status[nombre] = "yes"
    with c2:
        if st.button("❌ No cumple", key=f"{nombre}_no"):
            st.session_state.status[nombre] = "no"
    with c3:
        if st.button("⚪ No aplica", key=f"{nombre}_na"):
            st.session_state.status[nombre] = "na"

    estado = st.session_state.status[nombre]
    if estado == "yes":
        st.markdown("<div style='background:#e6ffed;padding:6px;border-radius:5px;'>✅ Cumple</div>", unsafe_allow_html=True)
    elif estado == "no":
        st.markdown(f"<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple — {recomendacion}</div>", unsafe_allow_html=True)
    elif estado == "na":
        st.markdown("<div style='background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

    nota = st.text_area("Observación (opcional)", value=st.session_state.note.get(nombre, ""), key=f"{nombre}_nota")
    st.session_state.note[nombre] = nota
    st.markdown("---")

# -----------------------------
# CÁLCULO DE CUMPLIMIENTO
# -----------------------------
yes_count = sum(1 for v in st.session_state.status.values() if v == "yes")
no_count = sum(1 for v in st.session_state.status.values() if v == "no")
answered = yes_count + no_count
porcentaje = round((yes_count / answered * 100), 1) if answered > 0 else 0
st.metric("Cumplimiento total", f"{porcentaje}%")

# -----------------------------
# GENERAR PDF
# -----------------------------
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

    # Cabecera
    data = [["Ítem", "Estado", "Recomendación", "Referencia", "Observación"]]

    for _, r in df.iterrows():
        obs_text = r["Observación"] or "-"
        if len(obs_text) > 100:
            obs_text = '\n'.join([obs_text[i:i+100] for i in range(0, len(obs_text), 100)])

        data.append([
            Paragraph(str(r["Ítem"]), style_cell),
            Paragraph(str(r["Estado"]), style_cell),
            Paragraph(str(r["Recomendación"]), style_cell),
            Paragraph(str(r["Referencia"]), style_cell),
            Paragraph(obs_text, style_cell)
        ])

    # Columna ajustada al ancho total de A4 horizontal (275 mm aprox)
    col_widths = [70*mm, 25*mm, 100*mm, 45*mm, 55*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 8),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
    ]))

    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

df = pd.DataFrame([{
    "Ítem": i[0],
    "Estado": ("Cumple" if st.session_state.status[i[0]] == "yes" else
               "No cumple" if st.session_state.status[i[0]] == "no" else
               "No aplica" if st.session_state.status[i[0]] == "na" else "Sin responder"),
    "Recomendación": i[1],
    "Referencia": i[2],
    "Observación": st.session_state.note[i[0]]
} for i in CHECK_ITEMS])

st.subheader("Generar informe PDF")
if st.button("Generar PDF"):
    pdf = generar_pdf(df, producto, proveedor, responsable, porcentaje, nombre_pdf)
    st.download_button("Descargar PDF", data=pdf, file_name=f"{nombre_pdf}.pdf", mime="application/pdf")
