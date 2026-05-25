import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

# 1. CONFIGURACIÓN DE LA PÁGINA (Estilo Corporativo)
st.set_page_config(
    page_title="Control Tower Premium | Parkano Bolivia",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado mediante CSS interno para mejorar la visualización corporativa
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #1e293b; font-family: 'Segoe UI', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Control Tower Premium — Parkano Bolivia")
st.markdown("---")

# 2. CONEXIÓN DE DATOS EN TIEMPO REAL (Auto-actualizable cada 5 minutos)
DATA_URL = "https://docs.google.com/spreadsheets/d/1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns/export?format=csv&gid=158096369"

@st.cache_data(ttl=300) # El dashboard se refresca solo internamente cada 300 segundos
def load_data():
    df = pd.read_csv(DATA_URL)
    # Limpieza automática de columnas vacías
    df = df.dropna(how='all', axis=1)
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()

    # 3. BARRA LATERAL CONTROLES Y FILTROS DINÁMICOS
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1041/1041910.png", width=80)
    st.sidebar.title("Panel de Control")
    
    if st.sidebar.button("🔄 Forzar Actualización Inmediata"):
        st.cache_data.clear()
        st.rerun()

    # Separación automática de tipos de datos
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=[object]).columns.tolist()
    
    st.sidebar.markdown("### 🔍 Filtros Globales")
    # Generar un filtro dinámico si existen columnas categóricas
    if cat_cols:
        filtro_col = st.sidebar.selectbox("Filtrar por columna:", cat_cols)
        opciones = df[filtro_col].unique().tolist()
        seleccion = st.sidebar.multiselect(f"Selecciona valores de {filtro_col}:", opciones, default=opciones)
        df = df[df[filtro_col].isin(seleccion)]

    # 4. DISEÑO DE TABS (PESTAÑAS PROFESIONALES)
    tab1, tab2, tab3 = st.tabs(["📊 Análisis Descriptivo", "🔮 Inteligencia Predictiva", "📋 Base de Datos Activa"])

    # ==========================================
    # PESTAÑA 1: ANÁLISIS DESCRIPTIVO
    # ==========================================
    with tab1:
        st.header("📈 Resumen Estadístico y KPIs")
        
        # Métricas Dinámicas principales
        if num_cols:
            cols_kpi = st.columns(min(len(num_cols), 4))
            for i, col in enumerate(num_cols[:4]):
                with cols_kpi[i]:
                    total = df[col].sum()
                    promedio = df[col].mean()
                    st.metric(label=f"Total {col}", value=f"{total:,.2f}", delta=f"Promedio: {promedio:,.1f}")
        else:
            st.warning("No se encontraron columnas numéricas para calcular KPIs.")

        st.markdown("### 📊 Visualización de Tendencias y Distribuciones")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            if len(num_cols) >= 1 and len(cat_cols) >= 1:
                eje_x = st.selectbox("Eje X (Categoría):", cat_cols, key="x_desc")
                eje_y = st.selectbox("Eje Y (Valor Numérico):", num_cols, key="y_desc")
                
                df_grouped = df.groupby(eje_x)[eje_y].sum().reset_index()
                fig_bar = px.bar(df_grouped, x=eje_x, y=eje_y, title=f"{eje_y} por {eje_x}",
                                 color=eje_y, color_continuous_scale="Viridis", template="plotly_white")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Se requieren columnas numéricas y de texto para gráficos de barra.")

        with col_chart2:
            if len(num_cols) >= 2:
                scat_x = st.selectbox("Correlación Eje X:", num_cols, index=0)
                scat_y = st.selectbox("Correlación Eje Y:", num_cols, index=min(1, len(num_cols)-1))
                
                fig_scat = px.scatter(df, x=scat_x, y=scat_y, trendline="ols",
                                      title=f"Relación y Tendencia: {scat_x} vs {scat_y}", template="plotly_white")
                st.plotly_chart(fig_scat, use_container_width=True)
            else:
                st.info("Se necesitan al menos 2 columnas numéricas para ver correlaciones.")

    # ==========================================
    # PESTAÑA 2: INTELIGENCIA PREDICTIVA (Machine Learning)
    # ==========================================
    with tab2:
        st.header("🔮 Módulo de Predicción Avanzada")
        st.markdown("Este módulo entrena un modelo de Inteligencia Artificial en tiempo real con los datos de tu Excel para predecir tendencias futuras.")

        if len(num_cols) >= 2:
            col_p1, col_p2 = st.columns([1, 2])
            
            with col_p1:
                st.markdown("### 🛠️ Configurar Modelo")
                variable_objetivo = st.selectbox("¿Qué deseas predecir? (Target):", num_cols)
                
                variables_predictoras = [c for c in num_cols if c != variable_objetivo]
                features_seleccionadas = st.multiselect("Variables influyentes (Predictoras):", variables_predictoras, default=variables_predictoras)
                
                algoritmo = st.radio("Algoritmo de IA:", ["Random Forest (Complejo/Preciso)", "Regresión Lineal (Tendencia Simple)"])

            with col_p2:
                if features_seleccionadas:
                    # Preparación de datos para el modelo eliminando filas vacías
                    df_ml = df[[variable_objetivo] + features_seleccionadas].dropna()
                    
                    if len(df_ml) > 5:
                        X = df_ml[features_seleccionadas]
                        y = df_ml[variable_objetivo]
                        
                        # División Entrenamiento / Prueba
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                        
                        # Selección de Modelo
                        if algoritmo == "Regresión Lineal (Tendencia Simple)":
                            model = LinearRegression()
                        else:
                            model = RandomForestRegressor(n_estimators=100, random_state=42)
                            
                        model.fit(X_train, y_train)
                        predicciones = model.predict(X_test)
                        
                        # Métricas de precisión
                        r2 = r2_score(y_test, predicciones)
                        mae = mean_absolute_error(y_test, predicciones)
                        
                        st.markdown(f"### 📊 Rendimiento del Modelo")
                        c_m1, c_m2 = st.columns(2)
                        c_m1.metric("Precisión del Modelo (R²)", f"{max(0, r2)*100:.1f}%")
                        c_m2.metric("Margen de Error Promedio (MAE)", f"{mae:,.2f}")
                        
                        # Gráfico comparativo Real vs Predicción
                        fig_pred = go.Figure()
                        fig_pred.add_trace(go.Scatter(y=y_test.values, mode='markers', name='Valores Reales', marker=dict(color='blue')))
                        fig_pred.add_trace(go.Scatter(y=predicciones, mode='lines+markers', name='Predicción de IA', marker=dict(color='red')))
                        fig_pred.update_layout(title="Simulación: Valores Reales vs Predicciones del Modelo", template="plotly_white")
                        st.plotly_chart(fig_pred, use_container_width=True)
                        
                        # Simulador interactivo de entrada de datos
                        st.markdown("### 🎛️ Simulador de Predicciones en Vivo")
                        st.write("Cambia los valores abajo para calcular una predicción en tiempo real basada en el histórico:")
                        inputs_usuario = {}
                        cols_input = st.columns(len(features_seleccionadas))
                        
                        for idx, feat in enumerate(features_seleccionadas):
                            with cols_input[idx]:
                                val_min = float(X[feat].min())
                                val_max = float(X[feat].max())
                                val_mean = float(X[feat].mean())
                                inputs_usuario[feat] = st.slider(f"{feat}", val_min, val_max, val_mean)
                        
                        df_usuario = pd.DataFrame([inputs_usuario])
                        pred_resultado = model.predict(df_usuario)[0]
                        st.success(f"🔮 **Resultado Estimado de {variable_objetivo}: {pred_resultado:,.2f}**")
                        
                    else:
                        st.error("No hay suficientes filas de datos válidas (mínimo 6) para entrenar la Inteligencia Artificial.")
                else:
                    st.warning("Selecciona al menos una variable predictora para iniciar el análisis.")
        else:
            st.warning("Se necesitan al menos 2 columnas numéricas en tu Excel para habilitar el algoritmo de predicción.")

    # ==========================================
    # PESTAÑA 3: BASE DE DATOS COMPLETA
    # ==========================================
    with tab3:
        st.header("📋 Registros de la Base de Datos")
        st.markdown("Visualización completa de los datos limpios extraídos directamente desde Google Sheets.")
        st.dataframe(df, use_container_width=True)
        
        # Botón de descarga de datos filtrados
        csv_download = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados en CSV",
            data=csv_download,
            file_name="control_tower_data.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"🛑 Error crítico en el Control Tower: {e}")
    st.info("Asegúrate de que las columnas de tu Excel no tengan caracteres extraños en la primera fila y que contenga datos numéricos.")
