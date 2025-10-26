# app.py
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
# Configuración general
# -----------------------------
st.set_page_config(page_title="Verificador de Etiquetado — Resoluciones 5109, 810 y 2492", layout="wide")
st.title("Verificador de Etiquetado Nutricional — Resoluciones 5109, 810 y 2492")
st.markdown("Aplicativo interactivo para verificación del cumplimiento de etiquetado de alimentos según normativa colombiana vigente.")

# -----------------------------
# Datos del checklist
# -----------------------------
CHECK_ITEMS = [
    # Resolución 5109
    ("Denominación del producto correcta",
     "Verificar que la denominación describa el alimento según su naturaleza, sin inducir a error.",
     "Modificar la denominación para reflejar el tipo de alimento según ingredientes principales.",
     "Resol. 5109 Art. 4"),
    ("Lista de ingredientes en orden decreciente",
     "Confirmar que todos los ingredientes estén listados en orden de peso en español.",
     "Agregar lista completa de ingredientes y verificar su orden.",
     "Resol. 5109 Art. 6"),
    ("Contenido neto declarado en unidades SI",
     "Revisar que el contenido neto esté en g, mL o L y sea legible.",
     "Corregir etiqueta para usar unidades del Sistema Internacional.",
     "Resol. 5109 Art. 7"),
    ("Datos del fabricante o importador visibles",
     "Verificar nombre o razón social y dirección del responsable.",
     "Incluir datos completos del responsable del producto.",
     "Resol. 5109 Art. 8"),
    ("Lote y fecha de vencimiento legibles",
     "Comprobar existencia y formato de lote y fecha.",
     "Asegurar impresión legible y formato correcto (día/mes/año).",
     "Resol. 5109 Art. 10–11"),
    ("Idioma español obligatorio",
     "Verificar que toda la información esté en español.",
     "Agregar rótulo complementario en español si aplica.",
     "Resol. 5109 Art. 18"),

    # Resolución 810 y 2492 — Información nutricional
    ("Tabla de información nutricional presente",
     "Confirmar que exista la tabla dentro de un recuadro visible.",
     "Incluir tabla de información nutricional con borde negro visible.",
     "Resol. 810 Art. 27"),
    ("Columnas 'Por 100 g/mL' y 'Por porción'",
     "Revisar que estén ambas columnas con títulos exactos.",
     "Agregar o corregir las columnas según la norma.",
     "Resol. 810 Art. 30"),
    ("Orden de nutrientes obligatorio",
     "Verificar el orden normativo: calorías, grasa total, grasa saturada, trans, carbohidratos, fibra, azúcares, añadidos, proteína, sodio.",
     "Ajustar el orden y unidades según la norma.",
     "Resol. 810 Art. 28"),
    ("Vitaminas y minerales declarados correctamente",
     "Comprobar orden, unidades (mg, µg, UI) y línea separadora.",
     "Corregir unidades o formato según la resolución.",
     "Resol. 810 Art. 28.3"),
    ("Frase 'No es fuente significativa de…' (si aplica)",
     "Verificar si aplica y que esté incluida dentro del recuadro.",
     "Agregar la frase cuando haya nutrientes en cantidades no significativas.",
     "Resol. 810 Art. 27.1.2"),

    # Etiquetado frontal (810 y 2492)
    ("Presencia de sellos frontales cuando aplica",
     "Verificar que los sellos aparezcan solo si se superan los umbrales normativos.",
     "Agregar o retirar sellos conforme a los valores declarados.",
     "Resol. 810/2492"),
    ("Forma y color del sello",
     "Revisar forma octogonal, fondo negro, borde blanco y texto centrado.",
     "Rediseñar sellos conforme a especificaciones oficiales.",
     "Resol. 810/2492"),
    ("Tamaño proporcional del sello",
     "Comprobar que ocupe al menos el 10% del área principal del envase.",
     "Ajustar tamaño para cumplir proporción mínima.",
     "Resol. 810/2492"),
    ("Ubicación del sello frontal",
     "Verificar que esté en la parte superior derecha sin interferencias.",
     "Reubicar sello en área principal visible.",
     "Resol. 810/2492"),

    # Claims y advertencias
    ("Declaración de alérgenos visible",
     "Comprobar leyendas 'Contiene…' o 'Puede contener…'.",
     "Agregar declaración de alérgenos en lugar visible.",
     "Resol. 5109/810"),
    ("Advertencias especiales (edulcorantes, cafeína, etc.)",
     "Verificar presencia de advertencias según los ingredientes.",
     "Incluir advertencias obligatorias conforme a la norma.",
     "Resol. 810"),
    ("Claims nutricionales o saludables verificables",
     "Revisar que cualquier claim tenga sustento técnico y cumpla requisitos.",
     "Retirar claims no verificables o añadir respaldo técnico.",
     "Resol. 333/2011 y 810"),

    # Presentación y legibilidad
    ("Contraste y legibilidad del texto",
     "Comprobar que los textos sean claros y sin sobreimpresiones.",
     "Mejorar contraste o posición del texto.",
     "Resol. 5109/810"),
    ("Etiqueta complementaria para productos importados",
     "Verificar existencia y adherencia correcta de la etiqueta complementaria.",
     "Agregar etiqueta conforme a la normativa colombiana.",
     "Resol. 5109 Parágrafo"),
]

