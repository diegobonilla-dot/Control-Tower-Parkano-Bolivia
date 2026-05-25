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
    [data-testid="stAppViewContainer"] {background: linear-gradient(135deg, #0B0F1A 0%, #131B2E 100%);}
    [data-testid="stHeader"] {background: transparent;}
    .stMetric {background: linear-gradient(135deg, #131B2E, #1A2438);padding: 1.2rem;border-radius: 10px;border-left: 3px solid #C8A951;box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
    .stMetric label {color: #6B7C99 !important;font-size: 0.7rem;text-transform: uppercase;letter-spacing: 0.1em;font-weight: 700;}
    .stMetric [data-testid="stMetricValue"] {color: #E8E0CC !important;font-size: 1.6rem;font-weight: 800;}
    .stMetric [data-testid="stMetricDelta"] {color: #3DDC84 !important;font-size: 0.75rem;}
    h1 {color: #C8A951 !important;font-weight: 800;letter-spacing: 0.02em;}
    h2, h3 {color: #C8A951 !important;font-weight: 700;}
    .stTabs [data-baseweb="tab-list"] {gap: 0.5rem;background: #131B2E;padding: 0.5rem;border-radius: 10px;}
    .stTabs [data-baseweb="tab"] {background: #1A2438;border-radius: 8px;color: #6B7C99;padding: 0.75rem 1.5rem;font-weight: 600;border: none;}
    .stTabs [aria-selected="true"] {background: linear-gradient(135deg, #C8A951, #9A7D2E);color: #0B0F1A !important;}
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns"
URL_OPERACIONES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=158096369"
URL_TESORERIA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

def limpiar_numero(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    valor_str = str(valor).replace('Bs', '').replace(',', '').replace(' ', '').strip()
    try: return float(valor_str)
    except: return 0.0

@st.cache_data(ttl=300)
def load_operaciones():
    try:
        df = pd.read_csv(URL_OPERACIONES)
        # Limpiar nombres de columnas (quitar espacios extra)
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        
        # Mapeo de columnas
        col_map = {
            'Ingreso_Broza_TMH': 'Ingreso_Broza_TMH',
            'Inventario_Total_Broza_TMH': 'Inventario_Total_Broza_TMH',
            'Ley_Zn': 'Ley_Zn',
            'Ley_AG': 'Ley_AG',
            'Ley_PB': 'Ley_PB',
            'Inventario_CC_Zn': 'Inventario_CC_Zn',
            'Inventario_CC_Pb': 'Inventario_CC_Pb',
            'TMH_Procesadas_dia': 'TMH_Procesadas_dia'
        }
        
        for col in col_map.values():
            if col in df.columns:
                df[col] = df[col].apply(limpiar_numero)
        
        df = df.dropna(subset=['Fecha']).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_tesoreria():
    try:
        df = pd.read_csv(URL_TESORERIA)
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        
        cols = ['Efectivo_en_Bancos', 'Caja_Central_Mineral', 'CxC_Vigente', 'CxC_Vencidos', 'CxP_Mineral']
        for col in cols:
            if col in df.columns:
                df[col] = df[col].apply(limpiar_numero)
        
        df = df.dropna(subset=['Fecha']).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return pd.DataFrame()

with st.spinner("🔄 Cargando..."):
    df_ops = load_operaciones()
    df_teso = load_tesoreria()

if df_ops.empty:
    st.error("⚠️ No se pudieron cargar los datos")
    st.stop()

# HEADER
col1, col2, col3 = st.columns([3, 1, 1])
with col1: st.markdown("# ⛏️ MINERA PARKANO — Dashboard SSOT")
with col2: st.metric("📊 Registros", len(df_ops))
with col3: st.metric("📅 Ref.", (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y"))

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Operaciones", "💰 Tesorería", "🔮 Análisis Predictivo", "📋 Datos"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1: fecha_desde = st.date_input("Desde", value=df_ops['Fecha'].min().date())
    with col2: fecha_hasta = st.date_input("Hasta", value=df_ops['Fecha'].max().date())
    with col3: mes_filtro = st.selectbox("Mes", ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo"])
    
    df_f = df_ops[(df_ops['Fecha'] >= pd.to_datetime(fecha_desde)) & (df_ops['Fecha'] <= pd.to_datetime(fecha_hasta))].reset_index(drop=True)
    if mes_filtro != "Todos":
        meses = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5}
        df_f = df_f[df_f['Fecha'].dt.month == meses[mes_filtro]].reset_index(drop=True)
    
    if len(df_f) == 0:
        st.warning("⚠️ Sin datos")
        st.stop()
    
    st.markdown("### Indicadores")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1: st.metric("Inv. Broza (TMH)", f"{float(df_f['Inventario_Total_Broza_TMH'].iloc[-1]):,.2f}")
    with col2: st.metric("Ley Zn", f"{df_f['Ley_Zn'].mean():.2f}%")
    with col3: st.metric("Ley Ag", f"{df_f['Ley_AG'].mean():.2f}%")
    with col4: st.metric("Ley Pb", f"{df_f['Ley_PB'].mean():.2f}%")
    with col5: st.metric("Total Ingreso", f"{df_f['Ingreso_Broza_TMH'].sum():,.0f}")
    with col6: st.metric("TMH Proc.", f"{df_f['TMH_Procesadas_dia'].sum():,.0f}")
    
    if float(df_f['Inventario_Total_Broza_TMH'].iloc[-1]) < 500:
        st.error(f"⚠️ Inventario Crítico: {float(df_f['Inventario_Total_Broza_TMH'].iloc[-1]):,.2f} TMH")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Inventario Broza")
        fig = px.area(df_f, x='Fecha', y='Inventario_Total_Broza_TMH', color_discrete_sequence=['#C8A951'])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#6B7C99', height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Leyes")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Zn'], name='Zn%', line=dict(color='#4A9B8E', width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_AG'], name='Ag%', line=dict(color='#C8A951', width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_PB'], name='Pb%', line=dict(color='#8B6FA6', width=2)))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#6B7C99', height=300)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    if df_teso.empty:
        st.warning("⚠️ Sin datos de Tesorería")
    else:
        st.markdown("### Tesorería")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("💰 Bancos", f"Bs {float(df_teso['Efectivo_en_Bancos'].iloc[-1]):,.0f}")
        with col2: st.metric("🏦 Caja", f"Bs {float(df_teso['Caja_Central_Mineral'].iloc[-1]):,.0f}")
        with col3: st.metric("📈 CxC", f"Bs {float(df_teso['CxC_Vigente'].iloc[-1]):,.0f}")
        with col4: st.metric("📉 CxP", f"Bs {float(df_teso['CxP_Mineral'].iloc[-1]):,.0f}")

with tab3:
    st.markdown("### 🔮 Análisis Predictivo")
    X = np.arange(len(df_f))
    y = df_f['Inventario_Total_Broza_TMH'].values
    n = len(X)
    slope = (n*(X*y).sum() - X.sum()*y.sum()) / (n*(X**2).sum() - X.sum()**2)
    intercept = (y.sum() - slope*X.sum()) / n
    y_pred = slope*X + intercept
    r2 = 1 - ((y - y_pred)**2).sum() / ((y - y.mean())**2).sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ecuación", f"y = {slope:.4f}x + {intercept:.2f}")
        st.metric("R²", f"{r2*100:.1f}%")
    with col2:
        st.metric("Pendiente", f"{slope:+.2f} TMH/día")
        st.metric("Proy. +30d", f"{slope*30:+.2f} TMH")

with tab4:
    st.markdown("### Datos Completos")
    st.dataframe(df_f[['Fecha', 'Ingreso_Broza_TMH', 'Inventario_Total_Broza_TMH', 'Ley_Zn', 'Ley_AG', 'Ley_PB']], height=500)

st.markdown("---")
st.caption(f"📊 Minera Parkano | {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df_ops)} reg | Auto-refresh 5min")
