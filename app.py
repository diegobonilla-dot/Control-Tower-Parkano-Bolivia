import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Dashboard SSOT — Minera Parkano",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main {background-color: #0B0F1A;}
    .stMetric {background-color: #131B2E; padding: 1rem; border-radius: 8px; border-left: 3px solid #C8A951;}
    .stMetric label {color: #6B7C99 !important; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;}
    .stMetric .css-1wivap2 {color: #E8E0CC !important; font-size: 1.8rem; font-weight: 800;}
    h1, h2, h3 {color: #C8A951 !important;}
    .stTabs [data-baseweb="tab-list"] {gap: 0.5rem;}
    .stTabs [data-baseweb="tab"] {background-color: #131B2E; border-radius: 8px 8px 0 0; color: #6B7C99; padding: 0.75rem 1.5rem;}
    .stTabs [aria-selected="true"] {background-color: #1A2438; color: #C8A951 !important; border-bottom: 2px solid #C8A951;}
</style>
""", unsafe_allow_html=True)

# TU LINK REAL DE GOOGLE SHEETS EN FORMATO CSV
DATA_URL = "https://docs.google.com/spreadsheets/d/1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns/export?format=csv"

@st.cache_data(ttl=300)  # Se actualiza automáticamente cada 5 minutos
def load_data():
    """Carga datos desde Google Sheets"""
    try:
        df = pd.read_csv(DATA_URL)
        
        # Parsear fechas
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        
        # Limpiar columnas numéricas
        numeric_cols = df.columns[1:]
        for col in numeric_cols:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '').str.replace('Bs', '').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# Cargar datos
df = load_data()

# Header
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("# ⛏️ MINERA PARKANO — Dashboard SSOT")
with col2:
    st.metric("Registros Totales", len(df))
with col3:
    ayer = datetime.now() - timedelta(days=1)
    st.metric("Fecha Ref.", ayer.strftime("%d/%m/%Y"))

st.markdown("---")

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Operaciones", "💰 Tesorería", "🔮 Análisis Predictivo", "📋 Datos Completos"])

# ============================================
# TAB 1: OPERACIONES
# ============================================
with tab1:
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_desde = st.date_input("Desde", value=df['Fecha'].min())
    with col2:
        fecha_hasta = st.date_input("Hasta", value=df['Fecha'].max())
    with col3:
        mes_filtro = st.selectbox("Mes", ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo"])
    
    # Aplicar filtros
    df_filtered = df.copy()
    if mes_filtro != "Todos":
        meses = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5}
        df_filtered = df_filtered[df_filtered['Fecha'].dt.month == meses[mes_filtro]]
    
    df_filtered = df_filtered[(df_filtered['Fecha'] >= pd.to_datetime(fecha_desde)) & 
                               (df_filtered['Fecha'] <= pd.to_datetime(fecha_hasta))]
    
    # KPIs
    st.subheader("Indicadores Clave")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        inv_actual = df_filtered['Inventario_Total_Broza_TMH'].iloc[-1]
        st.metric("Inventario Broza (TMH)", f"{inv_actual:,.2f}")
    
    with col2:
        ley_zn_avg = df_filtered['Ley_Zn'].mean()
        ley_zn_last = df_filtered['Ley_Zn'].iloc[-1]
        st.metric("Ley Zn Promedio", f"{ley_zn_avg:.2f}%", 
                  delta=f"Último: {ley_zn_last:.2f}%")
    
    with col3:
        ley_ag_avg = df_filtered['Ley_AG'].mean()
        ley_ag_last = df_filtered['Ley_AG'].iloc[-1]
        st.metric("Ley Ag Promedio", f"{ley_ag_avg:.2f}%",
                  delta=f"Último: {ley_ag_last:.2f}%")
    
    with col4:
        ley_pb_avg = df_filtered['Ley_PB'].mean()
        ley_pb_last = df_filtered['Ley_PB'].iloc[-1]
        st.metric("Ley Pb Promedio", f"{ley_pb_avg:.2f}%",
                  delta=f"Último: {ley_pb_last:.2f}%")
    
    with col5:
        total_ingreso = df_filtered['Ingreso_Broza_TMH'].sum()
        st.metric("Total Ingreso (TMH)", f"{total_ingreso:,.0f}")
    
    with col6:
        tmh_proc = df_filtered['TMH_Procesadas_dia'].sum()
        st.metric("TMH Procesadas", f"{tmh_proc:,.0f}")
    
    # Alertas
    if inv_actual < 500:
        st.error(f"⚠️ **Inventario Crítico** — Inv. Broza = {inv_actual:,.2f} TMH (umbral mínimo: 500 TMH)")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Inventario Broza (TMH)")
        fig1 = px.line(df_filtered, x='Fecha', y='Inventario_Total_Broza_TMH',
                       color_discrete_sequence=['#C8A951'])
        fig1.update_layout(plot_bgcolor='#131B2E', paper_bgcolor='#131B2E',
                          font_color='#6B7C99', height=300)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Leyes Zn / Ag / Pb (%)")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_filtered['Fecha'], y=df_filtered['Ley_Zn'],
                                  name='Zn%', line=dict(color='#4A9B8E')))
        fig2.add_trace(go.Scatter(x=df_filtered['Fecha'], y=df_filtered['Ley_AG'],
                                  name='Ag%', line=dict(color='#C8A951')))
        fig2.add_trace(go.Scatter(x=df_filtered['Fecha'], y=df_filtered['Ley_PB'],
                                  name='Pb%', line=dict(color='#8B6FA6')))
        fig2.update_layout(plot_bgcolor='#131B2E', paper_bgcolor='#131B2E',
                          font_color='#6B7C99', height=300)
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Ingreso Broza Diario (TMH)")
        fig3 = px.bar(df_filtered, x='Fecha', y='Ingreso_Broza_TMH',
                      color_discrete_sequence=['#4A9B8E'])
        fig3.update_layout(plot_bgcolor='#131B2E', paper_bgcolor='#131B2E',
                          font_color='#6B7C99', height=300)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        st.subheader("TMH Procesadas por Día")
        fig4 = px.bar(df_filtered, x='Fecha', y='TMH_Procesadas_dia',
                      color_discrete_sequence=['#8B6FA6'])
        fig4.update_layout(plot_bgcolor='#131B2E', paper_bgcolor='#131B2E',
                          font_color='#6B7C99', height=300)
        st.plotly_chart(fig4, use_container_width=True)

# ============================================
# TAB 2: TESORERÍA
# ============================================
with tab2:
    st.subheader("Indicadores Tesorería")
    # Aquí añade las columnas de tesorería cuando estén disponibles en tu Sheet
    st.info("🚧 Sección de Tesorería — Requiere datos de la hoja 'Tesorería' del Google Sheet")

# ============================================
# TAB 3: ANÁLISIS PREDICTIVO
# ============================================
with tab3:
    st.subheader("🔮 Análisis Predictivo — Regresión Lineal")
    
    # Regresión lineal
    from sklearn.linear_model import LinearRegression
    
    X = np.arange(len(df_filtered)).reshape(-1, 1)
    y = df_filtered['Inventario_Total_Broza_TMH'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    r2 = model.score(X, y)
    slope = model.coef_[0]
    intercept = model.intercept_
    
    proy_30 = slope * 30
    
    # Resultados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Regresión Lineal — Inventario Broza")
        st.metric("Ecuación", f"y = {slope:.4f}x + {intercept:.2f}")
        st.metric("R² (bondad ajuste)", f"{r2*100:.1f}%")
        st.metric("Pendiente", f"{slope:+.2f} TMH/día")
        st.metric("Proyección +30 días", f"{proy_30:+.2f} TMH")
        
        tendencia = "↗ CRECIENTE" if slope > 0 else "↘ DECRECIENTE"
        st.info(f"**Tendencia:** {tendencia}")
    
    with col2:
        st.markdown("### Estadísticas Descriptivas")
        st.metric("Media Inv. Broza", f"{y.mean():.2f} TMH")
        st.metric("Máximo", f"{y.max():.2f} TMH")
        st.metric("Mínimo", f"{y.min():.2f} TMH")
        st.metric("Desviación Estándar", f"{y.std():.2f} TMH")
    
    # Gráfico regresión
    st.subheader("Inventario Real vs Tendencia Lineal")
    fig_reg = go.Figure()
    fig_reg.add_trace(go.Scatter(x=df_filtered['Fecha'], y=y, name='Real',
                                 line=dict(color='#C8A951')))
    fig_reg.add_trace(go.Scatter(x=df_filtered['Fecha'], y=y_pred, name='Tendencia',
                                 line=dict(color='#FF4D6D', dash='dash')))
    fig_reg.update_layout(plot_bgcolor='#131B2E', paper_bgcolor='#131B2E',
                         font_color='#6B7C99', height=400)
    st.plotly_chart(fig_reg, use_container_width=True)

# ============================================
# TAB 4: DATOS COMPLETOS
# ============================================
with tab4:
    st.subheader("📋 Tabla de Datos Operaciones")
    st.dataframe(df_filtered, use_container_width=True, height=500)
    
    # Botón de descarga
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f'parkano_datos_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )

# Footer
st.markdown("---")
st.caption(f"📊 Dashboard SSOT — Minera Parkano | Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df)} registros totales")
