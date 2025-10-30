"""
Componente de Cambio de Tema
Permite cambiar entre modo claro y oscuro dinámicamente
"""

try:
    import streamlit as st
except ImportError:
    st = None


class ThemeToggle:
    """Controlador del cambio de tema entre claro y oscuro"""

    @staticmethod
    def initialize_theme():
        """Inicializa el estado del tema"""
        if 'theme' not in st.session_state:
            st.session_state.theme = 'dark'

        if 'theme_initialized' not in st.session_state:
            st.session_state.theme_initialized = False

    @staticmethod
    def setup_page_config():
        """Configura Streamlit según el tema actual"""
        if not st.session_state.theme_initialized:
            # Solo configuramos una vez por sesión
            if st.session_state.theme == 'dark':
                st.set_page_config(
                    page_title="Sistema Experto de Riego",
                    page_icon="💧",
                    layout="wide",
                    initial_sidebar_state="expanded",
                    menu_items={
                        'Get Help': 'https://www.streamlit.io/',
                        'Report a bug': "https://github.com",
                        'About': "# Sistema Experto de Riego Inteligente"
                    }
                )
            else:
                st.set_page_config(
                    page_title="Sistema Experto de Riego",
                    page_icon="💧",
                    layout="wide",
                    initial_sidebar_state="expanded",
                    menu_items={
                        'Get Help': 'https://www.streamlit.io/',
                        'Report a bug': "https://github.com",
                        'About': "# Sistema Experto de Riego Inteligente"
                    }
                )
            st.session_state.theme_initialized = True

    @staticmethod
    def get_theme_colors():
        """Retorna colores según el tema actual"""
        if st.session_state.theme == 'dark':
            return {
                'bg': '#0E1117',
                'secondary_bg': '#262730',
                'text': '#FAFAFA',
                'primary': '#FF4B4B',
                'accent': '#29b5e8',
                'success': '#06A77D',
                'warning': '#F39C12',
                'danger': '#E74C3C',
                'card_bg': '#262730',
                'border': '#404040'
            }
        else:
            # Tema claro con buena legibilidad
            return {
                'bg': '#FFFFFF',
                'secondary_bg': '#F8F9FA',
                'text': '#2D3142',
                'primary': '#FF4B4B',
                'accent': '#2E86AB',
                'success': '#28A745',
                'warning': '#FFC107',
                'danger': '#DC3545',
                'card_bg': 'white',
                'border': '#E9ECEF'
            }

    @staticmethod
    def render_theme_toggle():
        """Renderiza el toggle del tema en la sidebar"""

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎨 Tema")

        col1, col2, col3 = st.sidebar.columns([1, 3, 1])

        icon_left = "🌙" if st.session_state.theme == 'dark' else "☀️"
        icon_right = "☀️" if st.session_state.theme == 'dark' else "🌙"

        with col2:
            if st.button(
                f"{icon_left} {'Oscuro' if st.session_state.theme == 'dark' else 'Claro'} {icon_right}",
                key="theme_toggle",
                help=f"Cambiar a modo {'claro' if st.session_state.theme == 'dark' else 'oscuro'}",
                use_container_width=True
            ):
                # Cambiar tema
                st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
                st.session_state.theme_initialized = False

                # Aplicar cambio inmediatamente
                st.rerun()

        # Mostrar estado actual
        current_theme = "Oscuro 🌙" if st.session_state.theme == 'dark' else "Claro ☀️"
        st.sidebar.markdown(f"**Actual:** {current_theme}")

        return st.session_state.theme

    @staticmethod
    def inject_theme_css():
        """Inyecta CSS adaptativo según el tema"""
        colors = ThemeToggle.get_theme_colors()

        css = f"""
        <style>
        /* CSS dinámico según tema */
        :root {{
            --theme-bg: {colors['bg']};
            --theme-secondary-bg: {colors['secondary_bg']};
            --theme-text: {colors['text']};
            --theme-primary: {colors['primary']};
            --theme-accent: {colors['accent']};
            --theme-success: {colors['success']};
            --theme-warning: {colors['warning']};
            --theme-danger: {colors['danger']};
            --theme-card-bg: {colors['card_bg']};
            --theme-border: {colors['border']};
        }}

        /* Aplica variables CSS dinámicamente */
        .main {{
            background-color: var(--theme-bg) !important;
            color: var(--theme-text) !important;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: var(--theme-secondary-bg) !important;
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--theme-text) !important;
        }}

        /* Texto general */
        p, span, div:not([class*="st-"]), label {{
            color: var(--theme-text) !important;
        }}

        /* Tabs */
        [data-testid="stTabs"] [data-testid="stTab"] {{
            background-color: var(--theme-secondary-bg) !important;
            color: var(--theme-text) !important;
        }}

        /* Métricas */
        [data-testid="stMetricValue"] {{
            color: var(--theme-primary) !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--theme-text) !important;
        }}

        /* Selectores */
        [data-testid="stSelectbox"] button {{
            background-color: var(--theme-card-bg) !important;
            color: var(--theme-text) !important;
            border-color: var(--theme-border) !important;
        }}

        /* Sliders */
        [data-testid="stSlider"] {{
            color: var(--theme-text) !important;
        }}

        /* Botones */
        [data-testid="stButton"] button {{
            background-color: var(--theme-primary) !important;
            color: white !important;
            border: none !important;
        }}

        /* Dataframe */
        [data-testid="stDataframe"] {{
            background-color: var(--theme-card-bg) !important;
        }}

        /* Cards personalizados */
        .stCard {{
            background-color: var(--theme-card-bg) !important;
            border: 1px solid var(--theme-border) !important;
            color: var(--theme-text) !important;
        }}

        /* Expander */
        [data-testid="stExpander"] summary {{
            color: var(--theme-text) !important;
            background-color: var(--theme-secondary-bg) !important;
        }}

        /* Plotly charts */
        .js-plotly-plot {{
            background-color: var(--theme-card-bg) !important;
        }}

        .plotly-notifier {{
            fill: var(--theme-text) !important;
        }}

        /* Específicos del sistema */
        .card {{
            background-color: var(--theme-card-bg) !important;
            border: 1px solid var(--theme-border) !important;
            color: var(--theme-text) !important;
            box-shadow: 0 2px 8px {'rgba(0,0,0,0.3)' if colors['bg'] == '#0E1117' else 'rgba(0,0,0,0.1)'} !important;
        }}

        .stMetric {{
            background-color: var(--theme-card-bg) !important;
            border: 1px solid var(--theme-border) !important;
            border-radius: 8px !important;
            padding: 15px !important;
        }}

        /* Asegurar legibilidad en modo oscuro */
        .stMarkdown, .stText {{
            color: var(--theme-text) !important;
        }}

        .st-emotion-cache-1v0mbdj, .st-emotion-cache-1r6m2br {{
            color: var(--theme-text) !important;
        }}

        </style>
        """

        st.markdown(css, unsafe_allow_html=True)

    @staticmethod
    def get_plotly_template():
        """Template de Plotly según el tema actual"""
        if st.session_state.theme == 'dark':
            return "plotly_dark"
        else:
            return "plotly_white"

    @staticmethod
    def update_visualization_config(config):
        """Actualiza la configuración de visualización según el tema"""
        colors = ThemeToggle.get_theme_colors()

        # Actualizar colores de la configuración
        config.LAYOUT_TEMPLATE = ThemeToggle.get_plotly_template()
        config.COLORS.update(colors)
        config.FONT_FAMILY = 'Segoe UI, sans-serif'

        return config
