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
# DATOS DE VERIFICACIÓN (sidebar)
# -----------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
nombre_pdf = st.sidebar.text_input("Nombre del archivo PDF (sin .pdf)", f"informe_{datetime.now().strftime('%Y%m%d')}")
filter_no = st.sidebar.checkbox("Mostrar solo 'No cumple'", value=False)

# -----------------------------
# LISTA DE ÍTEMS con "Qué verificar"
# Cada item: (Título, Qué verificar, Recomendación, Referencia)
# -----------------------------
CHECK_ITEMS = [
    ("Denominación del producto correcta",
     "Verificar que la denominación describa el alimento según su naturaleza; no utilizar nombres que induzcan a error.",
     "Modificar la denominación para reflejar el tipo de alimento según ingredientes principales.",
     "Resol. 5109 Art. 4"),

    ("Lista de ingredientes en orden decreciente",
     "Comprobar que todos los ingredientes estén listados en español y en orden de mayor a menor proporción.",
     "Agregar lista completa de ingredientes y verificar su orden.",
     "Resol. 5109 Art. 6"),

    ("Contenido neto declarado en unidades SI",
     "Revisar que el contenido neto esté expresado en g, mL o L según corresponda y que sea legible.",
     "Corregir etiqueta para usar unidades del Sistema Internacional.",
     "Resol. 5109 Art. 7"),

    ("Datos del fabricante o importador visibles",
     "Verificar que el nombre o razón social y la dirección del responsable estén en la etiqueta.",
     "Incluir datos completos del responsable del producto.",
     "Resol. 5109 Art. 8"),

    ("Lote y fecha de vencimiento legibles",
     "Comprobar existencia de lote y fecha, formato legible (día/mes/año) y ubicación visible.",
     "Asegurar impresión legible y formato correcto.",
     "Resol. 5109 Art. 10–11"),

    ("Idioma español obligatorio",
     "Verificar que la información obligatoria figure en español; si no, debe existir rótulo complementario adherido.",
     "Agregar rótulo complementario en español si aplica.",
     "Resol. 5109 Art. 18"),

    ("Tabla de información nutricional presente",
     "Confirmar que la tabla figura en la etiqueta, en un recuadro visible y en idioma español.",
     "Incluir tabla de información nutricional con borde negro visible.",
     "Resol. 810 Art. 27"),

    ("Columnas 'Por 100 g/mL' y 'Por porción'",
     "Comprobar que existan ambas columnas: 'Por 100 g' o 'Por 100 mL' y 'Por porción'.",
     "Agregar o corregir las columnas según la norma.",
     "Resol. 810 Art. 30"),

    ("Orden de nutrientes obligatorio",
     "Verificar que el orden sea: calorías, grasa total, grasa saturada, grasas trans, carbohidratos, fibra dietaria, azúcares totales, azúcares añadidos, proteína y sodio.",
     "Ajustar la tabla para mostrar nutrientes en el orden normativo y con unidades correctas.",
     "Resol. 810 Art. 28"),

    ("Vitaminas y minerales declarados correctamente",
     "Si se declaran, comprobar orden (tabla 9), unidades (mg, µg, UI) y que estén separados con línea.",
     "Corregir unidades, orden y separación de micronutrientes según la resolución.",
     "Resol. 810 Art. 28.3"),

    ("Frase 'No es fuente significativa de…' (si aplica)",
     "Verificar si hay nutrientes en cantidades no significativas y que la frase figure dentro del recuadro.",
     "Agregar la frase dentro del recuadro según proceda.",
     "Resol. 810 Art. 27.1.2"),

    ("Presencia de sellos frontales cuando aplica",
     "Según valores declarados, comprobar si corresponde aplicar sellos de advertencia frontales.",
     "Agregar o retirar sellos conforme a los umbrales normativos.",
     "Resol. 810/2492"),

    ("Forma y color del sello",
     "Comprobar que el sello es octógono, fondo negro y texto en blanco; sin alteraciones cromáticas ni deformaciones.",
     "Rediseñar sellos conforme a especificaciones oficiales.",
     "Resol. 810/2492"),

    ("Tamaño proporcional del sello",
     "Verificar que el sello tenga la proporción mínima requerida respecto al área principal del envase.",
     "Ajustar tamaño para cumplir proporción mínima establecida.",
     "Resol. 810/2492"),

    ("Ubicación del sello frontal",
     "Confirmar que el sello esté en la cara principal, preferiblemente en la parte superior derecha, sin obstrucciones.",
     "Reubicar sello en área principal visible si es necesario.",
     "Resol. 810/2492"),

    ("Declaración de alérgenos visible",
     "Comprobar presencia de leyenda 'Contiene:' o 'Puede contener trazas de:' cuando aplique.",
     "Agregar declaración de alérgenos en lugar visible si falta.",
     "Resol. 5109/810"),

    ("Advertencias especiales (edulcorantes, cafeína, etc.)",
     "Verificar que las advertencias exigidas por ingredientes estén presentes (p. ej. edulcorantes, cafeína).",
     "Incluir advertencias obligatorias conforme a la norma.",
     "Resol. 810"),

    ("Claims nutricionales o saludables verificables",
     "Revisar que cualquier claim esté respaldado y cumpla requisitos legales y técnicos.",
     "Retirar claims no verificables o adjuntar evidencia técnica.",
     "Resol. 333/2011 y 810"),

    ("Contraste y legibilidad del texto",
     "Verificar contraste de texto/fondo, tamaño y que no existan sobreimpresiones que obstaculicen lectura.",
     "Mejorar contraste o reposicionar texto para garantizar legibilidad.",
     "Resol. 5109/810"),

    ("Etiqueta complementaria para productos importados",
     "Comprobar que exista etiqueta complementaria adherida con la información en español cuando el empaque original no esté en español.",
     "Agregar etiqueta complementaria conforme a la normativa nacional.",
     "Resol. 5109 Parágrafo"),
]

