import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Mi Dashboard Dinámico", layout="wide")
st.title("📊 Dashboard Automatizado en Tiempo Real")

# Link de tu Google Sheets (Reemplázalo por tu link CSV real cuando lo tengas)
DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT37GvyvJ-B0uKAnF8lUki9yYp1iYh_nNl3mZ8Vn-Z7dG1M/pub?output=csv"

@st.cache_data(ttl=600) # Se actualiza automáticamente cada 10 minutos
def load_data():
    df = pd.read_csv(DATA_URL)
    return df

try:
    df = load_data()

    if st.sidebar.button("🔄 Forzar Actualización de Datos"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.header("Filtros")
    if 'Categoría' in df.columns:
        categorias = st.sidebar.multiselect("Selecciona Categoría:", options=df['Categoría'].unique(), default=df['Categoría'].unique())
        df_filtrado = df[df['Categoría'].isin(categorias)]
    else:
        df_filtrado = df

    st.subheader("📈 Métricas Clave")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registros", len(df_filtrado))
    
    if 'Ventas' in df_filtrado.columns:
        col2.metric("Total Ventas", f"${df_filtrado['Ventas'].sum():,.2f}")
        col3.metric("Promedio Ventas", f"${df_filtrado['Ventas'].mean():,.2f}")

    st.subheader("📊 Análisis Visual")
    if 'Ventas' in df_filtrado.columns and 'Fecha' in df_filtrado.columns:
        fig = px.line(df_filtrado, x='Fecha', y='Ventas', title="Evolución de Ventas en el Tiempo")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Estructura tus columnas como 'Fecha', 'Categoría' y 'Ventas' para ver el gráfico de ejemplo, o edita el código.")
        st.dataframe(df_filtrado)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
