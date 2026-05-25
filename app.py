import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Control Tower Premium | Parkano Bolivia", page_icon="📈", layout="wide")

st.title("🛡️ Control Tower Premium — Parkano Bolivia")
st.markdown("---")

# 2. ENLACE DE DATOS
DATA_URL = "https://docs.google.com/spreadsheets/d/1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns/export?format=csv&gid=158096369"

# =====================================================================
# 🛠️ REEMPLAZA LOS NOMBRES DE ABAJO POR LOS NOMBRES EXACTOS DE TU EXCEL:
COLUMNA_NUMERICA_PRINCIPAL = "Ventas"   # Pon aquí el nombre de tu columna con números (ej: "Monto", "Cantidad")
COLUMNA_TEXTO_PRINCIPAL = "Categoría"   # Pon aquí el nombre de tu columna de texto (ej: "Detalle", "Producto")
# =====================================================================

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(DATA_URL)
    df = df.dropna(how='all', axis=1)
    
    # Forzar la conversión de números limpiando caracteres extraños
    for col in df.columns:
        # Si la columna parece tener números, la limpiamos para Python
        if df[col].dtype == object:
            # Quitamos espacios, signos de dólar y corregimos comas por puntos
            test_clean = df[col].astype(str).str.replace(r'[\$,\s]', '', regex=True)
            if test_clean.str.isnumeric().any():
                df[col] = pd.to_numeric(test_clean, errors='coerce')
                
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    # Controles laterales
    if st.sidebar.button("🔄 Forzar Actualización Inmediata"):
        st.cache_data.clear()
        st.rerun()

    # Detectar columnas automáticamente tras la limpieza
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=[object]).columns.tolist()
    
    # Filtro Dinámico por Fecha o Categoría
    st.sidebar.markdown("### 🔍 Filtros Globales")
    filtro_col = st.sidebar.selectbox("Filtrar por columna:", df.columns.tolist())
    opciones = df[filtro_col].dropna().unique().tolist()
    seleccion = st.sidebar.multiselect(f"Selecciona valores:", opciones, default=opciones)
    df = df[df[filtro_col].isin(seleccion)]

    # Pestañas
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Descriptivo", "🔮 Inteligencia Predictiva", "📋 Base de Datos Activa"])

    # PESTAÑA 1: DESCRIPTIVO
    with tab1:
        st.header("📈 Resumen Estadístico y KPIs")
        
        if num_cols:
            cols_kpi = st.columns(min(len(num_cols), 4))
            for i, col in enumerate(num_cols[:4]):
                with cols_kpi[i]:
                    st.metric(label=f"Total {col}", value=f"{df[col].sum():,.2f}", delta=f"Promedio: {df[col].mean():,.1f}")
        else:
            # Si Python no detectó automáticamente, usamos la columna que configuraste manualmente arriba
            try:
                df[COLUMNA_NUMERICA_PRINCIPAL] = pd.to_numeric(df[COLUMNA_NUMERICA_PRINCIPAL].astype(str).str.replace(r'[\$,\s]', '', regex=True), errors='coerce')
                cols_kpi = st.columns(2)
                cols_kpi[0].metric(label=f"Total {COLUMNA_NUMERICA_PRINCIPAL}", value=f"{df[COLUMNA_NUMERICA_PRINCIPAL].sum():,.2f}")
                cols_kpi[1].metric(label=f"Promedio {COLUMNA_NUMERICA_PRINCIPAL}", value=f"{df[COLUMNA_NUMERICA_PRINCIPAL].mean():,.2f}")
                num_cols.append(COLUMNA_NUMERICA_PRINCIPAL)
            except:
                st.warning("⚠️ No se detectaron números automáticamente. Asegúrate de escribir los nombres exactos de tus columnas en las líneas 18 y 19 del código en GitHub.")

        st.markdown("### 📊 Visualización de Tendencias")
        c1, c2 = st.columns(2)
        
        with c1:
            x_axis = COLUMNA_TEXTO_PRINCIPAL if COLUMNA_TEXTO_PRINCIPAL in df.columns else df.columns[0]
            y_axis = COLUMNA_NUMERICA_PRINCIPAL if COLUMNA_NUMERICA_PRINCIPAL in df.columns else num_cols[0] if num_cols else df.columns[0]
            
            fig_bar = px.bar(df, x=x_axis, y=y_axis, title=f"Distribución de {y_axis} por {x_axis}", color=y_axis, template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            fig_line = px.line(df, x=df.columns[0], y=y_axis, title="Evolución Temporal / Histórica", template="plotly_white")
            st.plotly_chart(fig_line, use_container_width=True)

    # PESTAÑA 2: PREDICTIVO
    with tab2:
        st.header("🔮 Módulo de Predicción Avanzada")
        if len(num_cols) >= 1:
            st.info("🎯 Entrenando modelo de tendencia lineal automático...")
            df_ml = df.dropna().copy()
            df_ml['Index_Temporal'] = range(len(df_ml))
            
            X = df_ml[['Index_Temporal']]
            y = df_ml[num_cols[0]]
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predicción futuros 5 puntos
            futuro_index = np.array([[len(df_ml) + i] for i in range(5)])
            predicciones_futuras = model.predict(futuro_index)
            
            fig_pred = go.Figure()
            fig_pred.add_trace(go.Scatter(y=y.values, mode='lines+markers', name='Histórico Real'))
            fig_pred.add_trace(go.Scatter(x=list(range(len(df_ml), len(df_ml)+5)), y=predicciones_futuras, mode='lines+markers', name='Proyección Predictiva IA', line=dict(dash='dash', color='red')))
            fig_pred.update_layout(title=f"Predicción Automática de Tendencia para: {num_cols[0]}", template="plotly_white")
            st.plotly_chart(fig_pred, use_container_width=True)
        else:
            st.warning("Se necesita definir la columna numérica correctamente en el código para activar la IA.")

    # PESTAÑA 3: DATA
    with tab3:
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"🛑 Error de mapeo: {e}")
