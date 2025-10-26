# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import textwrap

# ReportLab (platypus) for nicer table/report layout
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="Verificador Rotulado (5109+810+2492)", layout="wide")
st.title("Verificador de Etiquetado — Resoluciones 5109, 810 y 2492")
st.markdown(
    "Aplicación interactiva para verificar el cumplimiento del etiquetado de alimentos.\n\n"
    "Use los botones ✅ Cumple / ❌ No cumple / ⚪ No aplica. Si marca **No cumple** aparecerá una "
    "recomendación normativa y acciones sugeridas."
)

# --------------------------
# Checklist data structure
# Each item: (section, label, what_to_check, recommendation, reference, severity, resolution)
# severity: 'crítico','medio','menor'
# resolution: '5109','810','2492' or combined
# --------------------------

CHECK_ITEMS = [
    # Section: Información general (5109)
    ("Información general", "Denominación del producto (denominación exacta)",
     "Verificar que la denominación describa el alimento según su naturaleza; no usar marcas engañosas.",
     "Modificar denominación para que refleje el tipo de alimento; revisar ingredientes principales.",
     "Resol. 5109 Art.4", "crítico", "5109"),

    ("Información general", "Lista de ingredientes en orden decreciente",
     "Comprobar que todos los ingredientes estén listados en español y en orden de peso.",
     "Agregar lista completa de ingredientes en la etiqueta; corregir orden si es necesario.",
     "Resol. 5109 Art.6", "crítico", "5109"),

    ("Información general", "Contenido neto declarado en unidades SI",
     "Revisar que el contenido neto esté en g, mL o L según corresponda y sea legible.",
     "Reimprimir etiqueta con unidad SI correcta y valor verificado en producción.",
     "Resol. 5109 Art.7", "crítico", "5109"),

    ("Información general", "Nombre o razón social y dirección del responsable",
     "Verificar que el fabricante/empacador/importador figura con dirección legible.",
     "Incluir datos completos del responsable en la etiqueta conforme a normativa.",
     "Resol. 5109 Art.8", "crítico", "5109"),

    ("Información general", "Lote y fecha de vencimiento (legibles)",
     "Confirmar existencia y formato legible (día/mes/año o formato exigido).",
     "Asegurar impresión de lote y fecha en área visible; corregir formato.",
     "Resol. 5109 Art.10-11", "crítico", "5109"),

    ("Información general", "Instrucciones de conservación y uso (si aplican)",
     "Verificar que las instrucciones necesarias para conservar/usar el producto estén presentes.",
     "Agregar indicaciones de conservación o preparación si faltan.",
     "Resol. 5109 Art.12", "medio", "5109"),

    # Section: Información nutricional (810 & 2492)
    ("Información nutricional", "Tabla de Información Nutricional presente y enmarcada",
     "Comprobar la presencia de la tabla en la etiqueta, dentro de un recuadro visible.",
     "Añadir la tabla de información nutricional en recuadro con líneas legibles.",
     "Resol. 810 Art.27", "crítico", "810"),

    ("Información nutricional", "Columnas: Por 100 g/mL y Por porción",
     "Verificar que existan ambas columnas y títulos exactos 'Por 100 g' o 'Por 100 mL' y 'Por porción'.",
     "Incluir ambas columnas y ajustar porciones declaradas correctamente.",
     "Resol. 810 Art.30", "crítico", "810"),

    ("Información nutricional", "Orden y presencia de nutrientes obligatorios",
     "Verifique presencia y orden: calorías, grasa total, grasa saturada, grasas trans, carbohidratos, fibra, azúcares, azúcares añadidos, proteína, sodio.",
     "Ajustar tabla para mostrar los nutrientes en el orden normativo y con unidades correctas.",
     "Resol. 810 Art.28-28.4", "crítico", "810"),

    ("Información nutricional", "Vitaminas y minerales (declaración y unidades)",
     "Si se declaran vitaminas/minerales, verificar orden, unidades (mg, µg, UI) y separación con línea.",
     "Corregir unidades y orden; separar micronutrientes con línea según resolución.",
     "Resol. 810 Art.28.3", "medio", "810"),

    ("Información nutricional", "Frase 'No es fuente significativa de...'(cuando aplique)",
     "Comprobar inclusión de la frase si hay nutrientes en cantidades no significativas.",
     "Agregar la frase dentro del recuadro según la norma si procede.",
     "Resol. 810 Art.27.1.2 & Tabla 9", "menor", "810"),

    ("Información nutricional", "Tipografía y contraste (Arial/Helvética, legible)",
     "Verificar que la tipografía sea legible, en color contrastante (negro sobre claro) y tamaños mínimos.",
     "Ajustar tipografía a Arial/Helvetica y tamaños mínimos establecidos.",
     "Resol. 810 Art.27.1.4 & 28.1", "crítico", "810"),

    # Section: Etiquetado frontal (810 & 2492) - visual checks included
    ("Etiquetado frontal", "Presencia de sellos frontales cuando aplican",
     "Comprobar que los sellos aparecen solo si los valores exceden los umbrales normativos.",
     "Calcular según valores declarados y añadir/retirar sellos conforme aplique.",
     "Resol. 810 Art. (sellos)", "crítico", "810/2492"),

    ("Etiquetado frontal", "Forma y color del sello (octógono negro, borde blanco)",
     "Verificar forma octogonal, fondo negro y texto en blanco; sin alteraciones cromáticas.",
     "Rediseñar sello para ajustarlo a las especificaciones visuales oficiales.",
     "Resol. 810 / 2492", "crítico", "810/2492"),

    ("Etiquetado frontal", "Tamaño del sello (proporción del área principal)",
     "Comprobar que el sello tenga la proporción mínima requerida (p.ej. >=10% del área principal cuando corresponde).",
     "Ajustar tamaño y posición para cumplir con la proporción mínima.",
     "Resol. 810 / 2492", "medio", "810/2492"),

    ("Etiquetado frontal", "Ubicación y espacio (parte superior derecha, sin obstrucciones)",
     "Verificar que el sello esté en la cara principal y en la posición correcta sin sobreposiciones.",
     "Reubicar sello en área superior derecha y asegurar visibilidad.",
     "Resol. 810 / 2492", "medio", "810/2492"),

    # Section: Claims, leyendas y alérgenos
    ("Claims y advertencias", "Declaración de alérgenos visible",
     "Comprobar 'Contiene: ...' o 'Puede contener trazas de ...' según ingredientes.",
     "Añadir leyenda de alérgenos con formato claro y visible.",
     "Resol. 5109 / 810", "crítico", "5109/810"),

    ("Claims y advertencias", "Advertencias específicas (edulcorantes, cafeína, etc.)",
     "Verificar si el producto lleva advertencias especiales y que estas estén presentes si corresponde.",
     "Incluir las advertencias en lugar visible conforme a normativa.",
     "Resol. 810", "medio", "810"),

    ("Claims y advertencias", "Claims nutricionales verificables",
     "Verificar que cualquier claim nutricional o saludable tenga evidencia y cumpla la normativa.",
     "Retirar claims no verificables o adjuntar evidencia y referencias.",
     "Resol. 333/2011 & 810", "crítico", "810"),

    # Section: Presentación / legibilidad
    ("Presentación y legibilidad", "Idioma español en información obligatoria",
     "Comprobar que toda la información obligatoria esté en español.",
     "Agregar rótulo complementario en español si la etiqueta original está en otro idioma.",
     "Resol. 5109 Art.18", "crítico", "5109"),

    ("Presentación y legibilidad", "Contraste y legibilidad (sin sobreimpresiones)",
     "Verificar que el texto sea legible, sin superposición y con contraste suficiente.",
     "Modificar color/posición para mejorar contraste y legibilidad.",
     "Resol. 5109 / 810", "medio", "5109/810"),

    ("Presentación y legibilidad", "Etiqueta complementaria para importados",
     "Comprobar que existe etiqueta complementaria cuando el empaque original está en otro idioma.",
     "Agregar etiqueta complementaria cumpliendo requisitos nacionales.",
     "Resol. 5109 (parágrafo)", "menor", "5109"),
]

