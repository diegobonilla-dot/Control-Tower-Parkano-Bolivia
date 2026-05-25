import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Control Tower - Parkano Bolivia", layout="wide")
st.title("📊 Control Tower - Parkano Bolivia")

# TU LINK REAL DE GOOGLE SHEETS EN FORMATO CSV:
DATA_URL = "https://docs.google.com/spreadsheets/d/1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns/export?format=csv&gid=158096369"

@st.cache_data(ttl=300) # Se actualiza automáticamente cada 5 minutos
def load_data():
    df = pd.read_csv(DATA_URL)
    return df

try:
    df = load_data()

    # Botón para forzar actualización inmediata
    if st.sidebar.button("🔄 Forzar Actualización de Datos"):
        st.cache_data.clear()
        st.rerun()

    # Vista previa de los datos para ver tus columnas
    st.subheader("Datos actuales del Excel Sheet")
    st.dataframe(df)

except Exception as e:
    st.error(f"Error al cargar los datos de Google Sheets: {e}")
    st.info("Asegúrate de que el Google Sheet esté compartido como 'Cualquier persona con el enlace puede ver'.")
