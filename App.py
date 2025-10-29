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
# (Se mantiene tu estructura, solo se enriquecen los textos)
# -----------------------------------------------------------
CATEGORIAS = {
    "1. Identificación general del producto": [
        ("Nombre del alimento",
         "Verificar que el nombre refleje la verdadera naturaleza del producto (no genérico). En producto terminado debe describir el alimento final (p. ej., “Bebida de café con leche”); en materia prima, el insumo (p. ej., “Jarabe de glucosa”). (Art. 5.1 Res. 5109/2005)",
         "Debe indicar la verdadera naturaleza del producto.",
         "Art. 5.1 Resol. 5109/2005"),

        ("Marca comercial",
         "Comprobar que la marca no sustituya la denominación del alimento. La marca puede acompañar, nunca reemplazar el nombre del alimento. (Art. 5.1.2 Res. 5109/2005)",
         "Debe coexistir con la denominación del alimento.",
         "Art. 5.1.2 Resol. 5109/2005"),

        ("Lista de ingredientes",
         "Revisar que todos los ingredientes estén listados en orden decreciente de peso al momento de fabricación; incluir aditivos con su categoría funcional y nombre específico (p. ej., “Conservante (Sorbato de potasio)”). En materias primas simples puede no aplicar. (Art. 5.2 Res. 5109/2005)",
         "Agregar lista completa y verificar el orden correcto.",
         "Art. 5.2 Resol. 5109/2005"),

        ("Aditivos alimentarios",
         "Verificar que los aditivos se declaren por su nombre común o categoría funcional; no usar códigos o abreviaturas. (Art. 5.2.1 Res. 5109/2005)",
         "Declarar correctamente los aditivos alimentarios.",
         "Art. 5.2.1 Resol. 5109/2005"),

        ("Contenido neto",
         "Verificar que el contenido neto se exprese en unidades SI (g, kg, mL o L) sin incluir el envase, con legibilidad adecuada. Aplica principalmente para producto terminado envasado. (Anexo Res. 5109/2005)",
         "Declarar contenido neto con unidad del Sistema Internacional.",
         "Art. 3 y Anexo Resol. 5109/2005"),

        ("Lote",
         "Comprobar que el número/código de lote sea visible, indeleble y legible para trazabilidad, tanto en producto terminado como en materia prima. (Art. 5.4 Res. 5109/2005)",
         "Debe existir lote visible y legible.",
         "Art. 5.4 Resol. 5109/2005"),

        ("Fecha de vencimiento o duración mínima",
         "Verificar legibilidad, ubicación y formato (día/mes/año). En materias primas corresponde al insumo; en producto terminado, al alimento para consumo. (Art. 5.5 Res. 5109/2005)",
         "Usar formato legible y visible (día/mes/año).",
         "Art. 5.5 Resol. 5109/2005"),

        ("País de origen",
         "Comprobar que se declare “Hecho en…” o “Producto de…”. Para materias primas de uso interno industrial puede no exigirse al consumidor final, pero debe obrar documentalmente. (Art. 5.9 Res. 5109/2005)",
         "Incluir país de origen claramente.",
         "Art. 5.9 Resol. 5109/2005"),

        ("Nombre y dirección del fabricante/importador",
         "Revisar que incluya razón social y dirección completa del fabricante, importador o reenvasador, según aplique. (Art. 5.8 Res. 5109/2005)",
         "Incluir nombre y dirección completos.",
         "Art. 5.8 Resol. 5109/2005"),
    ],

    "2. Cumplimiento de requisitos gráficos y sanitarios": [
        ("Legibilidad",
         "Asegurar que la información sea visible, indeleble y contrastante con el fondo; tamaño de fuente suficiente y tipografía clara (Arial/Helvética sugeridas por Res. 810 para la tabla). (Art. 4 y 6 Res. 5109/2005; Art. 27 Res. 810/2021)",
         "Mejorar contraste o tamaño del texto.",
         "Art. 4 y 6 Resol. 5109/2005"),

        ("Idioma",
         "Verificar que toda la información obligatoria esté en español; si la etiqueta original está en otro idioma, usar rótulo complementario adherido. (Art. 5 Res. 5109/2005; Art. 27.1.3 Res. 810/2021)",
         "Agregar traducción completa en español si aplica.",
         "Art. 5 Resol. 5109/2005"),

        ("Ubicación del rótulo",
         "Revisar que la información esté en la cara principal visible al consumidor, sin ocultamientos ni pliegues que dificulten la lectura. (Art. 3 y 5 Res. 5109/2005)",
         "Reubicar etiqueta si no es visible para el consumidor.",
         "Art. 3 y 5 Resol. 5109/2005"),

        ("Prohibición de inducir a error",
         "Verificar que no existan afirmaciones falsas, engañosas o que atribuyan propiedades medicinales; evitar imágenes o frases que puedan confundir. (Art. 4 Res. 5109/2005)",
         "Corregir mensajes que puedan inducir a error.",
         "Art. 4 Resol. 5109/2005"),
    ],

    "3. Etiquetado nutricional (Información nutricional obligatoria)": [
        ("Tabla nutricional presente",
         "Confirmar presencia de la tabla nutricional cuando el producto se destine al consumidor final. Las materias primas industriales están exceptuadas. (Art. 2 y Art. 8–10 Res. 810/2021; mod. 2492/2022)",
         "Incluir tabla con los nutrientes requeridos cuando aplique.",
         "Art. 8, 9 y 10 Resol. 810/2021"),

        ("Unidad de medida",
         "Verificar que los nutrientes se declaren por 100 g o 100 mL y por porción; coherencia con estado físico (sólido/líquido). (Art. 12 Res. 810/2021)",
         "Corregir las unidades según corresponda.",
         "Art. 12 Resol. 810/2021"),

        ("Porciones por envase",
         "Revisar que indique el número de porciones por envase, salvo productos de peso variable. (Art. 12 y Par. 2 Art. 2 Res. 810 mod. 2492/2022)",
         "Agregar número de porciones si aplica.",
         "Art. 12 y Par. 2 Art. 2 Resol. 810 modif. 2492/2022"),

        ("Nutrientes adicionales",
         "Cuando se declaren vitaminas/minerales, verificar que cumplan los requisitos de inclusión mínima/máxima y la presentación separada por una línea de los demás nutrientes. (Art. 15 y 28.3 Res. 810/2021)",
         "Ajustar la declaración de micronutrientes según límites.",
         "Art. 15 Resol. 810/2021"),

        ("Tolerancias analíticas",
         "Comparar valores declarados vs. análisis de laboratorio: la diferencia no debe superar ±20 %. (Art. 14 Res. 810/2021)",
         "Ajustar declaraciones según análisis.",
         "Art. 14 Resol. 810/2021"),

        ("Fuente de nutrientes",
         "Para usar términos como “fuente de…/alto en…”, verificar mínimos establecidos por la norma y que el producto no presente sellos de advertencia que los invaliden. (Art. 16 Res. 810 mod. 2492/2022)",
         "Corregir o retirar declaraciones si no cumple.",
         "Art. 16 Resol. 810 modif. 2492/2022"),
    ],

    "4. Declaraciones nutricionales y de salud (voluntarias)": [
        ("Declaraciones nutricionales",
         "Permitir solo si el producto cumple con el perfil de nutrientes y no exhibe sellos de advertencia. Evitar términos ambiguos; sustentar cuantitativamente (p. ej., “fuente de…” con %VD). (Art. 25.4 Res. 810 mod. 2492/2022)",
         "Retirar declaraciones que no cumplan con los criterios.",
         "Art. 25.4 Resol. 810 modif. 2492/2022"),

        ("Declaraciones de salud",
         "Verificar que estén autorizadas por el MSPS, sean veraces y sustentadas científicamente; no atribuir propiedades medicinales. (Art. 25 Res. 810/2021)",
         "Incluir solo declaraciones aprobadas por el Ministerio.",
         "Art. 25 Resol. 810/2021"),

        ("Prohibición de declaraciones engañosas",
         "Asegurar que el rótulo no induzca a error sobre composición o beneficios; evitar equivalencias simplistas no sustentadas. (Art. 25.5 Res. 810/2021)",
         "Eliminar declaraciones confusas o engañosas.",
         "Art. 25.5 Resol. 810/2021"),
    ],

    "5. Etiquetado frontal de advertencia (Sellos negros)": [
        ("Aplicabilidad",
         "Verificar si aplica en alimentos procesados/ultraprocesados con exceso de azúcares, grasas saturadas, sodio o presencia de edulcorantes. (Art. 32 Res. 810 mod. 2492/2022)",
         "Evaluar composición para determinar necesidad de sellos.",
         "Art. 32 Resol. 810 modif. 2492/2022"),

        ("Forma y color",
         "Comprobar octágono negro, borde blanco y texto “EXCESO EN” en mayúsculas, tipografía adecuada. (Art. 32 Res. 2492/2022)",
         "Corregir forma o color según especificación oficial.",
         "Art. 32 Resol. 2492/2022"),

        ("Ubicación",
         "Verificar ubicación en tercio superior de la cara principal de exhibición, visible y sin obstrucciones. (Art. 32 Res. 2492/2022)",
         "Reubicar sello si no cumple posición.",
         "Art. 32 Resol. 2492/2022"),

        ("Tamaño del sello",
         "Verificar dimensión mínima según el área principal del envase conforme a Tabla 17. (Art. 32 Res. 810 mod. 2492/2022)",
         "Ajustar tamaño del sello según tabla normativa.",
         "Art. 32 Resol. 810 modif. 2492/2022"),

        ("Tipografía",
         "Confirmar uso de tipografía blanca de alto contraste sobre fondo negro (Arial Black recomendada), sin otros elementos que distraigan. (Art. 32 Res. 810/2021)",
         "Corregir tipografía o contraste del sello.",
         "Art. 32 Resol. 810/2021"),

        ("Límite de nutrientes críticos",
         "Comparar con límites OPS: azúcares libres ≥10% kcal totales; grasas saturadas ≥10% kcal totales; grasas trans ≥1% kcal totales; sodio ≥1 mg/kcal o ≥300 mg/100 g (sólidos). Para bebidas sin aporte energético: criterio específico de sodio (≥40 mg/100 mL). Exceder obliga a sello. (Tabla 17 Res. 810 mod. 2492/2022)",
         "Revisar composición frente a límites establecidos.",
         "Tabla 17 Resol. 810 modif. 2492/2022"),

        ("Sello 'Contiene edulcorante'",
         "Si contiene edulcorantes (calóricos o no), incluir el sello correspondiente (“Contiene edulcorante, no recomendable en niños”). (Art. 32 Res. 2492/2022)",
         "Agregar sello correspondiente si aplica.",
         "Art. 32 Resol. 2492/2022"),

        ("Excepciones al sello",
         "Verificar si el producto se encuentra exento (no procesados o mínimamente procesados, típicos o artesanales, fórmulas infantiles, APMES, etc.). (Art. 2 Res. 810 mod. 2492/2022)",
         "Aplicar excepción cuando corresponda.",
         "Art. 2 Resol. 810 modif. 2492/2022"),
    ],

    "6. Requisitos especiales": [
        ("Carne cruda con condimentos",
         "Verificar el contenido de sodio; si excede 300 mg/100 g o 1 mg/kcal requiere sello frontal de sodio. (Par. 1 Art. 2 Res. 810 mod. 2492/2022)",
         "Incluir sello frontal si aplica.",
         "Par. 1 Art. 2 Resol. 810 modif. 2492/2022"),

        ("Productos a granel",
         "Confirmar exención de tabla nutricional y sellos cuando no hay envase individual; asegurar trazabilidad documental. (Art. 2 Res. 810 mod. 2492/2022)",
         "Registrar exención si aplica.",
         "Art. 2 Resol. 810 modif. 2492/2022"),

        ("Materias primas industriales",
         "Verificar que no requieran tabla nutricional ni sellos (no destinadas al consumidor final). Deben llevar identificación, lote, país de origen y fabricante. (Art. 2 Res. 810/2021)",
         "Excluir etiquetado nutricional si no se vende al consumidor final.",
         "Art. 2 Resol. 810/2021"),

        ("Etiqueta de productos reempacados",
         "Comprobar que mantenga toda la información original y agregue el responsable del reenvasado. (Art. 3 y 4 Res. 5109/2005)",
         "Incluir responsable del reenvasado.",
         "Art. 3 y 4 Resol. 5109/2005"),

        ("Productos importados",
         "Confirmar cumplimiento de normas nacionales y traducción al español mediante rótulo complementario cuando aplique. (Art. 2 Res. 5109/2005; Art. 27.1.3 Res. 810/2021)",
         "Agregar rótulo complementario si aplica.",
         "Art. 2 Resol. 5109/2005"),
    ],

    "7. Control y evidencia documental": [
        ("Certificado de análisis",
         "Verificar soporte analítico emitido por laboratorio acreditado para validar los valores nutricionales declarados. (Art. 14 Res. 810/2021)",
         "Adjuntar o solicitar certificado de análisis.",
         "Art. 14 Resol. 810/2021"),

        ("Registro sanitario",
         "Comprobar visibilidad y vigencia del número INVIMA en productos terminados; en materias primas, contar con habilitaciones/soportes regulatorios aplicables. (Decreto 3075/1997; Res. 5109/2005)",
         "Actualizar o solicitar registro vigente.",
         "Decreto 3075/1997 y Resol. 5109/2005"),

        ("Evidencia fotográfica",
         "Tomar fotografías del rótulo (frontal, lateral, posterior) y anexarlas como respaldo de la inspección visual. (Guía INVIMA — práctica)",
         "Adjuntar evidencia visual al expediente.",
         "Guía INVIMA — práctica"),
    ]
}

