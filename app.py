import os
import streamlit as st
import streamlit.components.v1 as components
from components.tablero_control import render_dashboard
from components.simulador import render_simulator
from components.historico import render_historical
from components.informes import render_reports
from components.theme_toggle import ThemeToggle
from nucleo.utilidades import ensure_data_files

# Asegurar archivos de datos
ensure_data_files()

# Inicializar tema por defecto (OSCURO)
ThemeToggle.initialize_theme()
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # Tema oscuro por defecto

# Restore page after theme change rerun
if 'page_restore' in st.session_state:
    st.session_state.current_page = st.session_state.page_restore
    del st.session_state.page_restore

# Configuración de página
ThemeToggle.setup_page_config()

# Inyectar CSS del tema actual
ThemeToggle.inject_theme_css()

# ============= SIDEBAR - NAVEGACIÓN =============
with st.sidebar:

    # Componente de cambio de tema
    current_theme = ThemeToggle.render_theme_toggle()
    # (El selector de clima se muestra dentro de la Calculadora, no en la barra lateral.)

    # Logo
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("assets/images/icon-plant.png", width=40)
    with col2:
        st.subheader("Riego Inteligente")
        st.caption("Sistema Experto de Gestión Hídrica")

    st.divider()

    # Selector de página
    st.subheader("📋 Menú de Navegación")

    page_options = ["🏠 Inicio", "🌊 Calculadora de Riego", "📊 Visualizaciones", "📈 Histórico y Análisis", "🎓 Simulador de Escenarios"]

    # Maintain page selection
    if 'current_page' not in st.session_state:
        st.session_state.current_page = page_options[0]

    page = st.session_state.current_page

    # Navigation buttons in vertical list
    for i, option in enumerate(page_options):
        is_selected = st.session_state.current_page == option
        if st.button(
            option,
            key=f"nav_{i}_{option}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            help=f"Ir a {option}"
        ):
            st.session_state.current_page = option
            page = option

    st.divider()

    # Información rápida
    st.subheader("🔧 Información Técnica")
    st.info("""
    **Metodología:**
    Lógica Difusa Mamdani

    **Variables:**
    3-5 parámetros de entrada

    **Precisión:**
    ±5% error estimado
    """)

    st.divider()
    st.caption("Versión 1.0.0 | © 2025")

# ============= CONTENIDO PRINCIPAL =============

