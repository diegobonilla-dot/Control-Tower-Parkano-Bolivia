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
    initial_sidebar_state="collapsed"
)

# CSS mejorado
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0B0F1A 0%, #131B2E 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    .stMetric {
        background: linear-gradient(135deg, #131B2E, #1A2438);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 3px solid #C8A951;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stMetric label {
        color: #6B7C99 !important;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #E8E0CC !important;
        font-size: 1.6rem;
        font-weight: 800;
    }
    .stMetric [data-testid="stMetricDelta"] {
        color: #3DDC84 !important;
        font-size: 0.75rem;
    }
    h1 {
        color: #C8A951 !important;
        font-weight: 800;
        letter-spacing: 0.02em;
    }
    h2, h3 {
        color: #C8A951 !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #131B2E;
        padding: 0.5rem;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1A2438;
        border-radius: 8px;
        color: #6B7C99;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #C8A951, #9A7D2E);
        color: #0B0F1A !important;
    }
    .stSelectbox > div > div {
        background: #1A2438;
        color: #E8E0CC;
        border: 1px solid #C8A951;
    }
    .stDateInput > div > div > input {
        background: #1A2438;
        color: #E8E0CC;
        border: 1px solid #C8A951;
    }
    div[data-testid="stDataFrame"] {
        background: #131B2E;
    }