# -----------------------------------------------------------
# MAPA DE APLICABILIDAD VISIBLE EN PANTALLA (Producto terminado / Materia prima / Ambos)
# (No altera tu estructura; solo imprime una línea debajo de “Qué verificar”)
# -----------------------------------------------------------
APLICA = {
    # Categoría 1
    "Nombre del alimento": "Ambos",
    "Marca comercial": "Ambos",
    "Lista de ingredientes": "Producto terminado",
    "Aditivos alimentarios": "Ambos",
    "Contenido neto": "Producto terminado",
    "Lote": "Ambos",
    "Fecha de vencimiento o duración mínima": "Ambos",
    "País de origen": "Ambos",
    "Nombre y dirección del fabricante/importador": "Ambos",

    # Categoría 2
    "Legibilidad": "Ambos",
    "Idioma": "Ambos",
    "Ubicación del rótulo": "Ambos",
    "Prohibición de inducir a error": "Ambos",

    # Categoría 3
    "Tabla nutricional presente": "Producto terminado",
    "Unidad de medida": "Producto terminado",
    "Porciones por envase": "Producto terminado",
    "Nutrientes adicionales": "Producto terminado",
    "Tolerancias analíticas": "Producto terminado",
    "Fuente de nutrientes": "Producto terminado",

    # Categoría 4
    "Declaraciones nutricionales": "Producto terminado",
    "Declaraciones de salud": "Producto terminado",
    "Prohibición de declaraciones engañosas": "Ambos",

    # Categoría 5
    "Aplicabilidad": "Producto terminado",
    "Forma y color": "Producto terminado",
    "Ubicación": "Producto terminado",
    "Tamaño del sello": "Producto terminado",
    "Tipografía": "Producto terminado",
    "Límite de nutrientes críticos": "Producto terminado",
    "Sello 'Contiene edulcorante'": "Producto terminado",
    "Excepciones al sello": "Producto terminado",

    # Categoría 6
    "Carne cruda con condimentos": "Producto terminado",
    "Productos a granel": "Producto terminado",
    "Materias primas industriales": "Materia prima",
    "Etiqueta de productos reempacados": "Producto terminado",
    "Productos importados": "Ambos",

    # Categoría 7
    "Certificado de análisis": "Ambos",
    "Registro sanitario": "Producto terminado",
    "Evidencia fotográfica": "Producto terminado",
}
# -----------------------------------------------------------
# ESTADO INICIAL (se mantiene tu bloque)
# -----------------------------------------------------------
if "status" not in st.session_state:
    st.session_state.status = {i[0]: "none" for c in CATEGORIAS.values() for i in c}
