import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Control Tower — Minera Parkano", page_icon="⛏️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#0B0F1A,#131B2E)}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.2rem;max-width:1500px}
div[data-testid="stMetric"]{background:linear-gradient(135deg,#131B2E,#1A2438);padding:.9rem 1rem;border-radius:10px;border-left:3px solid #C8A951}
div[data-testid="stMetric"] label{color:#8595B0!important;font-size:.66rem!important;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#F0E9D6!important;font-size:1.3rem!important;font-weight:800;line-height:1.1}
div[data-testid="stMetric"] [data-testid="stMetricDelta"]{font-size:.7rem!important}
h1{color:#C8A951!important;font-weight:800;font-size:1.8rem}
h2,h3{color:#C8A951!important;font-weight:700}
.stTabs [data-baseweb="tab-list"]{background:#131B2E;padding:.4rem;border-radius:8px;gap:.3rem}
.stTabs [data-baseweb="tab"]{background:#1A2438;border-radius:6px;color:#8595B0;padding:.55rem 1.3rem;font-weight:600;border:none}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#C8A951,#9A7D2E)!important;color:#0B0F1A!important}
hr{border-color:rgba(200,169,81,.18);margin:.8rem 0}
</style>
""", unsafe_allow_html=True)

SID = "1jh_7rzOG1pisxwIIiT1CCfY3F0fdXmNA9vaaZFJUfns"
# GIDs confirmados directamente de la URL de Google Sheets
GID_OPS  = "225954691"   # Pestaña "Operaciones" — confirmado
GID_TESO = "158096369"   # Pestaña "Tesorería"   — confirmado
URL_OPS  = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid={GID_OPS}"
URL_TESO = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid={GID_TESO}"
def url(gid): return f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid={gid}"

# ─── Conversión número boliviano: "5.971,56"→5971.56 / "Bs8.134.479,10"→8134479.1
def bo(v):
    if v is None: return None
    s = str(v).strip()
    for r in ['Bs','%','\xa0',' ']: s = s.replace(r,'')
    if s in ('','-','#DIV/0!','#VALUE!','#REF!','#N/A','nan','None'): return None
    neg = s.startswith('-'); s = s.lstrip('-')
    s = s.replace('.','').replace(',','.')
    try:
        x = float(s)
        return -x if neg else x
    except: return None

# Headers conocidos para detectar la hoja
OPS_KEYS  = ['inventario_total_broza', 'ley_zn', 'ingreso_broza']
TESO_KEYS = ['efectivo_en_bancos', 'caja_central', 'cxc_vigente']

def detectar(df):
    cols = ' '.join(df.columns).lower()
    if any(k in cols for k in TESO_KEYS): return 'teso'
    if any(k in cols for k in OPS_KEYS):  return 'ops'
    return 'desconocido'

@st.cache_data(ttl=300)
def cargar_todo():
    """Carga Operaciones (URL sin gid) y Tesorería (gid=158096369)"""
    ops = None
    teso = None
    diag = []
    # Cargar Operaciones - URL sin GID = hoja por defecto
    try:
        raw = pd.read_csv(URL_OPS, dtype=str, storage_options={'User-Agent':'Mozilla/5.0'})
        raw.columns = raw.columns.str.strip()
        tipo = detectar(raw)
        diag.append(f"OPS URL: {len(raw)} filas, detectado='{tipo}', cols={list(raw.columns[:4])}")
        if tipo == 'ops':
            ops = procesar_ops(raw)
        else:
            diag.append(f"WARN: OPS URL devolvió tipo '{tipo}' — se intentará como ops de todas formas")
            ops = procesar_ops(raw)
    except Exception as e:
        diag.append(f"OPS URL ERROR: {type(e).__name__}: {str(e)[:150]}")
    # Cargar Tesorería - gid confirmado
    try:
        raw = pd.read_csv(URL_TESO, dtype=str, storage_options={'User-Agent':'Mozilla/5.0'})
        raw.columns = raw.columns.str.strip()
        tipo = detectar(raw)
        diag.append(f"TESO URL: {len(raw)} filas, detectado='{tipo}', cols={list(raw.columns[:4])}")
        if tipo == 'teso':
            teso = procesar_teso(raw)
    except Exception as e:
        diag.append(f"TESO URL ERROR: {type(e).__name__}: {str(e)[:150]}")
    return ops, teso, diag

def procesar_ops(raw):
    m = {}
    for c in raw.columns:
        cl = c.lower()
        if cl == 'fecha': m[c] = 'Fecha'
        elif 'ingreso_broza' in cl: m[c] = 'Ingreso_TMH'
        elif 'inventario_total_broza' in cl: m[c] = 'Inventario_TMH'
        elif cl == 'ley_zn': m[c] = 'Ley_Zn'
        elif cl == 'ley_ag': m[c] = 'Ley_Ag'
        elif cl == 'ley_pb': m[c] = 'Ley_Pb'
        elif 'inventario_cc_zn' in cl: m[c] = 'CC_Zn'
        elif 'inventario_cc_pb' in cl: m[c] = 'CC_Pb'
        elif 'tmh_procesadas' in cl: m[c] = 'TMH_Proc'
    df = raw.rename(columns=m)
    keep = [v for v in ['Fecha','Ingreso_TMH','Inventario_TMH','Ley_Zn','Ley_Ag','Ley_Pb','CC_Zn','CC_Pb','TMH_Proc'] if v in df.columns]
    df = df[keep].copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
    for c in keep:
        if c != 'Fecha': df[c] = df[c].map(bo)
    df = df.dropna(subset=['Fecha']).sort_values('Fecha').reset_index(drop=True)
    return df

def procesar_teso(raw):
    m = {}
    for c in raw.columns:
        cl = c.lower()
        if cl == 'fecha': m[c] = 'Fecha'
        elif 'efectivo_en_bancos' in cl: m[c] = 'Bancos'
        elif 'caja_central' in cl: m[c] = 'Caja'
        elif 'cxc_vigente' in cl: m[c] = 'CxC_Vig'
        elif 'cxc_vencido' in cl: m[c] = 'CxC_Ven'
        elif 'cxp_general' in cl: m[c] = 'CxP_Gen'
        elif 'cxp_mineral' in cl: m[c] = 'CxP_Min'
    df = raw.rename(columns=m)
    keep = [v for v in ['Fecha','Bancos','Caja','CxC_Vig','CxC_Ven','CxP_Gen','CxP_Min'] if v in df.columns]
    df = df[keep].copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
    for c in keep:
        if c != 'Fecha': df[c] = df[c].map(bo)
    df = df.dropna(subset=['Fecha'])
    numc = [c for c in keep if c != 'Fecha']
    df = df.dropna(subset=numc, how='all').sort_values('Fecha').reset_index(drop=True)
    return df

# ═══════════════════════ CARGAR ═══════════════════════
# Probar varios GIDs comunes para encontrar ambas hojas
df_ops, df_teso, diag = cargar_todo()

if df_ops is None or df_ops.empty:
    st.error("⚠️ No se pudieron cargar los datos de Operaciones.")
    with st.expander("🔍 Diagnóstico (ábrelo y compártelo si el error persiste)", expanded=True):
        for d in diag:
            st.code(d)
        st.markdown("**Verifica que el Google Sheet esté compartido como: 'Cualquiera con el enlace → Lector'**")
        st.markdown(f"URL probada ejemplo: `{url('0')}`")
    st.stop()

if df_teso is None or df_teso.empty:
    st.warning("⚠️ No se detectó la hoja de Tesorería. Operaciones sí cargó correctamente.")
    with st.expander("🔍 Diagnóstico Tesorería"):
        for d in diag:
            st.code(d)

# ─── Fecha referencia = última fecha CON datos de inventario ───
def ultima_con_dato(df, col):
    valido = df[df[col].notna()]
    return valido['Fecha'].max().date() if len(valido) else df['Fecha'].max().date()

fref_ops = ultima_con_dato(df_ops, 'Inventario_TMH')
fref_teso = ultima_con_dato(df_teso, 'Bancos') if (df_teso is not None and not df_teso.empty) else None

def snap(df, fref, col_req):
    """Última fila <= fref que tenga dato en col_req"""
    sub = df[(df['Fecha'].dt.date <= fref) & (df[col_req].notna())]
    if len(sub): return sub.iloc[-1]
    return df.iloc[-1]

def fmt(v, dec=2, pre='', suf=''):
    if v is None or pd.isna(v): return "—"
    return f"{pre}{v:,.{dec}f}{suf}"

def layout(h=300):
    return dict(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#8595B0', size=11), height=h,
        margin=dict(l=8, r=8, t=8, b=45), hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0, font_size=11),
        xaxis=dict(showgrid=False, nticks=9, tickangle=-25, tickfont_size=10),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont_size=10, zeroline=False)
    )

# ═══════════════════════ HEADER ═══════════════════════
c1,c2,c3,c4 = st.columns([3.2,1,1,1])
with c1: st.markdown("# ⛏️ MINERA PARKANO")
with c2: st.metric("Reg. Operaciones", len(df_ops))
with c3: st.metric("Reg. Tesorería", len(df_teso) if df_teso is not None else 0)
with c4: st.metric("Datos al", fref_ops.strftime("%d/%m/%Y"))
st.markdown("---")

# ═══════════════════════ FILTROS ═══════════════════════
c1,c2,c3,c4 = st.columns([1.4,1.4,1,0.7])
with c1: f_desde = st.date_input("Desde", value=df_ops['Fecha'].min().date())
with c2: f_hasta = st.date_input("Hasta", value=fref_ops)
with c3:
    mmap = {"Todos":0,"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,"Julio":7}
    mes = st.selectbox("Mes", list(mmap.keys()))
with c4:
    st.write("")
    if st.button("🔄 Refrescar"):
        st.cache_data.clear(); st.rerun()

df_f = df_ops[(df_ops['Fecha']>=pd.to_datetime(f_desde)) & (df_ops['Fecha']<=pd.to_datetime(f_hasta))].copy()
if mes != "Todos": df_f = df_f[df_f['Fecha'].dt.month == mmap[mes]]
df_f = df_f.reset_index(drop=True)
if len(df_f)==0:
    st.warning("Sin datos en el rango seleccionado"); st.stop()

s = snap(df_ops, fref_ops, 'Inventario_TMH')

t1,t2,t3,t4 = st.tabs(["📊 Operaciones","💰 Tesorería","🔮 Predictivo","📋 Datos"])

# ═══════════════════ TAB 1: OPERACIONES ═══════════════════
with t1:
    st.markdown(f"### Indicadores al {fref_ops.strftime('%d/%m/%Y')}")
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    with k1: st.metric("🗻 Inventario Broza", fmt(s.get('Inventario_TMH'),2,'',' TMH'))
    with k2: st.metric("⛏️ Ley Zn", fmt(s.get('Ley_Zn'),2,'','%'), delta=f"Prom: {df_f['Ley_Zn'].mean():.2f}%")
    with k3: st.metric("🥈 Ley Ag", fmt(s.get('Ley_Ag'),2,'','%'), delta=f"Prom: {df_f['Ley_Ag'].mean():.2f}%")
    with k4: st.metric("🔩 Ley Pb", fmt(s.get('Ley_Pb'),2,'','%'), delta=f"Prom: {df_f['Ley_Pb'].mean():.2f}%")
    with k5: st.metric("📥 Ingreso del día", fmt(s.get('Ingreso_TMH'),2,'',' TMH'))
    with k6: st.metric("⚙️ Procesado del día", fmt(s.get('TMH_Proc'),2,'',' TMH'))

    inv = s.get('Inventario_TMH') or 0
    if inv < 500:
        st.error(f"🔴 **INVENTARIO CRÍTICO** — {inv:,.2f} TMH (umbral mínimo: 500 TMH)")
    elif inv < 1000:
        st.warning(f"🟡 **Inventario bajo** — {inv:,.2f} TMH")

    st.markdown("---")
    st.markdown("#### 📈 Evolución del Inventario de Broza (TMH)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Inventario_TMH'], mode='lines',
                  name='Inventario', line=dict(color='#C8A951', width=2.5),
                  fill='tozeroy', fillcolor='rgba(200,169,81,0.10)'))
    fig.add_hline(y=500, line=dict(color='#FF4D6D', width=1.3, dash='dash'),
                  annotation_text="Crítico 500", annotation_font=dict(color='#FF4D6D', size=10))
    fig.update_layout(**layout(270))
    st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Leyes Zn / Ag / Pb (%)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Zn'], name='Zn', line=dict(color='#4A9B8E', width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Ag'], name='Ag', line=dict(color='#C8A951', width=2)))
        fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['Ley_Pb'], name='Pb', line=dict(color='#8B6FA6', width=2)))
        fig.update_layout(**layout(250))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        if 'CC_Zn' in df_f.columns:
            st.markdown("#### Inventario Concentrado CC (TMH)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['CC_Zn'], name='CC Zn', line=dict(color='#4A9B8E', width=2)))
            fig.add_trace(go.Scatter(x=df_f['Fecha'], y=df_f['CC_Pb'], name='CC Pb', line=dict(color='#8B6FA6', width=2)))
            fig.update_layout(**layout(250))
            st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Ingreso Broza Diario (TMH)")
        fig = go.Figure([go.Bar(x=df_f['Fecha'], y=df_f['Ingreso_TMH'], marker_color='#4A9B8E', marker_line_width=0)])
        fig.update_layout(**layout(230))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### TMH Procesadas Diario")
        fig = go.Figure([go.Bar(x=df_f['Fecha'], y=df_f['TMH_Proc'], marker_color='#8B6FA6', marker_line_width=0)])
        fig.update_layout(**layout(230))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════ TAB 2: TESORERÍA ═══════════════════
with t2:
    if df_teso is None or df_teso.empty:
        st.info("No se detectaron datos de Tesorería.")
    else:
        st.markdown(f"### Tesorería al {fref_teso.strftime('%d/%m/%Y')}")
        ts = snap(df_teso, fref_teso, 'Bancos')
        bancos = ts.get('Bancos') or 0
        caja   = ts.get('Caja') or 0
        cxc    = ts.get('CxC_Vig') or 0
        cxp    = ts.get('CxP_Min') or 0
        liq = bancos + caja
        ct  = cxc - cxp

        k1,k2,k3,k4,k5,k6 = st.columns(6)
        with k1: st.metric("🏦 Bancos", fmt(bancos,0,'Bs '))
        with k2: st.metric("💵 Caja", fmt(caja,0,'Bs '))
        with k3: st.metric("💰 Liquidez Total", fmt(liq,0,'Bs '))
        with k4: st.metric("📈 CxC Vigente", fmt(cxc,0,'Bs '))
        with k5: st.metric("📉 CxP Mineral", fmt(cxp,0,'Bs '))
        with k6: st.metric("⚖️ Cap. Trabajo", fmt(ct,0,'Bs '), delta="Positivo" if ct>=0 else "Déficit", delta_color="normal" if ct>=0 else "inverse")

        st.markdown("---")
        st.markdown("#### 📈 Evolución de Efectivo: Bancos & Caja (Bs)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['Bancos'], name='Bancos', line=dict(color='#3DDC84', width=2.5), fill='tozeroy', fillcolor='rgba(61,220,132,0.08)'))
        fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['Caja'], name='Caja', line=dict(color='#C8A951', width=2)))
        fig.update_layout(**layout(270))
        st.plotly_chart(fig, use_container_width=True)

        c1,c2 = st.columns(2)
        with c1:
            st.markdown("#### CxC Vigente vs CxP Mineral (Bs)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['CxC_Vig'], name='CxC Vigente', line=dict(color='#3DDC84', width=2)))
            fig.add_trace(go.Scatter(x=df_teso['Fecha'], y=df_teso['CxP_Min'], name='CxP Mineral', line=dict(color='#FF4D6D', width=2)))
            fig.update_layout(**layout(250))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### Capital de Trabajo (CxC − CxP)")
            serie = df_teso['CxC_Vig'].fillna(0) - df_teso['CxP_Min'].fillna(0)
            colores = ['#3DDC84' if v>=0 else '#FF4D6D' for v in serie]
            fig = go.Figure([go.Bar(x=df_teso['Fecha'], y=serie, marker_color=colores, marker_line_width=0)])
            fig.add_hline(y=0, line=dict(color='#8595B0', width=1, dash='dot'))
            fig.update_layout(**layout(250))
            st.plotly_chart(fig, use_container_width=True)

# ═══════════════════ TAB 3: PREDICTIVO ═══════════════════
with t3:
    st.markdown("### 🔮 Análisis Predictivo — Inventario de Broza")
    serie = df_f[df_f['Inventario_TMH'].notna()]
    if len(serie) < 3:
        st.warning("Se necesitan ≥3 registros.")
    else:
        x = list(range(len(serie)))
        y = serie['Inventario_TMH'].tolist()
        n = len(x); sx=sum(x); sy=sum(y); sxy=sum(x[i]*y[i] for i in range(n)); sx2=sum(v*v for v in x)
        sl = (n*sxy-sx*sy)/(n*sx2-sx*sx) if (n*sx2-sx*sx)!=0 else 0
        ic = (sy-sl*sx)/n
        yp = [sl*v+ic for v in x]
        ym = sy/n
        sst = sum((v-ym)**2 for v in y)
        r2 = 1-sum((y[i]-yp[i])**2 for i in range(n))/sst if sst>0 else 0
        adj = 'Excelente' if r2>.7 else 'Bueno' if r2>.5 else 'Moderado' if r2>.3 else 'Débil'

        c1,c2 = st.columns(2)
        with c1:
            st.markdown("#### Regresión Lineal")
            st.metric("Ecuación", f"y = {sl:.3f}x + {ic:.1f}")
            st.metric("R² (ajuste)", f"{r2*100:.1f}% — {adj}")
            st.metric("Pendiente", f"{sl:+.2f} TMH/día")
            st.metric("Proyección +30 días", f"{sl*30:+,.0f} TMH")
            st.markdown(f"**Tendencia:** :{'green' if sl>0 else 'red'}[{'↗ CRECIENTE' if sl>0 else '↘ DECRECIENTE'}]")
        with c2:
            st.markdown("#### Estadísticas del Período")
            st.metric("Media", f"{ym:,.2f} TMH")
            st.metric("Máximo", f"{max(y):,.2f} TMH")
            st.metric("Mínimo", f"{min(y):,.2f} TMH")
            st.metric("Registros", f"{n} días")

        st.markdown("#### Inventario Real vs Tendencia")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=serie['Fecha'], y=y, name='Real', line=dict(color='#C8A951', width=2.5), fill='tozeroy', fillcolor='rgba(200,169,81,0.08)'))
        fig.add_trace(go.Scatter(x=serie['Fecha'], y=yp, name='Tendencia', line=dict(color='#FF4D6D', width=2.5, dash='dash')))
        fig.update_layout(**layout(340))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════ TAB 4: DATOS ═══════════════════
with t4:
    st.markdown("### 📋 Histórico de Operaciones")
    show = df_f.copy()
    show['Fecha'] = show['Fecha'].dt.strftime('%d/%m/%Y')
    st.dataframe(show, use_container_width=True, height=430)
    st.download_button("📥 Descargar CSV", df_f.to_csv(index=False).encode('utf-8'),
                       file_name=f'parkano_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')
    if df_teso is not None and not df_teso.empty:
        st.markdown("### 📋 Histórico de Tesorería")
        sht = df_teso.copy()
        sht['Fecha'] = sht['Fecha'].dt.strftime('%d/%m/%Y')
        st.dataframe(sht, use_container_width=True, height=300)

st.markdown("---")
st.caption(f"⛏️ Minera Parkano — Control Tower SSOT | Datos al {fref_ops.strftime('%d/%m/%Y')} | {len(df_ops)} ops · {len(df_teso) if df_teso is not None else 0} tes. | Auto-refresh 5 min")