# --------------------------
# Session state init
# --------------------------
def init_state():
    if "status" not in st.session_state:
        st.session_state.status = {}  # key -> 'yes'/'no'/'na'/'none'
    if "note" not in st.session_state:
        st.session_state.note = {}
    if "init_done" not in st.session_state:
        for sec, label, what, rec, ref, sev, res in CHECK_ITEMS:
            key = f"{sec}||{label}"
            st.session_state.status.setdefault(key, "none")
            st.session_state.note.setdefault(key, "")
        st.session_state.init_done = True

init_state()

# --------------------------
# Header input: product info
# --------------------------
st.sidebar.header("Datos de la verificación")
product_name = st.sidebar.text_input("Nombre del producto", "")
provider = st.sidebar.text_input("Proveedor / Fabricante", "")
responsible = st.sidebar.text_input("Responsable de la verificación", "")
file_name_input = st.sidebar.text_input("Nombre archivo PDF (sin .pdf)", f"informe_{datetime.now().strftime('%Y%m%d')}")
start_eval = st.sidebar.button("Iniciar / Actualizar evaluación")

st.sidebar.markdown("---")
st.sidebar.markdown("Filtros:")
filter_no = st.sidebar.checkbox("Mostrar sólo No cumple", value=False)
st.sidebar.markdown(" ")

