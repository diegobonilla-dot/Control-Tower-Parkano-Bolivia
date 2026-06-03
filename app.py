import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import requests
import io

st.set_page_config(page_title="Dashboard SSOT — Minera Parkano", page_icon="⛏️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#0B0F1A,#131B2E)}
[data-testid="stHeader"]{background:transparent}
.stMetric{background:linear-gradient(135deg,#131B2E,#1A2438);padding:1.2rem;border-radius:10px;border-left:3px solid #C8A951;box-shadow:0 4px 6px rgba(0,0,0,.3)}
.stMetric label{color:#6B7C99!important;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700}
.stMetric [data-testid="stMetricValue"]{color:#E8E0CC!important;font-size:1.5rem;font-weight:800}
.stMetric [data-testid="stMetricDelta"]{font-size:.75rem}
h1{color:#C8A951!important;font-weight:800}
h2,h3,h4{color:#C8A951!important;font-weight:700}
.stTabs [data-baseweb="tab-list"]{gap:.5rem;background:#131B2E;padding:.5rem;border-radius:10px}
.stTabs [data-baseweb="tab"]{background:#1A2438;border-radius:8px;color:#6B7C99;padding:.75rem 1.5rem;font-weight:600;border:none}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#C8A951,#9A7D2E);color:#0B0F1A!important}
</style>
""", unsafe_allow_html=True)

SHEET_ID = "1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns"
URL_OPS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=158096369"
URL_TESO = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

def conv(val):
    """Convierte numeros bolivianos: 5.971,56 -> 5971.56 / Bs700.000,00 -> 700000"""
    if pd.isna(val): return np.nan
    if isinstance(val, (int, float)): return float(val)
    s = str(val).strip().replace('Bs','').replace('%','').replace('\xa0','').strip()
    if not s or s in ('-','#DIV/0!','#VALUE!','#REF!','#N/A'): return np.nan
    s = s.replace('.','').replace(',','.')
    try: return float(s)
    except: return np.nan

def smart_read_csv(url):
    """Lee CSV detectando separador automaticamente"""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        text = resp.text
        # Detectar separador: si la primera linea tiene ; probablemente es ;
        first_line = text.split('\n')[0]
        if first_line.count(';') > first_line.count(','):
            sep = ';'
        else:
            sep = ','
        df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_ops():
    raw = smart_read_csv(URL_OPS)
    if raw.empty: return raw
    # Renombrar por posicion para evitar problemas de nombres
    expected = ['Fecha','Ingreso_Broza','Inventario_Broza','Ley_Zn','Ley_Ag','Ley_Pb',
                'Inv_CC_Zn','Inv_CC_Pb','TMH_Proc']
    # Usar los primeros 9 cols
    cols = list(raw.columns[:min(9, len(raw.columns))])
    df = raw[cols].copy()
    rename = {}
    for i, name in enumerate(expected[:len(cols)]):
        rename[cols[i]] = name
    df = df.rename(columns=rename)
    # Parsear fecha
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
    # Convertir numericas
    for c in df.columns:
        if c != 'Fecha':
            df[c] = df[c].apply(conv)
    df = df.dropna(subset=['Fecha']).reset_index(drop=True)
    return df

@st.cache_data(ttl=300)
def load_teso():
    raw = smart_read_csv(URL_TESO)
    if raw.empty: return raw
    expected = ['Fecha','Bancos','Caja','CxC_Vig','CxC_Ven','CxP_Gen','CxP_Min']
    cols = list(raw.columns[:min(7, len(raw.columns))])
    df = raw[cols].copy()
    rename = {}
    for i, name in enumerate(expected[:len(cols)]):
        rename[cols[i]] = name
    df = df.rename(columns=rename)
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
    for c in df.columns:
        if c != 'Fecha':
            df[c] = df[c].apply(conv)
    df = df.dropna(subset=['Fecha']).reset_index(drop=True)
    return df

# ── Cargar ──
df_ops = load_ops()
df_teso = load_teso()

if df_ops.empty:
    st.error("⚠️ No se pudieron cargar datos. Verifica conexión.")
    st.stop()

# ── HEADER ──
c1,c2,c3 = st.columns([3,1,1])
with c1: st.markdown("# ⛏️ MINERA PARKANO — Dashboard SSOT")
with c2: st.metric("📊 Registros", len(df_ops))
with c3: st.metric("📅 Ref.", (datetime.now()-timedelta(days=1)).strftime("%d/%m/%Y"))
st.markdown("---")

# ── Filtros ──
c1,c2,c3 = st.columns(3)
with c1: f_desde = st.date_input("Desde", value=df_ops['Fecha'].min().date())
with c2: f_hasta = st.date_input("Hasta", value=df_ops['Fecha'].max().date())
with c3:
    meses = {"Todos":0,"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6}
    mes_sel = st.selectbox("Mes", list(meses.keys()))

df_f = df_ops[(df_ops['Fecha']>=pd.to_datetime(f_desde))&(df_ops['Fecha']<=pd.to_datetime(f_hasta))].copy()
if mes_sel != "Todos":
    df_f = df_f[df_f['Fecha'].dt.month == meses[mes_sel]]
df_f = df_f.reset_index(drop=True)

if len(df_f) == 0:
    st.warning("Sin datos para el rango seleccionado")
    st.stop()

# ── TABS ──
tab1,tab2,tab3,tab4 = st.tabs(["📊 Operaciones","💰 Tesorería","🔮 Predictivo","📋 Datos"])
plot_cfg = dict(plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',font_color='#6B7C99',height=300,margin=dict(l=0,r=0,t=30,b=0))

# ─── TAB 1 ───
with tab1:
    st.markdown("### Indicadores Clave")
    inv_s = df_f['Inventario_Broza'].dropna()
    zn_s = df_f['Ley_Zn'].dropna()
    ag_s = df_f['Ley_Ag'].dropna()
    pb_s = df_f['Ley_Pb'].dropna()
    ing_s = df_f['Ingreso_Broza'].dropna()
    tmh_s = df_f['TMH_Proc'].dropna()

    last_inv = float(inv_s.iloc[-1]) if len(inv_s)>0 else 0
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: st.metric("Inv. Broza (TMH)", f"{last_inv:,.2f}")
    with c2: st.metric("Ley Zn Prom.", f"{zn_s.mean():.2f}%" if len(zn_s)>0 else "—")
    with c3: st.metric("Ley Ag Prom.", f"{ag_s.mean():.2f}%" if len(ag_s)>0 else "—")
    with c4: st.metric("Ley Pb Prom.", f"{pb_s.mean():.2f}%" if len(pb_s)>0 else "—")
    with c5: st.metric("Total Ingreso", f"{ing_s.sum():,.0f} TMH")
    with c6: st.metric("TMH Procesadas", f"{tmh_s.sum():,.0f}")

    if last_inv < 500:
        st.error(f"⚠️ **Inventario Crítico** — {last_inv:,.2f} TMH (umbral: 500 TMH)")
    st.markdown("---")

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Inventario Broza (TMH)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_f['Fecha'],y=df_f['Inventario_Broza'],fill='tozeroy',line=dict(color='#C8A951',width=2),fillcolor='rgba(200,169,81,0.15)',name='Inv'))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Leyes Zn / Ag / Pb (%)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_f['Fecha'],y=df_f['Ley_Zn'],name='Zn%',line=dict(color='#4A9B8E',width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'],y=df_f['Ley_Ag'],name='Ag%',line=dict(color='#C8A951',width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'],y=df_f['Ley_Pb'],name='Pb%',line=dict(color='#8B6FA6',width=2)))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)

    c3,c4 = st.columns(2)
    with c3:
        st.markdown("#### Ingreso Broza Diario")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_f['Fecha'],y=df_f['Ingreso_Broza'],marker_color='#4A9B8E',name='Ingreso'))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.markdown("#### TMH Procesadas / Día")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_f['Fecha'],y=df_f['TMH_Proc'],marker_color='#8B6FA6',name='TMH'))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)

# ─── TAB 2 ───
with tab2:
    if df_teso.empty:
        st.warning("⚠️ Sin datos de Tesorería")
    else:
        st.markdown("### Tesorería")
        b_s = df_teso['Bancos'].dropna()
        c_s = df_teso['Caja'].dropna()
        cxc_s = df_teso['CxC_Vig'].dropna()
        cxp_s = df_teso['CxP_Min'].dropna()
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("💰 Bancos", f"Bs {float(b_s.iloc[-1]):,.0f}" if len(b_s)>0 else "—")
        with c2: st.metric("🏦 Caja", f"Bs {float(c_s.iloc[-1]):,.0f}" if len(c_s)>0 else "—")
        with c3: st.metric("📈 CxC Vigente", f"Bs {float(cxc_s.iloc[-1]):,.0f}" if len(cxc_s)>0 else "—")
        with c4: st.metric("📉 CxP Mineral", f"Bs {float(cxp_s.iloc[-1]):,.0f}" if len(cxp_s)>0 else "—")
        st.markdown("---")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("#### Bancos & Caja")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_teso['Fecha'],y=df_teso['Bancos'],name='Bancos',line=dict(color='#3DDC84',width=2)))
            fig.add_trace(go.Scatter(x=df_teso['Fecha'],y=df_teso['Caja'],name='Caja',line=dict(color='#C8A951',width=2)))
            fig.update_layout(**plot_cfg)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### CxC vs CxP")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_teso['Fecha'],y=df_teso['CxC_Vig'],name='CxC',line=dict(color='#3DDC84',width=2)))
            fig.add_trace(go.Scatter(x=df_teso['Fecha'],y=df_teso['CxP_Min'],name='CxP',line=dict(color='#FF4D6D',width=2)))
            fig.update_layout(**plot_cfg)
            st.plotly_chart(fig, use_container_width=True)

# ─── TAB 3 ───
with tab3:
    st.markdown("### 🔮 Análisis Predictivo")
    inv_clean = df_f['Inventario_Broza'].dropna()
    if len(inv_clean) > 2:
        X = np.arange(len(inv_clean)).astype(float)
        y = inv_clean.values.astype(float)
        n = len(X)
        slope = (n*(X*y).sum()-X.sum()*y.sum())/(n*(X**2).sum()-X.sum()**2)
        intercept = (y.sum()-slope*X.sum())/n
        y_pred = slope*X+intercept
        ss_t = ((y-y.mean())**2).sum()
        r2 = 1-((y-y_pred)**2).sum()/ss_t if ss_t>0 else 0

        c1,c2 = st.columns(2)
        with c1:
            st.metric("Ecuación", f"y = {slope:.4f}x + {intercept:.2f}")
            st.metric("R²", f"{r2*100:.1f}%")
            st.metric("Pendiente", f"{slope:+.2f} TMH/día")
            st.metric("Proy. +30d", f"{slope*30:+.0f} TMH")
            t = "↗ CRECIENTE" if slope>0 else "↘ DECRECIENTE"
            st.markdown(f"**Tendencia:** :{'green' if slope>0 else 'red'}[{t}]")
        with c2:
            st.metric("Media", f"{y.mean():,.2f} TMH")
            st.metric("Máximo", f"{y.max():,.2f} TMH")
            st.metric("Mínimo", f"{y.min():,.2f} TMH")
            st.metric("Desv. Est.", f"{y.std():,.2f} TMH")

        fig = go.Figure()
        fechas = df_f.loc[inv_clean.index,'Fecha']
        fig.add_trace(go.Scatter(x=fechas,y=y,name='Real',line=dict(color='#C8A951',width=2),fill='tozeroy',fillcolor='rgba(200,169,81,0.1)'))
        fig.add_trace(go.Scatter(x=fechas,y=y_pred,name='Tendencia',line=dict(color='#FF4D6D',width=3,dash='dash')))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',font_color='#6B7C99',height=400)
        st.plotly_chart(fig, use_container_width=True)

# ─── TAB 4 ───
with tab4:
    st.markdown("### 📋 Datos")
    st.dataframe(df_f, use_container_width=True, height=500)
    csv = df_f.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV",data=csv,file_name=f'parkano_{datetime.now().strftime("%Y%m%d")}.csv',mime='text/csv')

st.markdown("---")
st.caption(f"⛏️ Minera Parkano | {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df_ops)} reg | Auto-refresh 5 min")
