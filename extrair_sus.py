"""
Extrator da lista de espera SUS-DF (MPDFT)
- Consulta os catálogos de Consulta, Cirurgia eletiva e Exame.
- Percorre as páginas de cada procedimento.
- Salva progresso após cada página e permite retomar a execução.
- Exporta somente campos selecionados, sem nome, CNS, telefone ou nascimento.

Antes de usar:
1) Verifique os termos de uso e a autorização aplicável para reutilização dos dados.
2) Não publique dados individualizados de saúde. Use agregações no dashboard.
3) Execute com intervalo entre requisições e respeite eventuais bloqueios da API.
"""

import csv
import json
import random
import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.mpdft.mp.br/acompanhamento-sus-df/api/lista-de-espera/"
SERVICOS = {
    "Consulta": "Consulta",
    "Cirurgia eletiva": "Cirurgia-eletiva",
    "Exame": "Exame",
}

TAMANHO_PAGINA = 50       # manter 10 inicialmente; só aumentar se a API aceitar
PAUSA_ENTRE_PAGINAS = 1.0
MAX_TENTATIVAS = 6

PASTA = Path("dados_sus")
PASTA.mkdir(exist_ok=True)

ARQUIVO_JSONL = PASTA / "registros_progresso.jsonl"
ARQUIVO_CHECKPOINT = PASTA / "checkpoint.json"
ARQUIVO_CATALOGO = PASTA / "catalogo_procedimentos.csv"
ARQUIVO_FINAL = PASTA / "lista_espera_sus_df.csv"
ARQUIVO_FALHAS = PASTA / "procedimentos_com_erro.csv"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; pesquisa-academica/1.0)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.mpdft.mp.br/acompanhamento-sus-df/lista-de-espera",
})


def salvar_json_atomico(caminho: Path, conteudo):
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    temporario.replace(caminho)


def carregar_checkpoint():
    if ARQUIVO_CHECKPOINT.exists():
        try:
            return json.loads(ARQUIVO_CHECKPOINT.read_text(encoding="utf-8"))
        except Exception:
            print("Aviso: checkpoint inválido. Será criado um novo.")
    return {}


def requisitar_json(url, params=None):
    ultimo_erro = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = session.get(url, params=params, timeout=60)

            if resposta.status_code == 429:
                retry_after = resposta.headers.get("Retry-After")
                espera = int(retry_after) if retry_after and retry_after.isdigit() else min(120, 10 * tentativa)
                print(f"HTTP 429: limite de requisições. Aguardando {espera}s.")
                time.sleep(espera)
                continue

            if resposta.status_code in (500, 502, 503, 504):
                raise requests.HTTPError(
                    f"Erro temporário HTTP {resposta.status_code}"
                )

            resposta.raise_for_status()

            if not resposta.text.strip():
                raise ValueError("A API retornou resposta vazia.")

            try:
                return resposta.json()
            except requests.exceptions.JSONDecodeError as exc:
                trecho = resposta.text[:200].replace("\n", " ")
                raise ValueError(
                    f"Resposta não é JSON. HTTP {resposta.status_code}. "
                    f"Conteúdo inicial: {trecho}"
                ) from exc

        except (requests.RequestException, ValueError) as erro:
            ultimo_erro = erro
            espera = min(90, 5 * (2 ** (tentativa - 1))) + random.uniform(0, 2)
            print(f"Tentativa {tentativa}/{MAX_TENTATIVAS} falhou: {erro}")
            if tentativa < MAX_TENTATIVAS:
                print(f"Nova tentativa em {espera:.1f}s...")
                time.sleep(espera)

    raise RuntimeError(f"Falha após {MAX_TENTATIVAS} tentativas: {ultimo_erro}")


def primeiro_valor(item, chaves):
    for chave in chaves:
        valor = item.get(chave)
        if valor not in (None, ""):
            return valor
    return None


def normalizar_catalogo(item, servico):
    if not isinstance(item, dict):
        return None

    codigo = primeiro_valor(item, [
        "codigo", "codigoProcedimento", "codigo_procedimento",
        "id", "value", "codProcedimento"
    ])
    descricao = primeiro_valor(item, [
        "descricao", "descricaoProcedimento", "nome",
        "nomeProcedimento", "label", "text", "procedimento"
    ])

    if codigo is None:
        return None

    return {
        "servico": servico,
        "codigo_procedimento": str(codigo),
        "descricao_procedimento": str(descricao or "")
    }


def salvar_pagina_jsonl(registros):
    if not registros:
        return
    with ARQUIVO_JSONL.open("a", encoding="utf-8") as arquivo:
        for registro in registros:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
        arquivo.flush()


