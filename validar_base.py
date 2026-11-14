
import json
from pathlib import Path

import pandas as pd

# ==========================================
# CONFIGURAÇÕES
# ==========================================

PASTA = Path("dados_sus")

ARQUIVO_BASE = PASTA / "lista_espera_sus_df.csv"
ARQUIVO_CATALOGO = PASTA / "catalogo_procedimentos.csv"
ARQUIVO_FALHAS = PASTA / "procedimentos_com_erro.csv"
ARQUIVO_CHECKPOINT = PASTA / "checkpoint.json"

ARQUIVO_RELATORIO = PASTA / "relatorio_validacao.txt"

SERVICOS_ESPERADOS = {
    "Consulta",
    "Cirurgia eletiva",
    "Exame"
}

COLUNAS_ESPERADAS = [
    "servico",
    "codigo_procedimento",
    "descricao_procedimento",
    "procedimento",
    "grupo_procedimento",
    "posicao",
    "classificacao_risco",
    "data_solicitacao",
    "tempo_espera"
]

# ==========================================
# LEITURA DOS ARQUIVOS
# ==========================================

if not ARQUIVO_BASE.exists():
    raise FileNotFoundError(
        f"Arquivo não encontrado: {ARQUIVO_BASE}"
    )

df = pd.read_csv(
    ARQUIVO_BASE,
    sep=";",
    encoding="utf-8-sig"
)

print("\nBASE CARREGADA COM SUCESSO")
print("=" * 50)

# ==========================================
# 1. ESTRUTURA DA BASE
# ==========================================

print("\n1. ESTRUTURA")

print("Quantidade de registros:", len(df))
print("Quantidade de colunas:", len(df.columns))

colunas_ausentes = [
    coluna for coluna in COLUNAS_ESPERADAS
    if coluna not in df.columns
]

if colunas_ausentes:
    print("COLUNAS AUSENTES:", colunas_ausentes)
else:
    print("Todas as colunas esperadas estão presentes.")

# ==========================================
# 2. DISTRIBUIÇÃO DOS SERVIÇOS
# ==========================================

print("\n2. DISTRIBUIÇÃO DOS SERVIÇOS")

if "servico" in df.columns:

    distribuicao = df["servico"].value_counts(dropna=False)

    print(distribuicao.to_string())

    encontrados = set(
        df["servico"].dropna().astype(str).unique()
    )

    ausentes = SERVICOS_ESPERADOS - encontrados

    print("\nServiços encontrados:", encontrados)
    print("Serviços ausentes:", ausentes)

# ==========================================
# 3. PROCEDIMENTOS
# ==========================================

print("\n3. PROCEDIMENTOS")

if {"servico", "codigo_procedimento"}.issubset(df.columns):

    procedimentos = (
        df.groupby("servico")["codigo_procedimento"]
        .nunique()
    )

    print(procedimentos.to_string())

# ==========================================
# 4. VALORES AUSENTES
# ==========================================

print("\n4. VALORES AUSENTES")

ausentes = df.isna().sum()

percentuais = (
    df.isna().mean() * 100
).round(2)

for coluna in df.columns:
    print(
        f"{coluna}: {ausentes[coluna]} "
        f"({percentuais[coluna]}%)"
    )

# ==========================================
# 5. DUPLICIDADES
# ==========================================

print("\n5. DUPLICIDADES")

duplicados = df.duplicated().sum()

print("Linhas integralmente duplicadas:", duplicados)

# ==========================================
# 6. CONSISTÊNCIA DOS DADOS
# ==========================================

print("\n6. CONSISTÊNCIA")

if "tempo_espera" in df.columns:

    tempo = pd.to_numeric(
        df["tempo_espera"],
        errors="coerce"
    )

    print("Tempo de espera médio:", tempo.mean())
    print("Tempo de espera mediano:", tempo.median())
    print("Tempos negativos:", (tempo < 0).sum())