# -----------------------------
# Estado inicial
# -----------------------------
if "status" not in st.session_state:
    st.session_state.status = {item[0]: "none" for item in CHECK_ITEMS}
if "note" not in st.session_state:
    st.session_state.note = {item[0]: "" for item in CHECK_ITEMS}

# -----------------------------
# INTERFAZ: checklist con "Qué verificar"
# -----------------------------
st.header("Checklist normativo (guía de verificación incluida)")
st.markdown("Para cada criterio se muestra **qué verificar**. Responda con ✅ Cumple / ❌ No cumple / ⚪ No aplica. Si marca 'No cumple' aparecerá la recomendación asociada.")

for item in CHECK_ITEMS:
    titulo, que_verificar, recomendacion, referencia = item
    estado = st.session_state.status.get(titulo, "none")

    # filtrar si se pide mostrar solo 'No cumple'
    if filter_no and estado != "no":
        continue

    st.markdown(f"### {titulo}")
    st.markdown(f"**Qué verificar:** {que_verificar}")
    st.markdown(f"**Referencia:** {referencia}")

    # botones horizontales compactos
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

    # badge de estado y recomendación si aplica
    estado = st.session_state.status[titulo]
    if estado == "yes":
        st.markdown("<div style='display:inline-block;background:#e6ffed;padding:6px;border-radius:5px;'>✅ Cumple</div>", unsafe_allow_html=True)
    elif estado == "no":
        st.markdown(f"<div style='display:inline-block;background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple — {recomendacion}</div>", unsafe_allow_html=True)
    elif estado == "na":
        st.markdown("<div style='display:inline-block;background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='display:inline-block;background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

    nota = st.text_area("Observación (opcional)", value=st.session_state.note.get(titulo, ""), key=f"{titulo}_nota")
    st.session_state.note[titulo] = nota
    st.markdown("---")

# -----------------------------
# CÁLCULO DE CUMPLIMIENTO (corregido)
# -----------------------------
yes_count = sum(1 for v in st.session_state.status.values() if v == "yes")
no_count = sum(1 for v in st.session_state.status.values() if v == "no")
answered = yes_count + no_count
porcentaje = round((yes_count / answered * 100), 1) if answered > 0 else 0

st.metric("Cumplimiento total (sobre items contestados)", f"{porcentaje}%")
st.write(f"Contestados (Sí/No): {answered} — Cumple: {yes_count} — No cumple: {no_count} — No aplica: {sum(1 for v in st.session_state.status.values() if v=='na')} — Sin responder: {sum(1 for v in st.session_state.status.values() if v=='none')}")

# -----------------------------
# PREPARAR DataFrame para PDF (sin columna 'Qué verificar')
# -----------------------------
df = pd.DataFrame([{
    "Ítem": item[0],
    "Estado": ("Cumple" if st.session_state.status[item[0]] == "yes" else
               "No cumple" if st.session_state.status[item[0]] == "no" else
               "No aplica" if st.session_state.status[item[0]] == "na" else "Sin responder"),
    "Recomendación": item[2],
    "Referencia": item[3],
    "Observación": st.session_state.note[item[0]]
} for item in CHECK_ITEMS])

# -----------------------------
# FUNCIONES: ajuste de observación y generar PDF
# -----------------------------
def split_observation_text(text, chunk=100):
    """Divide texto largo en líneas de máximo `chunk` caracteres sin sangría, retorna string con '\n'."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= chunk:
        return text
    parts = [text[i:i+chunk] for i in range(0, len(text), chunk)]
    return "\n".join(parts)

def generar_pdf(df, producto, proveedor, responsable, porcentaje, nombre_archivo):
    buffer = BytesIO()
    # márgenes reducidos a 8 mm para más espacio
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=8*mm, rightMargin=8*mm, topMargin=8*mm, bottomMargin=8*mm)

    styles = getSampleStyleSheet()
    style_header = ParagraphStyle("header", parent=styles["Normal"], fontSize=8, leading=10)
    style_cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=7.5, leading=9)

    story = []
    # header
    story.append(Paragraph("<b>Informe de verificación de etiquetado nutricional — Juan Valdez</b>", style_header))
    story.append(Spacer(1, 3*mm))
    fecha = datetime.now().strftime("%Y-%m-%d")
    story.append(Paragraph(f"<b>Fecha:</b> {fecha} &nbsp;&nbsp; <b>Producto:</b> {producto or '-'} &nbsp;&nbsp; "
                           f"<b>Proveedor:</b> {proveedor or '-'} &nbsp;&nbsp; <b>Responsable:</b> {responsable or '-'}",
                           style_header))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"<b>Cumplimiento:</b> {porcentaje} %", style_header))
    story.append(Spacer(1, 5*mm))

    # preparar datos de tabla (Paragraph para wrapping; Observación dividida manualmente)
    data = [["Ítem", "Estado", "Recomendación", "Referencia", "Observación"]]
    for _, r in df.iterrows():
        obs = r["Observación"] or "-"
        # dividir observación en saltos reales de línea para evitar desbordes
        obs = split_observation_text(obs, chunk=100) if obs != "-" else obs

        data.append([
            Paragraph(str(r["Ítem"]), style_cell),
            Paragraph(str(r["Estado"]), style_cell),
            Paragraph(str(r["Recomendación"]), style_cell),
            Paragraph(str(r["Referencia"]), style_cell),
            Paragraph(obs, style_cell)
        ])

    # ancho máximo calculado para A4 landscape con márgenes 8 mm (ancho útil ≈ 297mm - 16mm = 281mm)
    # Col widths sum aproximado: 70 + 25 + 100 + 45 + 40 = 280 mm (ajustado)
    col_widths = [70*mm, 25*mm, 100*mm, 45*mm, 40*mm]  # todos en mm
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

# -----------------------------
# BOTÓN ÚNICO: Generar PDF
# -----------------------------
st.subheader("Generar informe PDF")
if st.button("Generar PDF"):
    pdf_buffer = generar_pdf(df, producto, proveedor, responsable, porcentaje, nombre_pdf)
    suggested_name = (nombre_pdf.strip() or f"informe_{datetime.now().strftime('%Y%m%d')}") + ".pdf"
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=suggested_name, mime="application/pdf")
