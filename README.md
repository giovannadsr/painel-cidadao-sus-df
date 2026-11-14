# 🏥 Painel Cidadão | Saúde Transparente (SUS-DF)

[![Python](https://img.shields.io/badge/Python-3.8%252B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)](https://streamlit.io/)
[![Licença Acadêmica](https://img.shields.io/badge/Licenca-Academica-green.svg)]()
[![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-orange.svg)]()

> **Projeto Integrador 1** • Curso de **Ciências de Dados** (UFMS Digital)  
> **Tema:** Transparência ativa e controle social das filas de espera do Sistema Único de Saúde no Distrito Federal (SUS-DF).

---

## 📋 Sobre o Projeto

Este repositório abriga o código-fonte e o pipeline de dados do **Painel Cidadão**, uma aplicação web interativa desenvolvida com o objetivo de mitigar a assimetria de informação entre a gestão pública e o cidadão. 

O sistema traduz bases de dados brutas e complexas do Complexo Regulador de Saúde do Distrito Federal (extraídas dos portais do MPDFT e SES-DF) em painéis visuais intuitivos, permitindo que a comunidade acompanhe indicadores de filas para **consultas, exames e cirurgias eletivas** de forma totalmente acessível, em conformidade com a Lei de Acesso à Informação (Lei nº 12.527/2011).

---

## 🛠️ Estrutura do Repositório

```text
├── dados_sus/                     # Diretório para bases de dados locais e checkpoints
│   └── lista_espera_sus_df.csv    # (Ignorado no Git se > 50MB) Base tratada do extrator
├── app_painel_cidadao.py          # Aplicação principal em Streamlit (Dashboard Interativo)
├── extrair_sus.py                 # Script de ETL para automação, paginação e consumo da API
├── validar_base.py                # Script de auditoria, consistência e métricas de qualidade
├── requirements.txt               # Dependências e bibliotecas do projeto Python
└── .gitignore                     # Configuração de arquivos ignorados pelo versionamento
```

---

## ⚙️ Tecnologias e Bibliotecas Utilizadas

* **Python 3.8+** (Linguagem principal)
* **Streamlit** (Framework para construção da interface web interativa)
* **Pandas / NumPy** (Manipulação, limpeza estrutural e pipeline ETL)
* **Plotly** (Geração de gráficos dinâmicos e responsivos com suporte a temas)
* **Requests** (Requisições HTTP para consumo e paginação de dados institucionais)

---

## 🚀 Como Executar o Projeto Localmente

Siga os passos abaixo no seu terminal para configurar o ambiente e rodar o painel na sua máquina:

### 1. Clonar o repositório
```bash
git clone https://github.com/giovannadsr/painel-cidadao-sus-df.git
cd painel-cidadao-sus-df
```

### 2. Criar e ativar um ambiente virtual
* **No Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
* **No macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o Dashboard
```bash
streamlit run app_painel_cidadao.py
```
O navegador abrirá automaticamente no endereço `http://localhost:8501`.

---

## ☁️ Implantação em Nuvem (Streamlit Community Cloud)

Como os arquivos CSV consolidados da lista de espera possuem volumetria elevada (acima do limite de rastreio otimizado do GitHub), o deploy na nuvem segue o procedimento padrão:

1. Suba o código atualizado (`app_painel_cidadao.py`, `requirements.txt` e `.gitignore`) para o seu repositório no GitHub.
2. Acesse [share.streamlit.io](https://share.streamlit.io/) e faça login com sua conta do GitHub.
3. Clique em **New app** e selecione o repositório `giovannadsr/painel-cidadao-sus-df`.
4. Defina o arquivo principal como `app_painel_cidadao.py` e clique em **Deploy!**.
5. Quando o painel abrir na nuvem pela primeira vez, utilize o componente lateral de upload para carregar a base tratada (`lista_espera_sus_df.csv`) caso não deseje mantê-la vinculada ao repositório remoto.

---

## 📌 Notas Metodológicas e Privacidade

* **Anonimização (LGPD):** O pipeline de extração e processamento descarta rigorosamente dados sensíveis e individualizados (como nomes, cartões do SUS, telefones e datas de nascimento), focando estritamente em indicadores agregados estatísticos.
* **Finalidade Acadêmica:** Este projeto faz parte das diretrizes de curricularização da extensão universitária, não possuindo vínculo comercial ou institucional direto com a Secretaria de Saúde do DF.