if "posicao" in df.columns:

    posicao = pd.to_numeric(
        df["posicao"],
        errors="coerce"
    )

    print("Posições não numéricas:", posicao.isna().sum())
    print("Posições menores que zero:", (posicao < 0).sum())

if "data_solicitacao" in df.columns:

    datas = pd.to_datetime(
        df["data_solicitacao"],
        errors="coerce"
    )

    print("Datas inválidas:", datas.isna().sum())

# ==========================================
# 7. CONFERÊNCIA DO CATÁLOGO
# ==========================================

print("\n7. CONFERÊNCIA DO CATÁLOGO")

if ARQUIVO_CATALOGO.exists():

    catalogo = pd.read_csv(
        ARQUIVO_CATALOGO,
        sep=";",
        encoding="utf-8-sig"
    )

    if {
        "servico",
        "codigo_procedimento"
    }.issubset(catalogo.columns):

        catalogo_ids = set(
            zip(
                catalogo["servico"].astype(str),
                catalogo["codigo_procedimento"].astype(str)
            )
        )

        base_ids = set(
            zip(
                df["servico"].astype(str),
                df["codigo_procedimento"].astype(str)
            )
        )

        sem_registros = catalogo_ids - base_ids

        print("Procedimentos no catálogo:", len(catalogo_ids))
        print("Procedimentos com registros:", len(base_ids))
        print(
            "Procedimentos sem registros:",
            len(sem_registros)
        )

        for item in sorted(sem_registros):
            print("Sem registros:", item)

else:
    print("Catálogo não encontrado.")

# ==========================================
# 8. CONFERÊNCIA DAS FALHAS
# ==========================================

print("\n8. FALHAS DA EXTRAÇÃO")

if ARQUIVO_FALHAS.exists():

    try:
        falhas = pd.read_csv(
            ARQUIVO_FALHAS,
            sep=";",
            encoding="utf-8-sig"
        )

        print("Falhas registradas:", len(falhas))

        if not falhas.empty:
            print(falhas["servico"].value_counts().to_string())

    except pd.errors.EmptyDataError:
        print("Arquivo de falhas vazio.")

else:
    print("Arquivo de falhas não encontrado.")

# ==========================================
# 9. CONFERÊNCIA DO CHECKPOINT
# ==========================================

print("\n9. CHECKPOINT")

if ARQUIVO_CHECKPOINT.exists():

    with open(
        ARQUIVO_CHECKPOINT,
        "r",
        encoding="utf-8"
    ) as arquivo:

        checkpoint = json.load(arquivo)

    concluidos = sum(
        1 for estado in checkpoint.values()
        if estado.get("concluido") is True
    )

    pendentes = len(checkpoint) - concluidos

    print("Procedimentos controlados:", len(checkpoint))
    print("Procedimentos concluídos:", concluidos)
    print("Procedimentos pendentes:", pendentes)

else:
    print("Checkpoint não encontrado.")

# ==========================================
# 10. RELATÓRIO FINAL
# ==========================================

print("\n10. FINALIZAÇÃO")

with open(
    ARQUIVO_RELATORIO,
    "w",
    encoding="utf-8"
) as arquivo:

    arquivo.write("RELATÓRIO DE VALIDAÇÃO DA BASE SUS-DF\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write(f"Registros: {len(df)}\n")
    arquivo.write(f"Colunas: {len(df.columns)}\n")
    arquivo.write(f"Duplicidades exatas: {duplicados}\n")
    arquivo.write("\nVALORES AUSENTES\n")
    arquivo.write(ausentes.to_string())
    arquivo.write("\n\nDISTRIBUIÇÃO DOS SERVIÇOS\n")

    if "servico" in df.columns:
        arquivo.write(
            df["servico"].value_counts().to_string()
        )

print("\nValidação concluída.")
print("Relatório salvo em:", ARQUIVO_RELATORIO)