# --------------------------
# Helper functions
# --------------------------
def key_for(sec, label):
    return f"{sec}||{label}"

def set_status(key, val):
    st.session_state.status[key] = val

# --------------------------
# Main UI: Checklist
# --------------------------
st.header("Checklist consolidado — 5109, 810, 2492")
st.markdown("Responda cada criterio. Si marca **No cumple**, verá una recomendación normativa inmediata.")

col_left, col_right = st.columns([3, 1])

with col_left:
    # iterate sections showing expanders grouped by section
    current_section = None
    for sec, label, what, rec, ref, sev, res in CHECK_ITEMS:
        key = key_for(sec, label)
        # group behavior: show expander once per section
        if sec != current_section:
            if current_section is not None:
                st.write("")  # spacer
            current_section = sec
            exp = st.expander(f"{sec}", expanded=True)
        # create UI inside expander (we must use the last created exp variable)
        with exp:
            if filter_no and st.session_state.status.get(key) != "no":
                # skip rendering this item if filtering No cumple
                continue

            st.subheader(label)
            st.markdown(f"**Qué verificar:** {what}")
            st.markdown(f"**Referencia:** {ref} • **Severidad:** {sev.capitalize()} • **Resolución:** {res}")
            # status buttons (semáforo) arranged inline
            cols = st.columns([0.12, 0.12, 0.12, 0.64])
            if cols[0].button("✅ Cumple", key=f"{key}_yes"):
                set_status(key, "yes")
            if cols[1].button("❌ No cumple", key=f"{key}_no"):
                set_status(key, "no")
            if cols[2].button("⚪ No aplica", key=f"{key}_na"):
                set_status(key, "na")

            # status badge
            status = st.session_state.status.get(key, "none")
            if status == "yes":
                st.markdown("<div style='background:#e6ffed;color:#014d14;padding:6px;border-radius:6px'>✅ Cumple</div>", unsafe_allow_html=True)
            elif status == "no":
                st.markdown("<div style='background:#ffe6e6;color:#8b0000;padding:6px;border-radius:6px'>❌ No cumple</div>", unsafe_allow_html=True)
                # show recommendation when No cumple
                st.markdown(f"<div style='border-left:5px solid #d62828; background:#fff0f0;padding:8px;border-radius:4px'><strong>Acción recomendada:</strong> {rec} <br><em style='color:#555'>Referencia: {ref}</em></div>", unsafe_allow_html=True)
            elif status == "na":
                st.markdown("<div style='background:#f2f2f2;color:#333;padding:6px;border-radius:6px'>⚪ No aplica</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='background:#fff;color:#333;padding:6px;border-radius:6px'>Sin responder</div>", unsafe_allow_html=True)

            # observation/note
            note_key = key + "||note"
            note_val = st.text_area("Observación (opcional)", value=st.session_state.note.get(note_key, ""), key=f"{note_key}")
            st.session_state.note[note_key] = note_val

            st.markdown("---")