def exportar_resultados():
    colunas = [
        "servico", "codigo_procedimento", "descricao_procedimento",
        "procedimento", "grupo_procedimento", "posicao",
        "classificacao_risco", "data_solicitacao", "tempo_espera"
    ]

    if ARQUIVO_JSONL.exists():
        dados = []
        with ARQUIVO_JSONL.open("r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if linha:
                    dados.append(json.loads(linha))

        df = pd.DataFrame(dados, columns=colunas)
        if not df.empty:
            # Remove apenas linhas integralmente repetidas; não deduplica por pessoa.
            df = df.drop_duplicates()
            df.to_csv(
                ARQUIVO_FINAL, index=False, sep=";", encoding="utf-8-sig"
            )
    else:
        df = pd.DataFrame(columns=colunas)
        df.to_csv(ARQUIVO_FINAL, index=False, sep=";", encoding="utf-8-sig")

    return df


def main():
    checkpoint = carregar_checkpoint()
    catalogo_completo = []
    falhas = []

    for nome_servico, parametro_servico in SERVICOS.items():
        print(f"\n===== CATÁLOGO: {nome_servico} =====")
        url_catalogo = BASE + "combo-procedimentos/"

        try:
            catalogo_api = requisitar_json(
                url_catalogo,
                params={"servico": parametro_servico}
            )
        except Exception as erro:
            falhas.append({
                "servico": nome_servico,
                "codigo": "",
                "offset": "",
                "etapa": "catalogo",
                "erro": str(erro)
            })
            print(f"Não foi possível obter o catálogo de {nome_servico}: {erro}")
            continue

        if isinstance(catalogo_api, dict):
            # Algumas APIs encapsulam a lista em uma chave.
            for chave in ("dados", "items", "results", "procedimentos"):
                if isinstance(catalogo_api.get(chave), list):
                    catalogo_api = catalogo_api[chave]
                    break

        if not isinstance(catalogo_api, list):
            falhas.append({
                "servico": nome_servico,
                "codigo": "",
                "offset": "",
                "etapa": "catalogo",
                "erro": f"Formato inesperado: {type(catalogo_api).__name__}"
            })
            continue

        procedimentos = []
        for item in catalogo_api:
            normalizado = normalizar_catalogo(item, nome_servico)
            if normalizado:
                procedimentos.append(normalizado)

        if not procedimentos:
            exemplo = repr(catalogo_api[:2])[:1000]
            falhas.append({
                "servico": nome_servico,
                "codigo": "",
                "offset": "",
                "etapa": "catalogo",
                "erro": f"Não identifiquei os campos de código. Amostra: {exemplo}"
            })
            print("Não foi possível reconhecer os campos do catálogo.")
            continue

        catalogo_completo.extend(procedimentos)
        print(f"Procedimentos identificados: {len(procedimentos)}")

        for proc in procedimentos:
            codigo = proc["codigo_procedimento"]
            descricao = proc["descricao_procedimento"]
            chave = f"{parametro_servico}|{codigo}"

            estado = checkpoint.get(chave, {})
            if estado.get("concluido"):
                print(f"Já concluído: {nome_servico} | {codigo}")
                continue

            offset = int(estado.get("proximo_offset", 0))
            print(f"\nExtraindo {nome_servico} | {codigo} | início offset={offset}")

            while True:
                params = {
                    "codigoDeSolicitacao": "null",
                    "servico": parametro_servico,
                    "procedimento": codigo,
                    "unidade": "null",
                    "prioridade": "null",
                    "offset": offset,
                    "next": TAMANHO_PAGINA,
                }

                try:
                    pagina = requisitar_json(BASE, params=params)
                    if not isinstance(pagina, list):
                        raise ValueError(
                            f"Resposta da lista não é uma lista: {type(pagina).__name__}"
                        )
                except Exception as erro:
                    falhas.append({
                        "servico": nome_servico,
                        "codigo": codigo,
                        "offset": offset,
                        "etapa": "lista",
                        "erro": str(erro)
                    })
                    print(f"Falha neste procedimento; será retomado depois: {erro}")
                    break

                if len(pagina) == 0:
                    checkpoint[chave] = {
                        "proximo_offset": offset,
                        "concluido": True
                    }
                    salvar_json_atomico(ARQUIVO_CHECKPOINT, checkpoint)
                    print("Sem mais registros. Procedimento concluído.")
                    break

                linhas = []
                for registro in pagina:
                    if not isinstance(registro, dict):
                        continue

                    # Lista permitida: nenhum nome, CNS, telefone ou nascimento.
                    linhas.append({
                        "servico": nome_servico,
                        "codigo_procedimento": codigo,
                        "descricao_procedimento": descricao,
                        "procedimento": registro.get("procedimento"),
                        "grupo_procedimento": registro.get("nomeGrupoProcedimento"),
                        "posicao": registro.get("posicao"),
                        "classificacao_risco": registro.get("classificacaoDeRisco"),
                        "data_solicitacao": registro.get("dataSolicitacao"),
                        "tempo_espera": registro.get("tempoDeEspera"),
                    })

                # Primeiro grava os dados; depois atualiza o checkpoint.
                salvar_pagina_jsonl(linhas)
                offset += len(pagina)

                checkpoint[chave] = {
                    "proximo_offset": offset,
                    "concluido": len(pagina) < TAMANHO_PAGINA
                }
                salvar_json_atomico(ARQUIVO_CHECKPOINT, checkpoint)

                print(f"Página salva. Próximo offset: {offset}")

                if len(pagina) < TAMANHO_PAGINA:
                    print("Última página do procedimento.")
                    break

                time.sleep(PAUSA_ENTRE_PAGINAS)

            # Atualiza o CSV consolidado mesmo se algum procedimento falhar.
            exportar_resultados()
            time.sleep(PAUSA_ENTRE_PAGINAS)

    # Salva catálogo, falhas e base consolidada.
    df_catalogo = pd.DataFrame(catalogo_completo).drop_duplicates()
    if not df_catalogo.empty:
        df_catalogo.to_csv(
            ARQUIVO_CATALOGO, index=False, sep=";", encoding="utf-8-sig"
        )

    pd.DataFrame(falhas).to_csv(
        ARQUIVO_FALHAS, index=False, sep=";", encoding="utf-8-sig"
    )

    df_final = exportar_resultados()

    print("\n========== RESUMO ==========")
    print(f"Registros salvos: {len(df_final):,}")
    print(f"Procedimentos no catálogo: {len(df_catalogo):,}")
    print(f"Falhas registradas nesta execução: {len(falhas):,}")
    print(f"CSV final: {ARQUIVO_FINAL}")
    print(f"Catálogo: {ARQUIVO_CATALOGO}")
    print(f"Falhas: {ARQUIVO_FALHAS}")
    print("\nExecute novamente o script para retomar procedimentos incompletos.")


if __name__ == "__main__":
    main()
