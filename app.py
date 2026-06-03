import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
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


def conv_num_bo(val):
    """Convierte números en formato boliviano (5.971,56 → 5971.56)"""
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    # Remover Bs, %, espacios, #DIV/0!
    s = s.replace('Bs', '').replace('%', '').replace('\xa0', '').strip()
    if s in ('', '-', '#DIV/0!', '#VALUE!', '#REF!', '#N/A'):
        return np.nan
    # Formato boliviano: punto = miles, coma = decimal
    # "5.971,56" → "5971.56"
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return np.nan


@st.cache_data(ttl=300)
def load_ops():
    try:
        raw = pd.read_csv(URL_OPS, dtype=str)
        raw.columns = raw.columns.str.strip()
        cols_need = ['Fecha', 'Ingreso_Broza_TMH', 'Inventario_Total_Broza_TMH',
                     'Ley_Zn', 'Ley_AG', 'Ley_PB',
                     'Inventario_CC_Zn', 'Inventario_CC_Pb', 'TMH_Procesadas_dia']
        # Solo quedarnos con columnas que existen
        cols_use = [c for c in cols_need if c in raw.columns]
        df = raw[cols_use].copy()
        # Parsear fecha
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        # Convertir numéricas
        for c in cols_use:
            if c != 'Fecha':
                df[c] = df[c].apply(conv_num_bo)
        df = df.dropna(subset=['Fecha']).reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_teso():
    try:
        raw = pd.read_csv(URL_TESO, dtype=str)
        raw.columns = raw.columns.str.strip()
        cols_need = ['Fecha', 'Efectivo_en_Bancos', 'Caja_Central_Mineral',
                     'CxC_Vigente', 'CxC_Vencidos', 'CxP_Mineral']
        cols_use = [c for c in cols_need if c in raw.columns]
        df = raw[cols_use].copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        for c in cols_use:
            if c != 'Fecha':
                df[c] = df[c].apply(conv_num_bo)
        df = df.dropna(subset=['Fecha']).reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()


# ── Cargar datos ──
df_ops = load_ops()
df_teso = load_teso()

if df_ops.empty:
    st.error("⚠️ No se pudieron cargar los datos. Verifica conexión a Google Sheets.")
    st.stop()

# ── HEADER ──
c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    st.markdown("# ⛏️ MINERA PARKANO — Dashboard SSOT")
with c2:
    st.metric("📊 Registros", len(df_ops))
with c3:
    st.metric("📅 Ref.", (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y"))

st.markdown("---")

# ── Filtros ──
c1, c2, c3 = st.columns(3)
with c1:
    f_desde = st.date_input("Desde", value=df_ops['Fecha'].min().date())
with c2:
    f_hasta = st.date_input("Hasta", value=df_ops['Fecha'].max().date())
with c3:
    meses = {"Todos": 0, "Enero": 1, "Febrero": 2, "Marzo": 3,
             "Abril": 4, "Mayo": 5, "Junio": 6}
    mes_sel = st.selectbox("Mes", list(meses.keys()))

df_f = df_ops[(df_ops['Fecha'] >= pd.to_datetime(f_desde)) &
              (df_ops['Fecha'] <= pd.to_datetime(f_hasta))].copy()
if mes_sel != "Todos":
    df_f = df_f[df_f['Fecha'].dt.month == meses[mes_sel]]
df_f = df_f.reset_index(drop=True)

if len(df_f) == 0:
    st.warning("Sin datos para el rango seleccionado")
    st.stop()

# ── TABS ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Operaciones", "💰 Tesorería", "🔮 Predictivo", "📋 Datos"])

# ─────────── TAB 1: OPERACIONES ───────────
with tab1:
    st.markdown("### Indicadores Clave")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    last_inv = df_f['Inventario_Total_Broza_TMH'].dropna().iloc[-1] if not df_f['Inventario_Total_Broza_TMH'].dropna().empty else 0
    avg_zn = df_f['Ley_Zn'].dropna().mean() if not df_f['Ley_Zn'].dropna().empty else 0
    avg_ag = df_f['Ley_AG'].dropna().mean() if not df_f['Ley_AG'].dropna().empty else 0
    avg_pb = df_f['Ley_PB'].dropna().mean() if not df_f['Ley_PB'].dropna().empty else 0
    tot_ing = df_f['Ingreso_Broza_TMH'].dropna().sum()
    tot_tmh = df_f['TMH_Procesadas_dia'].dropna().sum()

    with c1:
        st.metric("Inv. Broza (TMH)", f"{last_inv:,.2f}")
    with c2:
        st.metric("Ley Zn Prom.", f"{avg_zn:.2f}%")
    with c3:
        st.metric("Ley Ag Prom.", f"{avg_ag:.2f}%")
    with c4:
        st.metric("Ley Pb Prom.", f"{avg_pb:.2f}%")
    with c5:
        st.metric("Total Ingreso", f"{tot_ing:,.0f} TMH")
    with c6:
        st.metric("TMH Procesadas", f"{tot_tmh:,.0f}")

    if last_inv < 500:
        st.error(f"⚠️ **Inventario Crítico** — {last_inv:,.2f} TMH (umbral: 500 TMH)")

    st.markdown("---")

    # Gráficos
    c1, c2 = st.columns(2)
    plot_cfg = dict(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#6B7C99', height=300, margin=dict(l=0, r=0, t=30, b=0))

    with c1:
        st.markdown("#### Inventario Broza (TMH)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Inventario_Total_Broza_TMH'],
                                 fill='tozeroy', line=dict(color='#C8A951', width=2),
                                 fillcolor='rgba(200,169,81,0.15)', name='Inventario'))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### Leyes Zn / Ag / Pb (%)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Zn'], name='Zn%',
                                 line=dict(color='#4A9B8E', width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_AG'], name='Ag%',
                                 line=dict(color='#C8A951', width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_PB'], name='Pb%',
                                 line=dict(color='#8B6FA6', width=2)))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Ingreso Broza Diario (TMH)")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_f['Fecha'], y=df_f['Ingreso_Broza_TMH'],
                             marker_color='#4A9B8E', name='Ingreso'))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.markdown("#### TMH Procesadas / Día")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_f['Fecha'], y=df_f['TMH_Procesadas_dia'],
                             marker_color='#8B6FA6', name='TMH'))
        fig.update_layout(**plot_cfg)
        st.plotly_chart(fig, use_container_width=True)

