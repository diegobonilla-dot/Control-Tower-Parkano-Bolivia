import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Dashboard SSOT — Minera Parkano", page_icon="⛏️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#0B0F1A,#131B2E)}
[data-testid="stHeader"]{background:transparent}
.stMetric{background:linear-gradient(135deg,#131B2E,#1A2438);padding:1rem 1.2rem;border-radius:10px;border-left:3px solid #C8A951;box-shadow:0 4px 6px rgba(0,0,0,.3)}
.stMetric label{color:#6B7C99!important;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.stMetric [data-testid="stMetricValue"]{color:#E8E0CC!important;font-size:1.4rem;font-weight:800}
.stMetric [data-testid="stMetricDelta"]{font-size:.72rem}
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
    """Numeros bolivianos: 5.971,56 -> 5971.56 / Bs700.000,00 -> 700000"""
    if pd.isna(val): return np.nan
    if isinstance(val, (int, float)): return float(val)
    s = str(val).strip().replace('Bs', '').replace('%', '').replace('\xa0', '').strip()
    if not s or s in ('-', '#DIV/0!', '#VALUE!', '#REF!', '#N/A', 'nan'): return np.nan
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return np.nan

@st.cache_data(ttl=300)
def load_sheet(url, expected_names, n_cols):
    """Lee con pd.read_csv directo (maneja redireccion Google) y renombra por posicion"""
    df = pd.read_csv(url, dtype=str)
    df.columns = df.columns.str.strip()
    cols = list(df.columns[:min(n_cols, len(df.columns))])
    out = df[cols].copy()
    rename = {cols[i]: expected_names[i] for i in range(len(cols))}
    out = out.rename(columns=rename)
    out['Fecha'] = pd.to_datetime(out['Fecha'], format='%d/%m/%Y', errors='coerce')
    for c in out.columns:
        if c != 'Fecha':
            out[c] = out[c].apply(conv)
    out = out.dropna(subset=['Fecha']).reset_index(drop=True)
    out = out.sort_values('Fecha').reset_index(drop=True)
    return out

def chart_layout(h=320):
    return dict(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#6B7C99', size=11), height=h,
                margin=dict(l=10, r=10, t=10, b=40),
                hovermode='x unified',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                xaxis=dict(showgrid=False, nticks=10, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))

# ── Cargar ──
try:
    df_ops = load_sheet(URL_OPS, ['Fecha','Ingreso_Broza','Inventario_Broza','Ley_Zn','Ley_Ag','Ley_Pb','Inv_CC_Zn','Inv_CC_Pb','TMH_Proc'], 9)
except Exception as e:
    st.error(f"⚠️ Error cargando Operaciones: {e}")
    st.stop()

try:
    df_teso = load_sheet(URL_TESO, ['Fecha','Bancos','Caja','CxC_Vig','CxC_Ven','CxP_Gen','CxP_Min'], 7)
except Exception:
    df_teso = pd.DataFrame()

if df_ops.empty:
    st.error("⚠️ No hay datos disponibles")
    st.stop()

# ── Fecha de referencia: AYER, o ultima disponible ──
ayer = (datetime.now() - timedelta(days=1)).date()
fechas_disp = df_ops['Fecha'].dt.date
if ayer in fechas_disp.values:
    fecha_ref = ayer
else:
    fecha_ref = fechas_disp.max()  # ultima fecha con datos

# ── HEADER ──
c1, c2, c3 = st.columns([3, 1, 1])
with c1: st.markdown("# ⛏️ MINERA PARKANO — Dashboard SSOT")
with c2: st.metric("📊 Registros", len(df_ops))
with c3: st.metric("📅 Datos al", fecha_ref.strftime("%d/%m/%Y"))
st.markdown("---")

# ── Filtros ──
c1, c2, c3 = st.columns(3)
with c1: f_desde = st.date_input("Desde", value=df_ops['Fecha'].min().date())
with c2: f_hasta = st.date_input("Hasta", value=fecha_ref)
with c3:
    meses = {"Todos":0,"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6}
    mes_sel = st.selectbox("Mes", list(meses.keys()))

df_f = df_ops[(df_ops['Fecha'] >= pd.to_datetime(f_desde)) & (df_ops['Fecha'] <= pd.to_datetime(f_hasta))].copy()
if mes_sel != "Todos":
    df_f = df_f[df_f['Fecha'].dt.month == meses[mes_sel]]
df_f = df_f.reset_index(drop=True)

if len(df_f) == 0:
    st.warning("Sin datos para el rango seleccionado")
    st.stop()

# Fila de referencia (snapshot del dia)
row_ref = df_ops[df_ops['Fecha'].dt.date == fecha_ref]
snap = row_ref.iloc[-1] if len(row_ref) > 0 else df_f.iloc[-1]

tab1, tab2, tab3, tab4 = st.tabs(["📊 Operaciones", "💰 Tesorería", "🔮 Predictivo", "📋 Datos"])

# ─── TAB 1: OPERACIONES ───
with tab1:
    st.markdown(f"### Indicadores Clave — al {fecha_ref.strftime('%d/%m/%Y')}")

    def sv(v, dec=2, suf=''):
        return f"{v:,.{dec}f}{suf}" if pd.notna(v) else "—"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("Inv. Broza (TMH)", sv(snap['Inventario_Broza']))
    with c2: st.metric("Ley Zn", sv(snap['Ley_Zn'], 2, '%'), delta=f"Prom: {df_f['Ley_Zn'].mean():.2f}%")
    with c3: st.metric("Ley Ag", sv(snap['Ley_Ag'], 2, '%'), delta=f"Prom: {df_f['Ley_Ag'].mean():.2f}%")
    with c4: st.metric("Ley Pb", sv(snap['Ley_Pb'], 2, '%'), delta=f"Prom: {df_f['Ley_Pb'].mean():.2f}%")
    with c5: st.metric("Ingreso del día", sv(snap['Ingreso_Broza'], 2, ' TMH'))
    with c6: st.metric("TMH Procesadas día", sv(snap['TMH_Proc'], 2))

    if pd.notna(snap['Inventario_Broza']) and snap['Inventario_Broza'] < 500:
        st.error(f"⚠️ **Inventario Crítico** — {snap['Inventario_Broza']:,.2f} TMH (umbral: 500 TMH)")

    st.markdown("####  ")
    st.markdown("#### 📈 Evolución del Inventario de Broza (TMH)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Inventario_Broza'], mode='lines',
                             line=dict(color='#C8A951', width=2.5), fill='tozeroy',
                             fillcolor='rgba(200,169,81,0.12)', name='Inventario'))
    fig.update_layout(**chart_layout(300))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🔬 Evolución de Leyes (%)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Zn'], name='Zn', line=dict(color='#4A9B8E', width=2)))
    fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Ag'], name='Ag', line=dict(color='#C8A951', width=2)))
    fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Pb'], name='Pb', line=dict(color='#8B6FA6', width=2)))
    fig.update_layout(**chart_layout(300))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Ingreso Broza Diario")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_f['Fecha'], y=df_f['Ingreso_Broza'], marker_color='#4A9B8E', name='Ingreso'))
        fig.update_layout(**chart_layout(280))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### TMH Procesadas Diario")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_f['Fecha'], y=df_f['TMH_Proc'], marker_color='#8B6FA6', name='TMH'))
        fig.update_layout(**chart_layout(280))
        st.plotly_chart(fig, use_container_width=True)

# ─── TAB 2: TESORERÍA ───
with tab2:
    if df_teso.empty:
        st.warning("⚠️ Sin datos de Tesorería")
    else:
        # Fecha ref tesoreria
        tfechas = df_teso['Fecha'].dt.date
        tref = ayer if ayer in tfechas.values else tfechas.max()
        trow = df_teso[df_teso['Fecha'].dt.date == tref]
        tsnap = trow.iloc[-1] if len(trow) > 0 else df_teso.iloc[-1]

        st.markdown(f"### Tesorería — al {tref.strftime('%d/%m/%Y')}")

        def sbs(v):
            return f"Bs {v:,.0f}" if pd.notna(v) else "—"

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("💰 Bancos", sbs(tsnap['Bancos']))
        with c2: st.metric("🏦 Caja", sbs(tsnap['Caja']))
        with c3: st.metric("📈 CxC Vigente", sbs(tsnap['CxC_Vig']))
        with c4: st.metric("📉 CxP Mineral", sbs(tsnap['CxP_Min']))

        liq = (tsnap['Bancos'] if pd.notna(tsnap['Bancos']) else 0) + (tsnap['Caja'] if pd.notna(tsnap['Caja']) else 0)
        st.markdown("####  ")
        c1, c2 = st.columns(2)
        with c1: st.metric("💵 Liquidez Total (Bancos + Caja)", f"Bs {liq:,.0f}")
        ct = (tsnap['CxC_Vig'] if pd.notna(tsnap['CxC_Vig']) else 0) - (tsnap['CxP_Min'] if pd.notna(tsnap['CxP_Min']) else 0)
        with c2: st.metric("⚖️ Capital de Trabajo (CxC - CxP)", f"Bs {ct:,.0f}")

        st.markdown("#### 📈 Evolución Efectivo: Bancos & Caja")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['Bancos'], name='Bancos', line=dict(color='#3DDC84', width=2.5), fill='tozeroy', fillcolor='rgba(61,220,132,0.1)'))
        fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['Caja'], name='Caja', line=dict(color='#C8A951', width=2)))
        fig.update_layout(**chart_layout(300))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 📊 Cuentas por Cobrar vs Pagar")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['CxC_Vig'], name='CxC Vigente', line=dict(color='#3DDC84', width=2)))
        fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['CxP_Min'], name='CxP Mineral', line=dict(color='#FF4D6D', width=2)))
        fig.update_layout(**chart_layout(300))
        st.plotly_chart(fig, use_container_width=True)

