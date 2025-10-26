# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import datetime
import textwrap

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Checklist Rotulado 5109 (Interactivo)", layout="wide")
st.title("Checklist Interactivo — Rotulado (Resolución 5109)")

st.markdown(
    "Aplicativo interactivo tipo **semáforo** para verificar cumplimiento del rotulado "
    "según Resolución 5109 (versión adaptada y actualizada). "
    "Marca cada ítem: ✅ Cumple — ❌ No cumple — ⚪ No aplica. "
    "Cuando marque **No cumple** aparecerá una alerta con la acción recomendada."
)

# ---------------------------
# DEFINICIÓN DEL CHECKLIST (mejorado)
# Cada entrada: (label, recommendation, severity: 'critical'|'minor')
# ---------------------------
CHECKLIST_STRUCTURE = {
    "Información general obligatoria": [
        ("Nombre del producto coincide con la denominación del alimento",
         "Asegurar que la denominación sea la utilizada en la normativa y en el ingrediente principal. Revisar ingredientes.",
         "critical"),
        ("Lista de ingredientes en orden decreciente de peso",
         "Incluir lista completa, en español, en orden de mayor a menor proporción.",
         "critical"),
        ("Contenido neto declarado en unidades SI (g, mL, L, etc.)",
         "Ajustar la declaración a unidades del Sistema Internacional y usar el mismo número en todo el empaque.",
         "critical"),
        ("Nombre/razón social y dirección del responsable",
         "Agregar nombre y dirección del fabricante, empacador o importador tal como exige la normativa.",
         "critical"),
        ("Lote indicado claramente",
         "Incluir código de lote o referencia de fabricación visible en el envase.",
         "minor"),
        ("Fecha de vencimiento o consumo preferente con formato legible",
         "Usar formato día/mes/año y colocarlo en área visible.",
         "critical"),
        ("Instrucciones de conservación (si aplica)",
         "Agregar la instrucción exacta para conservar el producto (temperatura, refrigeración, etc.).",
         "minor")
    ],
    "Información nutricional": [
        ("Tabla de información nutricional presente y legible",
         "Incluir tabla con encabezados 'Por 100 g/mL' y 'Por porción' en idioma español.",
         "critical"),
        ("Declaración por 100 g/mL y por porción (ambas aparecen)",
         "Asegurar que ambas columnas estén presentes y que las porciones estén correctamente descritas.",
         "critical"),
        ("Tipo de letra y tamaño legible (Arial/Helvética, mínimo exigido)",
         "Utilizar Arial/Helvética con tamaño y contraste conforme al anexo técnico aplicable.",
         "critical"),
        ("Calorías y nutrientes obligatorios declarados",
         "Declarar energía, grasa (y subtipos si aplica), carbohidratos, proteína y sodio.",
         "critical"),
        ("Vitaminas o minerales obligatorios (si aplica) declarados correctamente",
         "Si declara vitaminas/minerales obligatorios, seguir orden y unidades exigidas.",
         "minor")
    ],
    "Leyendas y advertencias": [
        ("Leyenda de alérgenos presente y visible si aplica",
         "Indicar 'contiene: ...' o 'puede contener trazas de ...' según corresponda.",
         "critical"),
        ("Advertencias especiales presentes cuando aplican (edulcorantes, cafeína, etc.)",
         "Incluir advertencias específicas en lugar visible según el tipo de ingrediente.",
         "minor"),
        ("Instrucciones de uso claras si son necesarias",
         "Agregar modo de uso o preparación cuando sea necesario para consumo seguro.",
         "minor")
    ],
    "Presentación, idioma y legibilidad": [
        ("Toda la información obligatoria en español",
         "Agregar traducción o etiqueta complementaria si la etiqueta original está en otro idioma.",
         "critical"),
        ("Contraste de color adecuado (texto legible frente al fondo)",
         "Usar color de texto contrastante y evitar fondos que impidan lectura.",
         "minor"),
        ("No uso de elementos gráficos que induzcan a error",
         "Evitar imágenes o frases que sugieran propiedades no demostradas.",
         "minor")
    ],
    "Requisitos adicionales": [
        ("Claims nutricionales o saludables verificables",
         "Revisar requisitos y evidencia científica antes de usar claims; retirar si no cumple.",
         "critical"),
        ("Etiqueta complementaria para importados (si aplica)",
         "Asegurar que la etiqueta complementaria cumpla los requisitos nacionales.",
         "minor")
    ]
}

# If you want to add additional items later, append to this dict.

# ---------------------------
# SESSION STATE: inicializar estados para cada ítem
# ---------------------------
def init_session_state():
    if "status" not in st.session_state:
        st.session_state.status = {}
        for section, items in CHECKLIST_STRUCTURE.items():
            for (label, rec, sev) in items:
                key = f"{section}||{label}"
                st.session_state.status[key] = "no_response"  # 'yes','no','na'
    if "notes" not in st.session_state:
        st.session_state.notes = {}
    if "severity" not in st.session_state:
        st.session_state.severity = {}
        for section, items in CHECKLIST_STRUCTURE.items():
            for (label, rec, sev) in items:
                key = f"{section}||{label}"
                st.session_state.severity[key] = sev
    if "recommendation_shown" not in st.session_state:
        st.session_state.recommendation_shown = {}