# ─────────── TAB 2: TESORERÍA ───────────
with tab2:
    if df_teso.empty:
        st.warning("⚠️ Sin datos de Tesorería")
    else:
        st.markdown("### Indicadores Tesorería")
        last_b = df_teso['Efectivo_en_Bancos'].dropna().iloc[-1] if not df_teso['Efectivo_en_Bancos'].dropna().empty else 0
        last_c = df_teso['Caja_Central_Mineral'].dropna().iloc[-1] if not df_teso['Caja_Central_Mineral'].dropna().empty else 0
        last_cxc = df_teso['CxC_Vigente'].dropna().iloc[-1] if not df_teso['CxC_Vigente'].dropna().empty else 0
        last_cxp = df_teso['CxP_Mineral'].dropna().iloc[-1] if not df_teso['CxP_Mineral'].dropna().empty else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("💰 Bancos", f"Bs {last_b:,.0f}")
        with c2:
            st.metric("🏦 Caja", f"Bs {last_c:,.0f}")
        with c3:
            st.metric("📈 CxC Vigente", f"Bs {last_cxc:,.0f}")
        with c4:
            st.metric("📉 CxP Mineral", f"Bs {last_cxp:,.0f}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Efectivo: Bancos & Caja")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['Efectivo_en_Bancos'],
                                     name='Bancos', line=dict(color='#3DDC84', width=2)))
            fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['Caja_Central_Mineral'],
                                     name='Caja', line=dict(color='#C8A951', width=2)))
            fig.update_layout(**plot_cfg)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("#### CxC vs CxP")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['CxC_Vigente'],
                                     name='CxC', line=dict(color='#3DDC84', width=2)))
            fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['CxP_Mineral'],
                                     name='CxP', line=dict(color='#FF4D6D', width=2)))
            fig.update_layout(**plot_cfg)
            st.plotly_chart(fig, use_container_width=True)

# ─────────── TAB 3: PREDICTIVO ───────────
with tab3:
    st.markdown("### 🔮 Regresión Lineal — Inventario Broza")
    inv_clean = df_f['Inventario_Total_Broza_TMH'].dropna()
    if len(inv_clean) > 2:
        X = np.arange(len(inv_clean)).astype(float)
        y = inv_clean.values.astype(float)
        n = len(X)
        slope = (n * (X * y).sum() - X.sum() * y.sum()) / (n * (X ** 2).sum() - X.sum() ** 2)
        intercept = (y.sum() - slope * X.sum()) / n
        y_pred = slope * X + intercept
        ss_tot = ((y - y.mean()) ** 2).sum()
        ss_res = ((y - y_pred) ** 2).sum()
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Regresión")
            st.metric("Ecuación", f"y = {slope:.4f}x + {intercept:.2f}")
            st.metric("R²", f"{r2 * 100:.1f}%")
            st.metric("Pendiente", f"{slope:+.2f} TMH/día")
            st.metric("Proy. +30d", f"{slope * 30:+.0f} TMH")
            t = "↗ CRECIENTE" if slope > 0 else "↘ DECRECIENTE"
            cl = "green" if slope > 0 else "red"
            st.markdown(f"**Tendencia:** :{cl}[{t}]")
        with c2:
            st.markdown("#### Estadísticas")
            st.metric("Media", f"{y.mean():,.2f} TMH")
            st.metric("Máximo", f"{y.max():,.2f} TMH")
            st.metric("Mínimo", f"{y.min():,.2f} TMH")
            st.metric("Desv. Estándar", f"{y.std():,.2f} TMH")
            st.metric("Registros", f"{n} días")

        st.markdown("#### Inventario Real vs Tendencia")
        fechas_clean = df_f.loc[inv_clean.index, 'Fecha']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fechas_clean, y=y, name='Real',
                                 line=dict(color='#C8A951', width=2),
                                 fill='tozeroy', fillcolor='rgba(200,169,81,0.1)'))
        fig.add_trace(go.Scatter(x=fechas_clean, y=y_pred, name='Tendencia',
                                 line=dict(color='#FF4D6D', width=3, dash='dash')))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          font_color='#6B7C99', height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Insuficientes datos para regresión")

# ─────────── TAB 4: DATOS ───────────
with tab4:
    st.markdown("### 📋 Datos Completos")
    display_cols = [c for c in ['Fecha', 'Ingreso_Broza_TMH', 'Inventario_Total_Broza_TMH',
                                'Ley_Zn', 'Ley_AG', 'Ley_PB', 'TMH_Procesadas_dia']
                    if c in df_f.columns]
    st.dataframe(df_f[display_cols], use_container_width=True, height=500)
    csv = df_f[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV", data=csv,
                       file_name=f'parkano_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')

# Footer
st.markdown("---")
st.caption(f"⛏️ Minera Parkano | {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df_ops)} registros | Auto-refresh 5 min")