with col_right:
    st.subheader("Resumen")
    # compute statistics per resolution
    df_rows = []
    total = 0
    counts = {"yes": 0, "no": 0, "na": 0, "none": 0}
    per_resolution = {}
    for sec, label, what, rec, ref, sev, res in CHECK_ITEMS:
        key = key_for(sec, label)
        status = st.session_state.status.get(key, "none")
        counts[status] = counts.get(status, 0) + 1
        total += 1
        per_resolution.setdefault(res, {"total": 0, "yes": 0, "no": 0, "na": 0})
        per_resolution[res]["total"] += 1
        per_resolution[res][status] = per_resolution[res].get(status, 0) + 1
        df_rows.append({
            "Sección": sec,
            "Ítem": label,
            "Estado": status,
            "Recomendación": rec,
            "Referencia": ref,
            "Severidad": sev,
            "Resolución": res,
            "Observación": st.session_state.note.get(key + "||note", "")
        })

    applicable = total - per_resolution.get("none", {}).get("na", 0)  # approx: total minus nas (not perfect per-res)
    # better: compute percent as yes / (total - na)
    total_na = counts.get("na", 0)
    denom = total - total_na
    percent = int(round((counts.get("yes", 0) / denom * 100) if denom > 0 else 0))

    st.metric("Cumplimiento total", f"{percent} %")
    st.write(f"Ítems totales: **{total}**")
    st.write(f"Cumple: **{counts['yes']}** — No cumple: **{counts['no']}** — No aplica: **{counts['na']}** — Sin responder: **{counts['none']}**")

    st.markdown("---")
    st.subheader("Cumplimiento por Resolución")
    for res_key, vals in per_resolution.items():
        total_res = vals.get("total", 0)
        yes_res = vals.get("yes", 0)
        na_res = vals.get("na", 0)
        denom_res = total_res - na_res
        pct_res = int(round((yes_res / denom_res * 100) if denom_res > 0 else 0))
        st.write(f"- {res_key}: {pct_res} % ({yes_res}/{denom_res} aplicables)")

    st.markdown("---")
    if counts["no"] > 0:
        st.error(f"Hay {counts['no']} no conformidades. Revise las recomendaciones marcadas en rojo.")
    else:
        st.success("No hay no conformidades registradas.")

    if st.button("Marcar todo como 'No aplica'"):
        for sec, label, what, rec, ref, sev, res in CHECK_ITEMS:
            set_status(key_for(sec, label), "na")
        st.experimental_rerun()

    if st.button("Resetear todo"):
        for sec, label, what, rec, ref, sev, res in CHECK_ITEMS:
            set_status(key_for(sec, label), "none")
            st.session_state.note[key_for(sec, label) + "||note"] = ""
        st.experimental_rerun()

# --------------------------
# Build results DataFrame
# --------------------------
def build_results_df():
    df = pd.DataFrame(df_rows)
    # humanize Estado
    def map_state(s):
        return "Cumple" if s == "yes" else ("No cumple" if s == "no" else ("No aplica" if s == "na" else "Sin responder"))
    df["Estado"] = df["Estado"].apply(map_state)
    return df

results_df = build_results_df()

st.markdown("---")
st.subheader("Tabla completa de resultados")
st.dataframe(results_df, use_container_width=True)

