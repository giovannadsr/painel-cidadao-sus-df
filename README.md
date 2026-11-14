# Projeto: Lista de Espera SUS-DF

## Arquivos
- `extrair_sus.py`: coleta os catálogos e registros da API, salva progresso e permite retomar.
- `app.py`: dashboard interativo em Streamlit.
- `requirements.txt`: dependências.

## 1. Instalação
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2. Extração
```bash
python extrair_sus.py
```

Os arquivos são gravados na pasta `dados_sus/`. Se a execução parar, execute novamente:
o checkpoint permite continuar de onde parou. Confira `procedimentos_com_erro.csv`.
Não apague `checkpoint.json` nem `registros_progresso.jsonl` se quiser retomar.

## 3. Dashboard local
```bash
streamlit run app.py
```

O navegador abrirá o dashboard. O CSV esperado fica em:
`dados_sus/lista_espera_sus_df.csv`

## 4. Publicação
Para protótipo com dados estritamente agregados e adequadamente anonimizados:
- repositório GitHub;
- Streamlit Community Cloud.

Para dados de saúde em nível de registro, não publique o CSV nem o dashboard aberto.
Prefira ambiente privado com autenticação e controle de acesso, após avaliação jurídica,
de privacidade e dos termos de uso da fonte.

## Limitações
A API pode mudar, limitar requisições ou não disponibilizar todas as categorias.
A extração deve ser conferida pelos logs, pelo catálogo e pelo arquivo de falhas.
A existência de uma URL pública não significa automaticamente autorização para
coleta automatizada ou redistribuição dos dados.
