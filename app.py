import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Painel da Lista de Espera SUS-DF",
    page_icon="🏥",
    layout="wide"
)

st.title("Painel da Lista de Espera do SUS-DF")
st.caption(
    "Painel exploratório baseado em dados agregados. "
    "A data de atualização deve ser informada pelo responsável pela coleta."
)

ARQUIVO = Path("dados_sus/lista_espera_sus_df.csv")

arquivo_upload = st.sidebar.file_uploader(
    "Ou carregue um CSV",
    type=["csv"]
)

try:
    if arquivo_upload is not None:
        df = pd.read_csv(arquivo_upload, sep=";", encoding="utf-8-sig")
    elif ARQUIVO.exists():
        df = pd.read_csv(ARQUIVO, sep=";", encoding="utf-8-sig")
    else:
        st.warning(
            "Arquivo CSV não encontrado. Execute extrair_sus.py "
            "ou carregue um CSV na barra lateral."
        )
        st.stop()
except Exception as erro:
    st.error(f"Não foi possível ler o CSV: {erro}")
    st.stop()

colunas_obrigatorias = [
    "servico", "codigo_procedimento", "procedimento",
    "posicao", "classificacao_risco", "data_solicitacao",
    "tempo_espera"
]
faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
if faltantes:
    st.error(f"Colunas ausentes no arquivo: {faltantes}")
    st.stop()

df["tempo_espera"] = pd.to_numeric(df["tempo_espera"], errors="coerce")
df["posicao"] = pd.to_numeric(df["posicao"], errors="coerce")
df["classificacao_risco"] = df["classificacao_risco"].astype("string")
df["data_solicitacao"] = pd.to_datetime(
    df["data_solicitacao"], errors="coerce"
)

# Filtros
st.sidebar.header("Filtros")
servicos = sorted(df["servico"].dropna().astype(str).unique())
servicos_sel = st.sidebar.multiselect(
    "Serviço", servicos, default=servicos
)

filtrado = df[df["servico"].astype(str).isin(servicos_sel)].copy()

procedimentos = sorted(
    filtrado["procedimento"].dropna().astype(str).unique()
)
procedimentos_sel = st.sidebar.multiselect(
    "Procedimento", procedimentos
)
if procedimentos_sel:
    filtrado = filtrado[
        filtrado["procedimento"].astype(str).isin(procedimentos_sel)
    ]

riscos = sorted(
    filtrado["classificacao_risco"].dropna().astype(str).unique()
)
riscos_sel = st.sidebar.multiselect("Classificação de risco", riscos)
if riscos_sel:
    filtrado = filtrado[
        filtrado["classificacao_risco"].astype(str).isin(riscos_sel)
    ]

if filtrado.empty:
    st.info("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

# Indicadores
total = len(filtrado)
media_espera = filtrado["tempo_espera"].mean()
mediana_espera = filtrado["tempo_espera"].median()
procedimentos_count = filtrado["codigo_procedimento"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros na seleção", f"{total:,}".replace(",", "."))
c2.metric(
    "Tempo médio de espera",
    "—" if pd.isna(media_espera) else f"{media_espera:,.0f} dias"
)
c3.metric(
    "Mediana de espera",
    "—" if pd.isna(mediana_espera) else f"{mediana_espera:,.0f} dias"
)
c4.metric("Procedimentos distintos", f"{procedimentos_count:,}")

st.divider()

# Gráficos
esq, dir = st.columns(2)

with esq:
    por_servico = (
        filtrado.groupby("servico", dropna=False)
        .size().reset_index(name="registros")
        .sort_values("registros", ascending=False)
    )
    fig = px.bar(
        por_servico, x="servico", y="registros",
        title="Registros por tipo de serviço",
        labels={"servico": "Serviço", "registros": "Registros"}
    )
    st.plotly_chart(fig, use_container_width=True)

with dir:
    top_proc = (
        filtrado.groupby("procedimento", dropna=False)
        .size().reset_index(name="registros")
        .nlargest(15, "registros")
    )
    fig = px.bar(
        top_proc.sort_values("registros"),
        x="registros", y="procedimento", orientation="h",
        title="15 procedimentos com mais registros",
        labels={"procedimento": "Procedimento", "registros": "Registros"}
    )
    st.plotly_chart(fig, use_container_width=True)

esq, dir = st.columns(2)

with esq:
    espera = filtrado.dropna(subset=["tempo_espera"])
    if not espera.empty:
        fig = px.histogram(
            espera, x="tempo_espera", nbins=30,
            title="Distribuição do tempo de espera",
            labels={"tempo_espera": "Tempo de espera (dias)"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não há tempos de espera válidos para os filtros atuais.")

with dir:
    risco = (
        filtrado.groupby("classificacao_risco", dropna=False)
        .size().reset_index(name="registros")
    )
    fig = px.bar(
        risco, x="classificacao_risco", y="registros",
        title="Registros por classificação de risco",
        labels={
            "classificacao_risco": "Classificação",
            "registros": "Registros"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

# Evolução mensal das solicitações
mensal = filtrado.dropna(subset=["data_solicitacao"]).copy()
if not mensal.empty:
    mensal["mes"] = mensal["data_solicitacao"].dt.to_period("M").astype(str)
    mensal = mensal.groupby("mes").size().reset_index(name="solicitacoes")
    fig = px.line(
        mensal, x="mes", y="solicitacoes", markers=True,
        title="Solicitações por mês",
        labels={"mes": "Mês", "solicitacoes": "Registros"}
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Resumo por procedimento")
resumo = (
    filtrado.groupby(
        ["servico", "procedimento"], dropna=False
    )
    .agg(
        registros=("procedimento", "size"),
        espera_media=("tempo_espera", "mean"),
        espera_mediana=("tempo_espera", "median")
    )
    .reset_index()
    .sort_values("registros", ascending=False)
)
st.dataframe(resumo, use_container_width=True, hide_index=True)

st.caption(
    "Atenção: os indicadores descrevem os registros disponíveis na extração. "
    "Não representam, por si só, o tempo futuro até o atendimento nem "
    "a situação atualizada em tempo real."
)