# ─── TAB 3: PREDICTIVO ───
with tab3:
    st.markdown("### 🔮 Análisis Predictivo — Inventario de Broza")
    inv_clean = df_f['Inventario_Broza'].dropna()
    if len(inv_clean) > 2:
        X = np.arange(len(inv_clean)).astype(float)
        y = inv_clean.values.astype(float)
        n = len(X)
        slope = (n*(X*y).sum() - X.sum()*y.sum()) / (n*(X**2).sum() - X.sum()**2)
        intercept = (y.sum() - slope*X.sum()) / n
        y_pred = slope*X + intercept
        ss_t = ((y - y.mean())**2).sum()
        r2 = 1 - ((y - y_pred)**2).sum()/ss_t if ss_t > 0 else 0

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Ecuación", f"y = {slope:.3f}x + {intercept:.1f}")
            st.metric("R² (ajuste)", f"{r2*100:.1f}%")
            st.metric("Pendiente", f"{slope:+.2f} TMH/día")
            st.metric("Proyección +30 días", f"{slope*30:+,.0f} TMH")
            st.markdown(f"**Tendencia:** :{'green' if slope>0 else 'red'}[{'↗ CRECIENTE' if slope>0 else '↘ DECRECIENTE'}]")
        with c2:
            st.metric("Media período", f"{y.mean():,.2f} TMH")
            st.metric("Máximo", f"{y.max():,.2f} TMH")
            st.metric("Mínimo", f"{y.min():,.2f} TMH")
            st.metric("Desv. Estándar", f"{y.std():,.2f} TMH")

        st.markdown("#### Inventario Real vs Línea de Tendencia")
        fechas = df_f.loc[inv_clean.index, 'Fecha']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechas, y=y, name='Real', line=dict(color='#C8A951', width=2.5), fill='tozeroy', fillcolor='rgba(200,169,81,0.1)'))
        fig.add_trace(go.Scatter(x=fechas, y=y_pred, name='Tendencia', line=dict(color='#FF4D6D', width=2.5, dash='dash')))
        fig.update_layout(**chart_layout(380))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Insuficientes datos para regresión")

# ─── TAB 4: DATOS ───
with tab4:
    st.markdown("### 📋 Histórico Completo de Operaciones")
    show = df_f.copy()
    show['Fecha'] = show['Fecha'].dt.strftime('%d/%m/%Y')
    st.dataframe(show, use_container_width=True, height=480)
    csv = df_f.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV", data=csv, file_name=f'parkano_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')

st.markdown("---")
st.caption(f"⛏️ Minera Parkano — Dashboard SSOT | Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df_ops)} registros operaciones · {len(df_teso)} tesorería | Auto-refresh cada 5 min")