if "note" not in st.session_state:
    st.session_state.note = {i[0]: "" for c in CATEGORIAS.values() for i in c}

# -----------------------------------------------------------
# INTERFAZ DE CHECKLIST (se mantiene tu estructura)
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
        st.markdown(f"**Aplica a:** {APLICA.get(titulo, 'Ambos')}")

        # 🔹 BLOQUE informativo existente — Solo para "Tamaño del sello" (Tabla 17)
        if titulo == "Tamaño del sello":
            st.markdown("**Referencia normativa: Tabla 17 — Tamaño mínimo del sello según el área principal del envase**")
            opciones_tabla17 = {
                "< 30 cm²": "Se rotula envase secundario y si no cuenta con el se incluye QR o página web para consultar",
                "≥30 a < 35 cm²": "1,7 cm de lado",
                "≥35 a < 40 cm²": "1,8 cm de lado",
                "≥40 a < 50 cm²": "2,0 cm de lado",
                "≥50 a < 60 cm²": "2,2 cm de lado",
                "≥60 a < 80 cm²": "2,5 cm de lado",
                "≥80 a < 100 cm²": "2,8 cm de lado",
                "≥100 a < 125 cm²": "3,1 cm de lado",
                "≥125 a < 150 cm²": "3,4 cm de lado",
                "≥150 a < 200 cm²": "3,9 cm de lado",
                "≥200 a < 250 cm²": "4,4 cm de lado",
                "≥250 a < 300 cm²": "4,8 cm de lado",
                "> 300 cm²": "15% del tamaño de la cara principal"
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