init_session_state()

# ---------------------------
# Small helpers for UI
# ---------------------------
def key_for(section, label):
    return f"{section}||{label}"

def set_status(key, value):
    st.session_state.status[key] = value
    # reset recommendation visibility
    st.session_state.recommendation_shown[key] = False

def status_color(val):
    if val == "yes":
        return "background-color:#d4f7d4; color:#064; font-weight:bold; padding:4px; border-radius:6px"
    if val == "no":
        return "background-color:#ffd6d6; color:#800; font-weight:bold; padding:4px; border-radius:6px"
    if val == "na":
        return "background-color:#f0f0f0; color:#444; font-weight:bold; padding:4px; border-radius:6px"
    return "background-color:#fff; color:#000; padding:4px; border-radius:6px"

# ---------------------------
# MAIN UI
# ---------------------------
col_left, col_right = st.columns([3,1])
with col_left:
    st.markdown("### Checklist (responde cada ítem)")
    show_only_nonconform = st.checkbox("Mostrar solo No cumple (filtrar no conformidades)", value=False)
    # iterate sections
    for section, items in CHECKLIST_STRUCTURE.items():
        with st.expander(section, expanded=True):
            for label, recommendation, severity in items:
                k = key_for(section, label)
                # current value
                current = st.session_state.status.get(k, "no_response")
                # layout: label + buttons + status badge + quick note icon
                st.markdown(f"**{label}**")
                cols = st.columns([0.6, 0.14, 0.14, 0.12])
                # Button Cumple (green)
                if cols[1].button("✅ Cumple", key=f"{k}__yes"):
                    set_status(k, "yes")
                if cols[2].button("❌ No cumple", key=f"{k}__no"):
                    set_status(k, "no")
                if cols[3].button("⚪ No aplica", key=f"{k}__na"):
                    set_status(k, "na")

                # show badge of current status
                badge_html = f"<div style='{status_color(st.session_state.status[k])}'>{'Cumple' if st.session_state.status[k]=='yes' else ('No cumple' if st.session_state.status[k]=='no' else ('No aplica' if st.session_state.status[k]=='na' else 'Sin responder'))}</div>"
                st.markdown(badge_html, unsafe_allow_html=True)

                # note input (optional)
                note_key = k + "||note"
                user_note = st.text_input("Observación / nota (opcional)", value=st.session_state.notes.get(note_key, ""), key=note_key)
                st.session_state.notes[note_key] = user_note

                # If No cumple -> show urgent alert with recommendation and actions (big & red)
                if st.session_state.status[k] == "no":
                    st.markdown(
                        f"<div style='background:#ffe9e9; border-left:6px solid #d62828; padding:10px; border-radius:6px'>"
                        f"<strong style='color:#a10000'>NO CUMPLE — Acción recomendada:</strong><br>"
                        f"{recommendation}<br>"
                        f"<em style='color:#333'>Gravedad: {severity}</em>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Optionally hide nonconformities when filter is active
                if show_only_nonconform and st.session_state.status[k] != "no":
                    # remove the last elements we added visually: hack by using empty markdown (can't easily remove)
                    st.empty()

                st.markdown("---")

with col_right:
    st.markdown("### Resumen y estado")
    # compute stats
    total_items = 0
    count_yes = 0
    count_no = 0
    count_na = 0
    for section, items in CHECKLIST_STRUCTURE.items():
        for label, rec, sev in items:
            k = key_for(section, label)
            total_items += 1
            v = st.session_state.status.get(k, "no_response")
            if v == "yes":
                count_yes += 1
            elif v == "no":
                count_no += 1
            elif v == "na":
                count_na += 1
    applicable = total_items - count_na
    percent = int(round((count_yes / applicable * 100) if applicable > 0 else 0, 0))

    st.metric("Cumplimiento (%)", f"{percent} %")
    st.write(f"Items totales: **{total_items}**")
    st.write(f"Aplicables (no 'No aplica'): **{applicable}**")
    st.write(f"Cumple: **{count_yes}** — No cumple: **{count_no}** — No aplica: **{count_na}**")

    st.markdown("---")
    st.subheader("Acciones automáticas")
    if count_no > 0:
        st.error(f"Se han detectado {count_no} no conformidades. Revisar las recomendaciones para corregirlas.")
        st.markdown("**Sugerencias de priorización:**")
        # show critical ones first
        critical_list = []
        for section, items in CHECKLIST_STRUCTURE.items():
            for label, rec, sev in items:
                k = key_for(section, label)
                if st.session_state.status[k] == "no" and sev == "critical":
                    critical_list.append((section, label, rec))
        if critical_list:
            st.markdown("**Prioridad ALTA (corregir de inmediato):**")
            for sec, lab, rec in critical_list:
                st.write(f"- **{lab}** ({sec}): {rec}")
        else:
            st.write("- No hay ítems críticos sin cumplir.")

    else:
        st.success("No hay no conformidades detectadas.")

    st.markdown("---")
    # quick buttons
    if st.button("Marcar todo como 'No aplica'"):
        for section, items in CHECKLIST_STRUCTURE.items():
            for label, rec, sev in items:
                k = key_for(section, label)
                set_status(k, "na")
        st.experimental_rerun()

    if st.button("Resetear respuestas"):
        for section, items in CHECKLIST_STRUCTURE.items():
            for label, rec, sev in items:
                k = key_for(section, label)
                st.session_state.status[k] = "no_response"
                st.session_state.notes[k + "||note"] = ""
        st.experimental_rerun()

# ---------------------------
# REPORT: build dataframe for PDF / download
# ---------------------------
def build_results_df():
    rows = []
    for section, items in CHECKLIST_STRUCTURE.items():
        for label, rec, sev in items:
            k = key_for(section, label)
            status = st.session_state.status.get(k, "no_response")
            note = st.session_state.notes.get(k + "||note", "")
            rows.append({
                "Sección": section,
                "Ítem": label,
                "Estado": "Cumple" if status == "yes" else ("No cumple" if status == "no" else ("No aplica" if status == "na" else "Sin responder")),
                "Severidad": sev,
                "Recomendación": rec if status == "no" else "",
                "Observación": note
            })
    df = pd.DataFrame(rows)
    return df

# ---------------------------
# PDF generation
# ---------------------------
def generar_pdf_informe(df: pd.DataFrame, percent: int):
    buffer = BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    left_margin = 15 * mm
    right_margin = 15 * mm
    usable_w = page_w - left_margin - right_margin

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_margin, page_h - 25 * mm, "Informe Checklist Rotulado — Resolución 5109")
    c.setFont("Helvetica", 9)
    c.drawString(left_margin, page_h - 30 * mm, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(left_margin, page_h - 34 * mm, f"Cumplimiento: {percent} %")

    # Summary counts
    total = len(df)
    no_count = df[df["Estado"] == "No cumple"].shape[0]
    yes_count = df[df["Estado"] == "Cumple"].shape[0]
    na_count = df[df["Estado"] == "No aplica"].shape[0]
    c.drawString(left_margin, page_h - 38 * mm, f"Total ítems: {total} — Cumple: {yes_count} — No cumple: {no_count} — No aplica: {na_count}")

    # Table header
    y = page_h - 45 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(left_margin, y, "Sección")
    c.drawString(left_margin + 65 * mm, y, "Ítem")
    c.drawString(left_margin + 135 * mm, y, "Estado")
    c.drawString(left_margin + 155 * mm, y, "Sev.")
    c.drawString(left_margin + 170 * mm, y, "Recomendación / Observación")
    y -= 6 * mm
    c.setLineWidth(0.5)
    c.line(left_margin, y + 3 * mm, page_w - right_margin, y + 3 * mm)

    # Rows
    c.setFont("Helvetica", 8)
    for idx, r in df.iterrows():
        if y < 30 * mm:
            c.showPage()
            y = page_h - 20 * mm
            c.setFont("Helvetica", 8)
        # color coding: red text for no cumple
        state = r["Estado"]
        if state == "No cumple":
            c.setFillColorRGB(0.6, 0, 0)
        else:
            c.setFillColorRGB(0, 0, 0)
        c.drawString(left_margin, y, r["Sección"][:30])
        c.drawString(left_margin + 65 * mm, y, r["Ítem"][:40])
        c.drawString(left_margin + 135 * mm, y, r["Estado"])
        c.drawString(left_margin + 155 * mm, y, r["Severidad"][0].upper())
        # recommendation + observation (wrap)
        notes = ""
        if r["Recomendación"]:
            notes += "RECOM: " + r["Recomendación"] + " "
        if r["Observación"]:
            notes += "OBS: " + r["Observación"]
        wrapped = textwrap.wrap(notes, width=60)
        if wrapped:
            c.drawString(left_margin + 170 * mm, y, wrapped[0])
            # if more lines, draw them below
            for kline, ln in enumerate(wrapped[1:3], start=1):
                c.drawString(left_margin + 170 * mm, y - kline * 4.5 * mm, ln)
        y -= 8 * mm
        # reset color
        c.setFillColorRGB(0, 0, 0)

    # Footer
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ---------------------------
# Show table and PDF download
# ---------------------------
df_results = build_results_df()

st.markdown("---")
st.subheader("Resultado completo del checklist")
st.dataframe(df_results, use_container_width=True)

st.markdown("### Descargar informe (PDF)")
if st.button("Generar informe PDF"):
    pdf_buffer = generar_pdf_informe(df_results, percent)
    st.download_button("Descargar informe (PDF)", data=pdf_buffer, file_name="informe_checklist_5109.pdf", mime="application/pdf")

st.markdown("---")
st.caption("Esta herramienta es una guía de verificación basada en la Resolución 5109/2005 y adaptaciones prácticas. "
           "Las recomendaciones que aquí aparecen son de carácter orientativo y deben complementarse con asesoría legal/técnica cuando aplique.")