# -----------------------------
# Estado inicial
# -----------------------------
def init_state():
    if "status" not in st.session_state:
        st.session_state.status = {}
    if "note" not in st.session_state:
        st.session_state.note = {}
    for item in CHECK_ITEMS:
        key = item[0]
        st.session_state.status.setdefault(key, "none")
        st.session_state.note.setdefault(key, "")

init_state()

# -----------------------------
# Formulario inicial
# -----------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
nombre_pdf = st.sidebar.text_input("Nombre del archivo PDF (sin .pdf)", f"informe_{datetime.now().strftime('%Y%m%d')}")
st.sidebar.markdown("---")

# -----------------------------
# Checklist
# -----------------------------
st.header("Checklist de cumplimiento normativo")
st.markdown("Seleccione el estado correspondiente a cada requisito. Si marca **No cumple**, se mostrará una recomendación.")

for item in CHECK_ITEMS:
    nombre, verificar, recomendacion, referencia = item
    estado = st.session_state.status.get(nombre, "none")

    st.markdown(f"### {nombre}")
    st.markdown(f"**Qué verificar:** {verificar}")
    st.markdown(f"**Referencia:** {referencia}")

    c1, c2, c3 = st.columns([0.2, 0.2, 0.6])
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
# Resumen
# -----------------------------
total = len(CHECK_ITEMS)
cumple = sum(1 for k, v in st.session_state.status.items() if v == "yes")
no_cumple = sum(1 for k, v in st.session_state.status.items() if v == "no")
na = sum(1 for k, v in st.session_state.status.items() if v == "na")
responde = total - sum(1 for v in st.session_state.status.values() if v == "none")
denom = total - na
porcentaje = int(round((cumple / denom * 100) if denom > 0 else 0))

st.metric("Cumplimiento total", f"{porcentaje}%")
st.write(f"Cumple: {cumple} — No cumple: {no_cumple} — No aplica: {na} — Sin responder: {total - responde}")

# -----------------------------
# Generar PDF horizontal (A4)
# -----------------------------
def generar_pdf(df, producto, proveedor, responsable, porcentaje, nombre_archivo):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_bold = ParagraphStyle("bold", parent=style_normal, fontSize=10, spaceAfter=6)

    story = []
    story.append(Paragraph("<b>Informe de verificación de etiquetado nutricional — Juan Valdez</b>", style_bold))
    story.append(Spacer(1, 4 * mm))
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    info = f"<b>Fecha:</b> {fecha_actual} &nbsp;&nbsp; <b>Producto:</b> {producto or '-'} &nbsp;&nbsp; <b>Proveedor:</b> {proveedor or '-'} &nbsp;&nbsp; <b>Responsable:</b> {responsable or '-'}"
    story.append(Paragraph(info, style_normal))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"<b>Cumplimiento total:</b> {porcentaje}%", style_bold))
    story.append(Spacer(1, 6 * mm))

    data = [["Ítem", "Estado", "Recomendación", "Referencia", "Observación"]]
    for _, row in df.iterrows():
        data.append([
            row["Ítem"],
            row["Estado"],
            row["Recomendación"],
            row["Referencia"],
            row["Observación"]
        ])

    col_widths = [70 * mm, 25 * mm, 75 * mm, 40 * mm, 80 * mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

# Generar DataFrame
df = pd.DataFrame([{
    "Ítem": item[0],
    "Estado": ("Cumple" if st.session_state.status[item[0]] == "yes" else
               "No cumple" if st.session_state.status[item[0]] == "no" else
               "No aplica" if st.session_state.status[item[0]] == "na" else "Sin responder"),
    "Recomendación": item[2],
    "Referencia": item[3],
    "Observación": st.session_state.note[item[0]]
} for item in CHECK_ITEMS])

# Botón para generar PDF
st.subheader("Generar informe PDF (horizontal, empresarial)")
if st.button("Generar PDF"):
    pdf_buffer = generar_pdf(df, producto, proveedor, responsable, porcentaje, nombre_pdf)
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=f"{nombre_pdf}.pdf", mime="application/pdf")