# PÁGINA DE INICIO
if page == "🏠 Inicio":
    # Header principal
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("assets/images/logo.png", width=250)
    with col2:
        st.title("Sistema de Riego Inteligente")
        st.subheader("Plataforma de Optimización Hídrica Basada en Lógica Difusa Tipo Mamdani")

    st.divider()

    # Descripción principal
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 📋 Presentación del Sistema

        Bienvenido al **Sistema Experto de Riego Inteligente**, una plataforma avanzada diseñada para
        optimizar el uso del agua en la agricultura mediante la aplicación de técnicas de inteligencia
        artificial y lógica difusa tipo Mamdani.

        Este sistema analiza variables ambientales en tiempo real para proporcionar recomendaciones
        precisas sobre la cantidad y frecuencia de riego necesaria, contribuyendo a:

        - 💧 **Ahorro de agua** y recursos hídricos
        - 🌾 **Mejora en la productividad** agrícola
        - 🌍 **Sostenibilidad** ambiental
        - 📊 **Toma de decisiones** basada en datos
        """)

        st.success("**Desarrollado con:** Python, Streamlit, Scikit-Fuzzy, NumPy, Pandas")

    with col2:
        st.markdown("### 🎯 Características")
        st.markdown("""
        ✅ Motor de inferencia difusa
        ✅ Análisis en tiempo real
        ✅ Visualizaciones interactivas
        ✅ Base de datos histórica
        ✅ Simulador de escenarios
        ✅ Exportación de reportes
        """)

    st.divider()

    # Módulos del sistema
    st.markdown("## 🔧 Módulos del Sistema")

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("🌊 **Calculadora de Riego**", expanded=True):
            st.markdown("""
            **Función Principal:**
            Calcula la cantidad óptima de agua necesaria para el riego basándose en múltiples variables.

            **Variables de Entrada:**
            - Humedad del suelo (%)
            - Temperatura ambiente (°C)
            - Tipo de cultivo
            - Condiciones meteorológicas

            **Salida:**
            Recomendación de tiempo de riego en minutos con nivel de confianza.
            """)

        with st.expander("📊 **Visualizaciones**"):
            st.markdown("""
            **Análisis Gráfico del Sistema:**

            - **Funciones de membresía**: Representación de conjuntos difusos para cada variable
            - **Superficies 3D**: Relación entre variables de entrada y salida
            - **Gráficos de desfuzzificación**: Proceso de conversión de salida difusa a valor crisp
            - **Mapas de calor**: Correlación entre parámetros del sistema

            Herramientas visuales para comprender el comportamiento del motor de inferencia.
            """)

    with col2:
        with st.expander("📈 **Histórico y Análisis**"):
            st.markdown("""
            **Gestión de Datos Históricos:**

            - **Base de datos** de todas las mediciones realizadas
            - **Análisis estadístico** de tendencias temporales
            - **Comparativas** de eficiencia del sistema
            - **Exportación** de reportes en formatos CSV y PDF

            Permite evaluar el rendimiento del sistema a lo largo del tiempo y
            realizar ajustes para optimizar las estrategias de riego.
            """)

        with st.expander("🎓 **Simulador de Escenarios**"):
            st.markdown("""
            **Pruebas y Entrenamiento:**

            - **Escenarios predefinidos** (sequía extrema, lluvia abundante, temperatura alta, etc.)
            - **Simulaciones personalizadas** con parámetros definidos por el usuario
            - **Análisis de sensibilidad** de variables individuales
            - **Casos de estudio** educativos para comprensión del sistema

            Ideal para entender cómo responde el sistema ante diferentes condiciones climáticas.
            """)

    st.divider()

    # Metodología
    st.markdown("## 🧠 Metodología: Lógica Difusa Mamdani")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 1️⃣ Fuzzificación
        Conversión de valores numéricos
        de entrada en conjuntos difusos
        mediante funciones de membresía.
        """)

    with col2:
        st.markdown("""
        ### 2️⃣ Inferencia
        Aplicación de reglas difusas
        para obtener conclusiones basadas
        en el conocimiento experto.
        """)

    with col3:
        st.markdown("""
        ### 3️⃣ Desfuzzificación
        Conversión de la salida difusa
        en un valor numérico concreto
        utilizable.
        """)

    st.divider()

    # Instrucciones de uso
    st.markdown("## 📖 Guía de Uso")

    st.info("""
    **Pasos para utilizar el sistema:**

    1. Seleccione el módulo deseado desde el menú lateral izquierdo
    2. En **Calculadora de Riego**, ingrese los valores actuales de sus sensores
    3. El sistema calculará automáticamente la recomendación de riego
    4. Explore las **Visualizaciones** para comprender el funcionamiento interno
    5. Consulte el **Histórico** para analizar tendencias y patrones
    6. Use el **Simulador** para experimentar con diferentes escenarios
    """)

    st.divider()

    # Footer
    st.success("**Sistema de Riego Inteligente** | Ingeniería Agrícola y Tecnología")
    st.caption("Optimización mediante Lógica Difusa Mamdani | Universidad [Nombre] | Todos los derechos reservados © 2025")

# CALCULADORA DE RIEGO
elif page == "🌊 Calculadora de Riego":
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("assets/images/icon-water.png", width=100)
    with col2:
        st.title("Calculadora de Riego")
        st.write("Ingrese los parámetros ambientales para calcular la cantidad óptima de agua necesaria.")
    st.divider()
    render_dashboard()

# VISUALIZACIONES
elif page == "📊 Visualizaciones":
    try:
        from nucleo.visualizadores import renderizar_pagina_visualizaciones
        renderizar_pagina_visualizaciones()
    except ImportError as e:
        st.error(f"❌ Sistema de visualización no disponible: {e}")

# HISTÓRICO
elif page == "📈 Histórico y Análisis":
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("assets/images/icon-history.png", width=100)
    with col2:
        st.title("Análisis Histórico de Datos")
        st.write("Consulte y analice el historial de mediciones y recomendaciones del sistema.")
    st.divider()
    render_historical()

# SIMULADOR
elif page == "🎓 Simulador de Escenarios":
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("assets/images/icon-simulator.png", width=100)
    with col2:
        st.title("Simulador de Escenarios")
        st.write("Pruebe diferentes condiciones ambientales y analice las respuestas del sistema.")
    st.divider()
    render_simulator()