# --------------------------
# PDF generation (estilo empresarial)
# --------------------------
def generar_pdf(df: pd.DataFrame, percent_total: int, product_name: str, provider: str, responsible: str, filename: str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    styleH = styles["Heading1"]
    styleN = styles["Normal"]
    style_small = ParagraphStyle("small", parent=styleN, fontSize=8, leading=10)
    style_bold = ParagraphStyle("bold", parent=styleN, fontSize=10, leading=12, spaceAfter=6)
    story = []

    # Header: Title (Juan Valdez), date and optional logo placeholder
    title = "Informe de verificación de etiquetado nutricional — Juan Valdez"
    story.append(Paragraph(title, ParagraphStyle("title", parent=styleH, fontSize=14, leading=16)))
    story.append(Spacer(1, 4*mm))
    meta = f"<b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;&nbsp;&nbsp; <b>Producto:</b> {product_name or '-'} &nbsp;&nbsp;&nbsp; <b>Proveedor:</b> {provider or '-'} &nbsp;&nbsp;&nbsp; <b>Responsable:</b> {responsible or '-'}"
    story.append(Paragraph(meta, style_small))
    story.append(Spacer(1, 4*mm))

    # Summary box
    summary_text = f"<b>Cumplimiento total:</b> {percent_total} %"
    story.append(Paragraph(summary_text, style_bold))
    story.append(Spacer(1, 4*mm))

    # Table header and data
    table_data = []
    header = ["Sección", "Ítem", "Estado", "Qué verificar", "Recomendación", "Referencia", "Severidad"]
    table_data.append(header)
    for idx, row in df.iterrows():
        table_data.append([
            str(row["Sección"]),
            str(row["Ítem"]),
            str(row["Estado"]),
            str(row["Qué verificar"]) if "Qué verificar" in row.index else "",  # fallback
            str(row["Recomendación"]),
            str(row["Referencia"]),
            str(row["Severidad"]).capitalize()
        ])

    # Try to use columns narrower for aesthetics
    col_widths = [40*mm, 50*mm, 20*mm, 55*mm, 60*mm, 30*mm, 20*mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl_style = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ])
    t.setStyle(tbl_style)
    story.append(t)
    story.append(Spacer(1, 6*mm))

    # Add a final observations block
    # collect major nonconformities
    no_df = df[df["Estado"] == "No cumple"]
    if not no_df.empty:
        story.append(Paragraph("<b>No conformidades detectadas (resumen):</b>", style_bold))
        for idx, r in no_df.iterrows():
            text = f"- [{r['Severidad'].capitalize()}] {r['Ítem']} ({r['Sección']}): {r['Recomendación']}"
            story.append(Paragraph(text, style_small))
            story.append(Spacer(1, 1*mm))
    else:
        story.append(Paragraph("<b>No se detectaron no conformidades críticas.</b>", style_small))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Observaciones generales:", style_bold))
    story.append(Paragraph(" " , style_small))
    # Footer: signature placeholder
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph(f"Responsable de la verificación: {responsible or ' - '}", style_small))
    doc.build(story)

    buffer.seek(0)
    return buffer

# --------------------------
# Generate PDF button
# --------------------------
st.markdown("---")
st.subheader("Generar informe PDF (estilo empresarial)")
custom_fname = st.text_input("Nombre de archivo (sin .pdf)", value=file_name_input)
if st.button("Generar informe PDF"):
    # insert 'Qué verificar' column into df for PDF (we have it in CHECK_ITEMS mapping)
    pdf_df = results_df.copy()
    # Add Qué verificar column mapping from CHECK_ITEMS
    qmap = {}
    for sec, label, what, rec, ref, sev, res in CHECK_ITEMS:
        qmap[(sec, label)] = what
    pdf_df["Qué verificar"] = pdf_df.apply(lambda r: qmap.get((r["Sección"], r["Ítem"]), ""), axis=1)
    # Generate pdf bytes
    pdf_buffer = generar_pdf(pdf_df, percent, product_name, provider, responsible, custom_fname)
    suggested_name = (custom_fname.strip() or f"informe_{datetime.now().strftime('%Y%m%d')}") + ".pdf"
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=suggested_name, mime="application/pdf")
    st.success("Informe generado. Haz clic en 'Descargar PDF' para guardarlo en tu equipo.")