</style>
""", unsafe_allow_html=True)

# URL de Google Sheets
DATA_URL = "https://docs.google.com/spreadsheets/d/1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    """Carga datos desde Google Sheets con manejo robusto de errores"""
    try:
        df = pd.read_csv(DATA_URL)
        
        # Detectar si hay columnas de tesorería (empiezan con "Bs")
        # Por ahora solo trabajamos con columnas de operaciones
        
        # Parsear fechas
        df['Fecha'] = pd.to_datetime(df.iloc[:, 0], format='%d/%m/%Y', errors='coerce')
        
        # Renombrar columnas para facilitar acceso
        df.columns = [
            'Fecha', 'Ingreso_Broza_TMH', 'Inventario_Total_Broza_TMH',
            'Ley_Zn', 'Ley_AG', 'Ley_PB', 'Inventario_CC_Zn',
            'Inventario_CC_Pb', 'TMH_Procesadas_dia', 'Ley_Feed_ZN',
            'Ley_Feed_AG', 'Ley_Feed_PB', 'Ley_Analisis_ZN',
            'Ley_Analisis_AG', 'Ley_Analisis_PB', 'Desviacion_Zn',
            'Desviacion_AG', 'Desviacion_Pb'
        ][:len(df.columns)]
        
        # Limpiar columnas numéricas
        for col in df.columns[1:]:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('Bs', '').str.replace('%', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Eliminar filas con fechas inválidas
        df = df.dropna(subset=['Fecha'])
        
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return pd.DataFrame()

# Cargar datos
with st.spinner("🔄 Cargando datos desde Google Sheets..."):
    df = load_data()

if df.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica la URL del Google Sheet.")
    st.stop()

# ============================================
# HEADER
# ============================================
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.markdown("# ⛏️ MINERA PARKANO — Dashboard SSOT")
with col2:
    st.metric("📊 Registros Totales", len(df))
with col3:
    fecha_ref = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    st.metric("📅 Fecha Ref.", fecha_ref)

st.markdown("---")

# ============================================
# TABS
# ============================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Operaciones", "💰 Tesorería", "🔮 Análisis Predictivo", "📋 Datos Completos"])

# ============================================
# TAB 1: OPERACIONES
# ============================================
with tab1:
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_desde = st.date_input("Desde", value=df['Fecha'].min().date())
    with col2:
        fecha_hasta = st.date_input("Hasta", value=df['Fecha'].max().date())
    with col3:
        meses_dict = {
            "Todos": None, "Enero": 1, "Febrero": 2, "Marzo": 3,
            "Abril": 4, "Mayo": 5, "Junio": 6, "Julio": 7,
            "Agosto": 8, "Septiembre": 9, "Octubre": 10,
            "Noviembre": 11, "Diciembre": 12
        }
        mes_filtro = st.selectbox("Mes", list(meses_dict.keys()))
    
    # Aplicar filtros
    df_filtered = df.copy()
    df_filtered = df_filtered[
        (df_filtered['Fecha'] >= pd.to_datetime(fecha_desde)) &
        (df_filtered['Fecha'] <= pd.to_datetime(fecha_hasta))
    ]
    
    if mes_filtro != "Todos":
        df_filtered = df_filtered[df_filtered['Fecha'].dt.month == meses_dict[mes_filtro]]
    
    st.markdown("### Indicadores Clave")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    ultimo = df_filtered.iloc[-1]
    
    with col1:
        st.metric(
            "Inventario Broza (TMH)",
            f"{ultimo['Inventario_Total_Broza_TMH']:,.2f}"
        )
    
    with col2:
        ley_zn_avg = df_filtered['Ley_Zn'].mean()
        st.metric(
            "Ley Zn Promedio",
            f"{ley_zn_avg:.2f}%",
            delta=f"Último: {ultimo['Ley_Zn']:.2f}%"
        )
    
    with col3:
        ley_ag_avg = df_filtered['Ley_AG'].mean()
        st.metric(
            "Ley Ag Promedio",
            f"{ley_ag_avg:.2f}%",
            delta=f"Último: {ultimo['Ley_AG']:.2f}%"
        )
    
    with col4:
        ley_pb_avg = df_filtered['Ley_PB'].mean()
        st.metric(
            "Ley Pb Promedio",
            f"{ley_pb_avg:.2f}%",
            delta=f"Último: {ultimo['Ley_PB']:.2f}%"
        )
    
    with col5:
        total_ingreso = df_filtered['Ingreso_Broza_TMH'].sum()
        st.metric(
            "Total Ingreso (TMH)",
            f"{total_ingreso:,.0f}"
        )
    
    with col6:
        tmh_proc = df_filtered['TMH_Procesadas_dia'].sum()
        st.metric(
            "TMH Procesadas",
            f"{tmh_proc:,.0f}"
        )
    
    # Alerta
    if ultimo['Inventario_Total_Broza_TMH'] < 500:
        st.error(f"⚠️ **Inventario Crítico** — {ultimo['Inventario_Total_Broza_TMH']:,.2f} TMH (umbral: 500 TMH)")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Inventario Broza (TMH)")
        fig1 = px.area(
            df_filtered,
            x='Fecha',
            y='Inventario_Total_Broza_TMH',
            color_discrete_sequence=['#C8A951']
        )
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#6B7C99',
            height=300,
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.markdown("#### Leyes Zn / Ag / Pb (%)")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_filtered['Fecha'],
            y=df_filtered['Ley_Zn'],
            name='Zn%',
            line=dict(color='#4A9B8E', width=2)
        ))
        fig2.add_trace(go.Scatter(
            x=df_filtered['Fecha'],
            y=df_filtered['Ley_AG'],
            name='Ag%',
            line=dict(color='#C8A951', width=2)
        ))
        fig2.add_trace(go.Scatter(
            x=df_filtered['Fecha'],
            y=df_filtered['Ley_PB'],
            name='Pb%',
            line=dict(color='#8B6FA6', width=2)
        ))
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#6B7C99',
            height=300,
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Ingreso Broza Diario (TMH)")
        fig3 = px.bar(
            df_filtered,
            x='Fecha',
            y='Ingreso_Broza_TMH',
            color_discrete_sequence=['#4A9B8E']
        )
        fig3.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#6B7C99',
            height=300,
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        st.markdown("#### TMH Procesadas por Día")
        fig4 = px.bar(
            df_filtered,
            x='Fecha',
            y='TMH_Procesadas_dia',
            color_discrete_sequence=['#8B6FA6']
        )
        fig4.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#6B7C99',
            height=300,
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig4, use_container_width=True)

# ============================================
# TAB 2: TESORERÍA
# ============================================
with tab2:
    st.info("🚧 **Sección de Tesorería** — Requiere datos de la segunda hoja del Google Sheet")
    st.markdown("""
    Para activar esta sección, necesitas:
    1. Tener una segunda hoja en tu Google Sheet llamada "Tesorería"
    2. Exportar esa hoja como CSV separado
    3. Actualizar el código para cargar ambas hojas
    """)

# ============================================
# TAB 3: ANÁLISIS PREDICTIVO
# ============================================
with tab3:
    st.markdown("### 🔮 Regresión Lineal — Inventario Broza")
    
    # Regresión manual (sin sklearn)
    X = np.arange(len(df_filtered))
    y = df_filtered['Inventario_Total_Broza_TMH'].values
    
    # Cálculo manual de regresión lineal
    n = len(X)
    sum_x = X.sum()
    sum_y = y.sum()
    sum_xy = (X * y).sum()
    sum_x2 = (X ** 2).sum()
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n
    
    y_pred = slope * X + intercept
    
    # R²
    y_mean = y.mean()
    ss_tot = ((y - y_mean) ** 2).sum()
    ss_res = ((y - y_pred) ** 2).sum()
    r2 = 1 - (ss_res / ss_tot)
    
    proy_30 = slope * 30
    
    # Resultados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Regresión Lineal")
        st.metric("Ecuación", f"y = {slope:.4f}x + {intercept:.2f}")
        st.metric("R² (bondad ajuste)", f"{r2*100:.1f}%")
        st.metric("Pendiente", f"{slope:+.2f} TMH/día")
        st.metric("Proyección +30 días", f"{proy_30:+.2f} TMH")
        
        tendencia = "↗ CRECIENTE" if slope > 0 else "↘ DECRECIENTE"
        color = "green" if slope > 0 else "red"
        st.markdown(f"**Tendencia:** :{color}[{tendencia}]")
    
    with col2:
        st.markdown("#### Estadísticas Descriptivas")
        st.metric("Media", f"{y.mean():,.2f} TMH")
        st.metric("Máximo", f"{y.max():,.2f} TMH")
        st.metric("Mínimo", f"{y.min():,.2f} TMH")
        st.metric("Desv. Estándar", f"{y.std():,.2f} TMH")
        st.metric("Registros", f"{len(df_filtered)} días")
    
    # Gráfico
    st.markdown("#### Inventario Real vs Tendencia Lineal")
    fig_reg = go.Figure()
    fig_reg.add_trace(go.Scatter(
        x=df_filtered['Fecha'],
        y=y,
        name='Real',
        line=dict(color='#C8A951', width=2),
        fill='tozeroy',
        fillcolor='rgba(200, 169, 81, 0.1)'
    ))
    fig_reg.add_trace(go.Scatter(
        x=df_filtered['Fecha'],
        y=y_pred,
        name='Tendencia',
        line=dict(color='#FF4D6D', width=3, dash='dash')
    ))
    fig_reg.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6B7C99',
        height=400,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_reg, use_container_width=True)

# ============================================
# TAB 4: DATOS COMPLETOS
# ============================================
with tab4:
    st.markdown("### 📋 Tabla de Datos — Operaciones")
    
    # Mostrar tabla
    st.dataframe(
        df_filtered.style.format({
            'Inventario_Total_Broza_TMH': '{:,.2f}',
            'Ingreso_Broza_TMH': '{:,.2f}',
            'Ley_Zn': '{:.2f}%',
            'Ley_AG': '{:.2f}%',
            'Ley_PB': '{:.2f}%'
        }),
        use_container_width=True,
        height=500
    )
    
    # Descarga
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv,
        file_name=f'parkano_ops_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
        mime='text/csv',
    )

# Footer
st.markdown("---")
st.caption(f"📊 Dashboard SSOT — Minera Parkano | Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | {len(df)} registros totales | Auto-refresh cada 5 minutos")
