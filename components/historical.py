from __future__ import annotations
import io
import streamlit as st
import pandas as pd
from src.utils import load_history, export_history_csv, clear_history
from src.visualization import plot_historico


def _stats(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Decisiones registradas", len(df))
    with c2:
        st.metric("Tiempo promedio (min)", f"{df['tiempo_min'].mean():.1f}" if len(df) else "-")
    with c3:
        st.metric("Frecuencia promedio (x)", f"{df['frecuencia'].mean():.2f}" if len(df) else "-")


def render_historical() -> None:
    st.title("📈 Histórico de Riegos")

    df = load_history()
    if df.empty:
        st.info("Aún no hay registros. Usa la calculadora para generar decisiones.")
        return

    with st.expander("Filtros"):
        plantas = st.multiselect("Plantas", sorted(df["planta"].unique().tolist()))
        rango_tiempo = st.slider("Rango de tiempo (min)", 0.0, 60.0, (0.0, 60.0))
        if plantas:
            df = df[df["planta"].isin(plantas)]
        df = df[(df["tiempo_min"] >= rango_tiempo[0]) & (df["tiempo_min"] <= rango_tiempo[1])]

    _stats(df)
    st.dataframe(df.sort_values("ts", ascending=False), use_container_width=True)
    st.subheader("Evolución temporal")
    plot_historico(df)

    st.subheader("Exportar")
    if st.button("Exportar a CSV"):
        buf = io.BytesIO()
        path = "data/export_history.csv"
        export_history_csv(path)
        with open(path, "rb") as f:
            st.download_button("Descargar CSV", data=f, file_name="historial_riego.csv", mime="text/csv")
    if st.button("Limpiar Histórico"):
        clear_history()
        st.success("Histórico limpiado.")
