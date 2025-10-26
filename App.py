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
# ESTRUCTURA DE ÍTEMS AGRUPADOS POR CATEGORÍA
# -----------------------------------------------------------
CATEGORIAS = {
    "1. Identificación general del producto": [
        ("Nombre del alimento",
         "Verificar que indique la verdadera naturaleza del producto; usar nombre específico, no genérico.",
         "Debe indicar la verdadera naturaleza del producto.",
         "Art. 5.1 Resol. 5109/2005"),

        ("Marca comercial",
         "Confirmar que la marca no sustituya el nombre del alimento.",
         "Puede incluirse, pero no reemplaza el nombre del alimento.",
         "Art. 5.1.2 Resol. 5109/2005"),

        ("Lista de ingredientes",
         "Comprobar que todos los ingredientes estén listados en orden decreciente de peso al momento de fabricación.",
         "Agregar lista completa y verificar el orden correcto.",
         "Art. 5.2 Resol. 5109/2005"),

        ("Aditivos alimentarios",
         "Verificar que se declaren por su nombre común o categoría funcional (colorante, conservante, etc.).",
         "Declarar correctamente los aditivos alimentarios.",
         "Art. 5.2.1 Resol. 5109/2005"),

        ("Contenido neto",
         "Verificar que esté declarado en unidades del Sistema Internacional y sin incluir el envase.",
         "Declarar contenido neto en g, kg, mL o L.",
         "Art. 3 y Anexo Resol. 5109/2005"),

        ("Lote",
         "Revisar que exista número o código de lote visible e indeleble.",
         "Agregar o mejorar visibilidad del lote.",
         "Art. 5.4 Resol. 5109/2005"),

        ("Fecha de vencimiento o duración mínima",
         "Verificar formato, legibilidad y ubicación correcta.",
         "Usar formato legible y visible (día/mes/año).",
         "Art. 5.5 Resol. 5109/2005"),

        ("País de origen",
         "Comprobar que se declare 'Hecho en...' o 'Producto de...'.",
         "Incluir país de origen claramente.",
         "Art. 5.9 Resol. 5109/2005"),

        ("Nombre y dirección del fabricante/importador",
         "Revisar que la etiqueta contenga estos datos completos.",
         "Incluir nombre y dirección completos.",
         "Art. 5.8 Resol. 5109/2005"),
    ],

    "2. Cumplimiento de requisitos gráficos y sanitarios": [
        ("Legibilidad",
         "Asegurar que la información sea visible, indeleble y contrastante con el fondo.",
         "Mejorar contraste o tamaño del texto.",
         "Art. 4 y 6 Resol. 5109/2005"),

        ("Idioma",
         "Verificar que toda la información esté en español.",
         "Agregar traducción completa en español si aplica.",
         "Art. 5 Resol. 5109/2005"),

        ("Ubicación del rótulo",
         "Revisar que la etiqueta esté en la cara principal visible.",
         "Reubicar etiqueta si no es visible para el consumidor.",
         "Art. 3 y 5 Resol. 5109/2005"),

        ("Prohibición de inducir a error",
         "Verificar que no existan afirmaciones falsas o que atribuyan propiedades medicinales.",
         "Corregir mensajes que puedan inducir a error.",
         "Art. 4 Resol. 5109/2005"),
    ],

    "3. Etiquetado nutricional (Información nutricional obligatoria)": [
        ("Tabla nutricional presente",
         "Confirmar que esté incluida en la etiqueta.",
         "Incluir tabla con todos los nutrientes requeridos.",
         "Art. 8, 9 y 10 Resol. 810/2021"),

        ("Unidad de medida",
         "Verificar que los valores estén expresados por 100 g/mL y por porción.",
         "Corregir las unidades según corresponda.",
         "Art. 12 Resol. 810/2021"),

        ("Porciones por envase",
         "Verificar número de porciones por envase.",
         "Agregar número de porciones si aplica.",
         "Art. 12 y Par. 2 Art. 2 Resol. 810 modif. 2492/2022"),

        ("Nutrientes adicionales",
         "Verificar inclusión mínima y máxima permitida de vitaminas y minerales.",
         "Ajustar declaración de micronutrientes según límites.",
         "Art. 15 Resol. 810/2021"),

        ("Tolerancias analíticas",
         "Comprobar que las diferencias no superen ±20%.",
         "Ajustar declaraciones según análisis.",
         "Art. 14 Resol. 810/2021"),

        ("Fuente de nutrientes",
         "Verificar que cumpla con valores mínimos para usar términos como 'fuente de...'.",
         "Corregir o retirar declaraciones si no cumple.",
         "Art. 16 Resol. 810 modif. 2492/2022"),
    ],

    "4. Declaraciones nutricionales y de salud (voluntarias)": [
        ("Declaraciones nutricionales",
         "Comprobar que cumplan el perfil de nutrientes y no tengan sellos de advertencia.",
         "Retirar declaraciones que no cumplan con los criterios.",
         "Art. 25.4 Resol. 810 modif. 2492/2022"),

        ("Declaraciones de salud",
         "Verificar que estén autorizadas y con sustento científico.",
         "Incluir solo declaraciones aprobadas por el Ministerio.",
         "Art. 25 Resol. 810/2021"),

        ("Prohibición de declaraciones engañosas",
         "Revisar que no induzcan a error sobre beneficios del producto.",
         "Eliminar declaraciones confusas o engañosas.",
         "Art. 25.5 Resol. 810/2021"),
    ],

    "5. Etiquetado frontal de advertencia (Sellos negros)": [
        ("Aplicabilidad",
         "Verificar si aplica por exceso de azúcares, grasas saturadas, sodio o edulcorantes.",
         "Evaluar composición para determinar necesidad de sellos.",
         "Art. 32 Resol. 810 modif. 2492/2022"),

        ("Forma y color",
         "Revisar que el sello sea octagonal negro con borde blanco y texto 'EXCESO EN'.",
         "Corregir forma o color según especificación oficial.",
         "Art. 32 Resol. 2492/2022"),

        ("Ubicación",
         "Comprobar que esté en el tercio superior del panel principal.",
         "Reubicar sello si no cumple posición.",
         "Art. 32 Resol. 2492/2022"),

        ("Tamaño del sello",
         "Verificar proporción con el área del envase según tabla 17.",
         "Ajustar tamaño del sello según tabla normativa.",
         "Art. 32 Resol. 810 modif. 2492/2022"),

        ("Tipografía",
         "Verificar uso de fuente Arial Black, texto blanco sobre fondo negro.",
         "Corregir tipografía o contraste del sello.",
         "Art. 32 Resol. 810/2021"),

        ("Límite de nutrientes críticos",
         "Evaluar si cumple los límites OPS: azúcares ≥10% kcal, grasas sat. ≥10% kcal, sodio ≥1 mg/kcal.",
         "Revisar composición nutricional frente a límites establecidos.",
         "Tabla 17 Resol. 810 modif. 2492/2022"),

        ("Sello 'Contiene edulcorante'",
         "Verificar presencia del sello si contiene edulcorantes.",
         "Agregar sello correspondiente si aplica.",
         "Art. 32 Resol. 2492/2022"),

        ("Excepciones al sello",
         "Verificar si el producto pertenece a excepciones (no procesados, típicos, infantiles, etc.).",
         "Aplicar excepción cuando corresponda.",
         "Art. 2 Resol. 810 modif. 2492/2022"),
    ],

    "6. Requisitos especiales": [
        ("Carne cruda con condimentos",
         "Verificar contenido de sodio y sello correspondiente si excede el límite.",
         "Incluir sello frontal si aplica.",
         "Par. 1 Art. 2 Resol. 810 modif. 2492/2022"),

        ("Productos a granel",
         "Confirmar exención de etiquetado nutricional y frontal.",
         "Registrar exención si aplica.",
         "Art. 2 Resol. 810 modif. 2492/2022"),

        ("Materias primas industriales",
         "Confirmar que no requieran tabla nutricional.",
         "Excluir etiquetado si no se vende al consumidor final.",
         "Art. 2 Resol. 810/2021"),

        ("Etiqueta de productos reempacados",
         "Verificar que mantenga la información original.",
         "Incluir responsable del reenvasado.",
         "Art. 3 y 4 Resol. 5109/2005"),

        ("Productos importados",
         "Confirmar que cumplan normas y estén traducidos al español.",
         "Agregar rótulo complementario si aplica.",
         "Art. 2 Resol. 5109/2005"),
    ],

    "7. Control y evidencia documental": [
        ("Certificado de análisis",
         "Verificar existencia de soporte de laboratorio acreditado.",
         "Adjuntar o solicitar certificado de análisis.",
         "Art. 14 Resol. 810/2021"),

        ("Registro sanitario",
         "Comprobar visibilidad y vigencia del número INVIMA.",
         "Actualizar o solicitar registro vigente.",
         "Decreto 3075/1997 y Resol. 5109/2005"),

        ("Evidencia fotográfica",
         "Tomar fotografías del rótulo completo (frontal, lateral, trasera).",
         "Adjuntar evidencia visual al expediente.",
         "Guía INVIMA — práctica"),
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
st.markdown("Cada criterio incluye **qué verificar**, su **recomendación** y **referencia normativa**. Responde con ✅ Cumple / ❌ No cumple / ⚪ No aplica.")

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
# CÁLCULO DE CUMPLIMIENTO (sobre ítems contestados Sí/No)
# -----------------------------------------------------------
yes_count = sum(1 for v in st.session_state.status.values() if v == "yes")
no_count = sum(1 for v in st.session_state.status.values() if v == "no")
answered_count = yes_count + no_count
percent = round((yes_count / answered_count * 100), 1) if answered_count > 0 else 0.0

st.metric("Cumplimiento total (sobre ítems contestados)", f"{percent}%")
st.write(
    f"CUMPLE: {yes_count} — NO CUMPLE: {no_count} — "
    f"NO APLICA: {sum(1 for v in st.session_state.status.values() if v == 'na')} — "
    f"SIN RESPONDER: {sum(1 for v in st.session_state.status.values() if v == 'none')}"
)

# -----------------------------------------------------------
# ARMAR DataFrame para PDF (sin categorías ni 'Qué verificar')
# -----------------------------------------------------------
rows = []
for items in CATEGORIAS.values():
    for titulo, que_verificar, recomendacion, referencia in items:
        estado_val = st.session_state.status.get(titulo, "none")
        estado_humano = (
            "Cumple" if estado_val == "yes"
            else "No cumple" if estado_val == "no"
            else "No aplica" if estado_val == "na"
            else "Sin responder"
        )
        rows.append({
            "Ítem": titulo,
            "Estado": estado_humano,
            "Recomendación": recomendacion,
            "Referencia": referencia,
            "Observación": st.session_state.note.get(titulo, "")
        })

df = pd.DataFrame(rows, columns=["Ítem", "Estado", "Recomendación", "Referencia", "Observación"])

# -----------------------------------------------------------
# UTILIDAD: dividir Observación en renglones reales
# -----------------------------------------------------------
def split_observation_text(text: str, chunk: int = 100) -> str:
    """Divide el texto de Observación en líneas de 'chunk' caracteres (sin sangría)."""
    if not text:
        return ""
    s = str(text)
    if len(s) <= chunk:
        return s
    parts = [s[i:i+chunk] for i in range(0, len(s), chunk)]
    return "\n".join(parts)

# -----------------------------------------------------------
# PDF: A4 horizontal, sin cortes, con wrapping y saltos en Observación
# -----------------------------------------------------------
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors

def generar_pdf(df: pd.DataFrame, producto: str, proveedor: str, responsable: str, porcentaje: float, nombre_archivo: str) -> BytesIO:
    buf = BytesIO()

    # Márgenes 8 mm para aprovechar ancho; A4 landscape ≈ 297 x 210 mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=8*mm, rightMargin=8*mm,
        topMargin=8*mm, bottomMargin=8*mm
    )

    styles = getSampleStyleSheet()
    style_header = ParagraphStyle("header", parent=styles["Normal"], fontSize=8, leading=10)
    style_cell   = ParagraphStyle("cell",   parent=styles["Normal"], fontSize=7.5, leading=9)

    story = []
    # Encabezado
    story.append(Paragraph("<b>Informe de verificación de etiquetado nutricional — Juan Valdez</b>", style_header))
    story.append(Spacer(1, 3*mm))
    fecha_str = datetime.now().strftime("%Y-%m-%d")
    meta = (
        f"<b>Fecha:</b> {fecha_str} &nbsp;&nbsp; "
        f"<b>Producto:</b> {producto or '-'} &nbsp;&nbsp; "
        f"<b>Proveedor:</b> {proveedor or '-'} &nbsp;&nbsp; "
        f"<b>Responsable:</b> {responsable or '-'}"
    )
    story.append(Paragraph(meta, style_header))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"<b>Cumplimiento (sobre ítems contestados):</b> {porcentaje}%", style_header))
    story.append(Spacer(1, 5*mm))

    # Tabla
    data = [["Ítem", "Estado", "Recomendación", "Referencia", "Observación"]]
    for _, r in df.iterrows():
        obs = r["Observación"] or "-"
        if obs != "-":
            obs = split_observation_text(obs, chunk=100)

        data.append([
            Paragraph(str(r["Ítem"]),          style_cell),
            Paragraph(str(r["Estado"]),        style_cell),
            Paragraph(str(r["Recomendación"]), style_cell),
            Paragraph(str(r["Referencia"]),    style_cell),
            Paragraph(obs,                     style_cell),
        ])

    # Anchos (total útil ≈ 281 mm). Suma = 70 + 25 + 100 + 45 + 40 = 280 mm
    col_widths = [70*mm, 25*mm, 100*mm, 45*mm, 40*mm]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 8),
        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",(0,0), (-1,-1), 3),
        ("RIGHTPADDING",(0,0), (-1,-1), 3),
    ]))

    story.append(tbl)
    doc.build(story)
    buf.seek(0)
    return buf

# -----------------------------------------------------------
# BOTÓN ÚNICO: Generar y descargar PDF
# -----------------------------------------------------------
st.subheader("Generar informe PDF (A4 horizontal)")
if st.button("Generar PDF"):
    pdf_buffer = generar_pdf(df, producto, proveedor, responsable, percent, nombre_pdf)
    file_name = (nombre_pdf.strip() or f"informe_{datetime.now().strftime('%Y%m%d')}") + ".pdf"
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=file_name, mime="application/pdf")
