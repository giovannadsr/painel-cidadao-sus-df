from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# PAINEL CIDADÃO | SAÚDE TRANSPARENTE - SUS/DF
# ------------------------------------------------------------

st.set_page_config(
    page_title="Painel Cidadão | SUS-DF",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARQUIVO_PADRAO = Path("dados_sus/lista_espera_sus_df.csv")

COLUNAS = [
    "servico",
    "codigo_procedimento",
    "descricao_procedimento",
    "procedimento",
    "grupo_procedimento",
    "posicao",
    "classificacao_risco",
    "data_solicitacao",
    "tempo_espera",
]

# ------------------------------------------------------------
# ESTILIZAÇÃO SOFISTICADA E DESTAQUE PARA OS CARTÕES
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* BARRA LATERAL EM AZUL ESCURO INSTITUCIONAL */
    [data-testid="stSidebar"] {
        background-color: #102f66 !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }

    /* CARTÕES DE INDICADORES SOFISTICADOS */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #d0e1fd;
        border-top: 4px solid #12366f;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 6px 18px rgba(18, 54, 111, 0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(18, 54, 111, 0.14);
    }

    .kpi-label {
        color: #4a5d78;
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }

    .kpi-value {
        color: #12366f;
        font-size: 1.85rem;
        font-weight: 800;
        line-height: 1.15;
        margin-bottom: 6px;
    }

    .kpi-note {
        color: #64748b;
        font-size: 0.78rem;
    }

    /* TÍTULOS E CABEÇALHO */
    .brand-kicker {
        color: #245a9b;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
    }

    .main-title {
        color: #12366f;
        font-size: 2.15rem;
        font-weight: 800;
        line-height: 1.12;
        margin: .15rem 0 .45rem 0;
    }

    .main-subtitle {
        color: #40536c;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }

    .section-title {
        color: #173b72;
        font-size: 1.25rem;
        font-weight: 750;
        margin: 1.2rem 0 .8rem 0;
        border-left: 4px solid #245a9b;
        padding-left: 10px;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# DETECÇÃO DO TEMA PARA OS GRÁFICOS PLOTLY
# ------------------------------------------------------------
try:
    theme_base = st.get_option("theme.base")
    is_dark = theme_base == "dark"
except Exception:
    is_dark = False

tema_grafico = "plotly_dark" if is_dark else "plotly_white"

# ------------------------------------------------------------
# CABEÇALHO
# ------------------------------------------------------------

st.markdown('<div class="brand-kicker">Transparência pública • Distrito Federal</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Painel Cidadão | Saúde Transparente</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Visualização analítica das filas de espera por consultas, '
    'cirurgias eletivas e exames do SUS-DF.</div>',
    unsafe_allow_html=True,
)
st.divider()

# ------------------------------------------------------------
# FONTE DE DADOS (BARRA LATERAL)
# ------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🏥 Painel Cidadão")
    st.caption("SUS • Distrito Federal")
    st.divider()

    st.markdown("### Fonte de dados")

    upload = st.file_uploader(
        "Carregar planilha CSV",
        type=["csv"],
        help="A base consolidada do extrator é esperada em CSV separado por ponto e vírgula.",
    )

    st.caption(f"Arquivo local esperado: {ARQUIVO_PADRAO.as_posix()}")
    st.divider()
    st.markdown("### Filtros")
    st.caption("Os filtros serão habilitados após o carregamento da base.")

try:
    if upload is not None:
        df = pd.read_csv(upload, sep=";", encoding="utf-8-sig")
        origem = "Arquivo carregado manualmente"

    elif ARQUIVO_PADRAO.exists():
        df = pd.read_csv(ARQUIVO_PADRAO, sep=";", encoding="utf-8-sig")
        origem = str(ARQUIVO_PADRAO)

    else:
        df = None
        origem = None

except Exception as exc:
    st.error(f"Não foi possível abrir o arquivo CSV: {exc}")
    st.stop()

# ------------------------------------------------------------
# ESTADO SEM BASE
# ------------------------------------------------------------

if df is None:
    with st.container(border=True):
        st.markdown("### 📊 A interface está pronta para receber os dados")
        st.write(
            "A extração da lista de espera ainda está em andamento. "
            "Quando o arquivo **lista_espera_sus_df.csv** estiver "
            "consolidado, coloque-o na pasta **dados_sus** ou "
            "carregue-o pela barra lateral."
        )
    st.stop()

# ------------------------------------------------------------
# VALIDAÇÃO E PREPARAÇÃO DOS DADOS
# ------------------------------------------------------------

faltantes = [col for col in COLUNAS if col not in df.columns]
if faltantes:
    st.error(f"A planilha não corresponde ao formato esperado. Colunas ausentes: {', '.join(faltantes)}")
    st.stop()

df["servico"] = df["servico"].astype("string").str.strip()
df["procedimento"] = df["procedimento"].astype("string").str.strip()
df["classificacao_risco"] = df["classificacao_risco"].astype("string").str.strip()
df["tempo_espera"] = pd.to_numeric(df["tempo_espera"], errors="coerce")
df["posicao"] = pd.to_numeric(df["posicao"], errors="coerce")
df["data_solicitacao"] = pd.to_datetime(df["data_solicitacao"], errors="coerce", format="%Y-%m-%d")

# ------------------------------------------------------------
# FILTROS
# ------------------------------------------------------------

with st.sidebar:
    servicos = sorted(df["servico"].dropna().astype(str).unique().tolist())
    servicos_sel = st.multiselect("Tipo de serviço", servicos, default=servicos)

    base_filtro = df[df["servico"].astype(str).isin(servicos_sel)].copy()

    procedimentos = sorted(base_filtro["procedimento"].dropna().astype(str).unique().tolist())
    procedimentos_sel = st.multiselect("Procedimento", procedimentos)

    riscos = sorted(base_filtro["classificacao_risco"].dropna().astype(str).unique().tolist())
    riscos_sel = st.multiselect("Classificação de risco", riscos)

filtrado = base_filtro.copy()
if procedimentos_sel:
    filtrado = filtrado[filtrado["procedimento"].astype(str).isin(procedimentos_sel)]
if riscos_sel:
    filtrado = filtrado[filtrado["classificacao_risco"].astype(str).isin(riscos_sel)]

if filtrado.empty:
    st.warning("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

# ------------------------------------------------------------
# INDICADORES (KPIs COM ALTO DESTAQUE)
# ------------------------------------------------------------

total = len(filtrado)
media = filtrado["tempo_espera"].mean()
mediana = filtrado["tempo_espera"].median()
n_procedimentos = filtrado["codigo_procedimento"].nunique()

def fmt_num(valor):
    if pd.isna(valor):
        return "—"
    return f"{valor:,.0f}".replace(",", ".")

st.markdown('<div class="section-title">Visão geral da fila</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Registros na seleção</div>
            <div class="kpi-value">{fmt_num(total)}</div>
            <div class="kpi-note">Solicitações na base filtrada</div>
        </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Tempo médio de espera</div>
            <div class="kpi-value">{fmt_num(media)} <span style="font-size:1rem; font-weight:600;">dias</span></div>
            <div class="kpi-note">Média dos tempos registrados</div>
        </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Mediana de espera</div>
            <div class="kpi-value">{fmt_num(mediana)} <span style="font-size:1rem; font-weight:600;">dias</span></div>
            <div class="kpi-note">50% abaixo deste valor</div>
        </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Procedimentos distintos</div>
            <div class="kpi-value">{fmt_num(n_procedimentos)}</div>
            <div class="kpi-note">Códigos na seleção atual</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")
st.info("💡 **Nota de Transparência:** Os indicadores refletem os registros extraídos e não substituem o agendamento em tempo real do Complexo Regulador.")
st.write("")

# ------------------------------------------------------------
# CONFIGURAÇÃO DE PLOTLY REFINADA E LIMPA (CORRIGIDO)
# ------------------------------------------------------------
def ajustar_grafico(fig):
    fig.update_layout(
        template=tema_grafico,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#334155" if not is_dark else "#e2e8f0"),
        title_font=dict(size=15, family="Inter, sans-serif", color="#12366f" if not is_dark else "#ffffff"),
        margin=dict(l=15, r=15, t=50, b=15),
        hoverlabel=dict(bgcolor="#ffffff" if not is_dark else "#1c2b40", font_size=13, font_family="Inter"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)", zeroline=False)
    return fig

# ------------------------------------------------------------
# GRÁFICOS
# ------------------------------------------------------------

st.markdown('<div class="section-title">Distribuição e Perfil da Fila</div>', unsafe_allow_html=True)

esq, dir = st.columns(2)

with esq:
    por_servico = filtrado.groupby("servico", dropna=False).size().reset_index(name="registros").sort_values("registros", ascending=False)
    fig = px.bar(
        por_servico, x="servico", y="registros", color="servico",
        title="Registros por tipo de serviço",
        labels={"servico": "Tipo de serviço", "registros": "Total de Registros"},
        color_discrete_sequence=["#12366f", "#245a9b", "#4b9bea"]
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(ajustar_grafico(fig), use_container_width=True)

with dir:
    top_proc = filtrado.groupby("procedimento", dropna=False).size().reset_index(name="registros").nlargest(12, "registros").sort_values("registros")
    fig = px.bar(
        top_proc, x="registros", y="procedimento", orientation="h",
        title="Top 15 procedimentos com mais registros",
        labels={"procedimento": "Procedimento", "registros": "Total de Registros"},
        color_discrete_sequence=["#0d9488"]
    )
    st.plotly_chart(ajustar_grafico(fig), use_container_width=True)

esq, dir = st.columns(2)

with esq:
    espera = filtrado.dropna(subset=["tempo_espera"])
    if not espera.empty:
        fig = px.histogram(
            espera, x="tempo_espera", nbins=30,
            title="Distribuição do tempo de espera (Dias)",
            labels={"tempo_espera": "Dias de espera", "count": "Frequência (Registros)"},
            color_discrete_sequence=["#3b82f6"]
        )
        st.plotly_chart(ajustar_grafico(fig), use_container_width=True)
    else:
        st.info("Não há dados de tempo de espera válidos para os filtros atuais.")

with dir:
    risco = filtrado.groupby("classificacao_risco", dropna=False).size().reset_index(name="registros").sort_values("registros", ascending=False)
    fig = px.bar(
        risco, x="classificacao_risco", y="registros",
        title="Registros por classificação de risco",
        labels={"classificacao_risco": "Classificação de Risco", "registros": "Total de Registros"},
        color_discrete_sequence=["#d97706"]
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(ajustar_grafico(fig), use_container_width=True)

# Evolução mensal
mensal_base = filtrado.dropna(subset=["data_solicitacao"]).copy()
if not mensal_base.empty:
    mensal_base["mes"] = mensal_base["data_solicitacao"].dt.to_period("M").astype(str)
    mensal = mensal_base.groupby("mes").size().reset_index(name="registros")
    fig = px.line(
        mensal, x="mes", y="registros", markers=True,
        title="Evolução de registros por mês de solicitação",
        labels={"mes": "Mês", "registros": "Registros"},
        color_discrete_sequence=["#2563eb"]
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(ajustar_grafico(fig), use_container_width=True)

# ------------------------------------------------------------
# TABELA DE RESUMO
# ------------------------------------------------------------
st.markdown('<div class="section-title">Detalhamento por Procedimento</div>', unsafe_allow_html=True)
resumo = filtrado.groupby(["servico", "procedimento"], dropna=False).agg(
    registros=("procedimento", "size"),
    espera_media=("tempo_espera", "mean"),
    espera_mediana=("tempo_espera", "median"),
).reset_index().sort_values("registros", ascending=False)

resumo["espera_media"] = resumo["espera_media"].round(1)
resumo["espera_mediana"] = resumo["espera_mediana"].round(1)

st.dataframe(resumo, use_container_width=True, hide_index=True)

st.divider()
st.caption(f"Fonte dos dados: {origem} | Painel desenvolvido para fins acadêmicos e de transparência social.")