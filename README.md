# Aplicação de Planejamento de Férias

## Introdução

Essa aplicação foi desenvolvida utilizando o Streamlit e tem como objetivo ajudar na gestão de férias dos funcionários de uma empresa. Com ela, é possível adicionar, editar e remover períodos de férias, além de visualizar essas informações em uma tabela e em um calendário interativo.

## Pré-requisitos

Antes de começar a utilizar a aplicação, é necessário garantir que os seguintes itens estejam instalados:

1. **Python 3.8+**: Certifique-se de ter o Python instalado. [Download Python](https://www.python.org/downloads/).
2. **Bibliotecas Python necessárias**: As seguintes bibliotecas serão usadas:
   - `streamlit`
   - `pandas`
   - `gspread`
   - `oauth2client`
   - `streamlit_calendar`
   
   Você pode instalar todas elas com o comando abaixo:
   ```bash
   pip install streamlit pandas gspread oauth2client streamlit_calendar
   ```

## Configuração

### 1. Credenciais do Google Sheets

A aplicação usa o Google Sheets para armazenar os dados dos funcionários e seus períodos de férias. Para configurar isso, você precisa:

- Criar um projeto no [Google Cloud Console](https://console.cloud.google.com/).
- Ativar a API do Google Sheets.
- Criar uma conta de serviço e gerar um arquivo de credenciais `credentials.json`.

Após obter o arquivo `credentials.json`, coloque-o no mesmo diretório da aplicação.

### 2. Configurar a Planilha no Google Sheets

- Crie uma planilha no Google Sheets com o nome que você preferir. A planilha deve ter as seguintes colunas:
  - `ID`
  - `Funcionário`
  - `Área`
  - `Início`
  - `Fim`
  - `Duração (dias)`
  
- Anote o **ID** da planilha. Ele pode ser encontrado na URL da planilha, por exemplo: 
  ```
  https://docs.google.com/spreadsheets/d/1niEXvLi2C5qXOXy2bn5G1i-2L4UBPBiKlcGO_9LK5nw/edit
  ```
  O ID será `1niEXvLi2C5qXOXy2bn5G1i-2L4UBPBiKlcGO_9LK5nw`.

### 3. Configurar o Código

No arquivo Python, atualize as seguintes informações:

- `SHEET_NAME`: Substitua pelo nome da sua planilha.
- `SHEET_ID`: Insira o ID da sua planilha.

## Executando a Aplicação

Para rodar a aplicação, basta usar o comando abaixo no terminal:

```bash
streamlit run app.py
```

A aplicação será aberta no seu navegador.

## Funcionalidades

### 1. Adicionar Funcionário

- Clique no botão "Adicionar Novo Funcionário".
- Preencha as informações do funcionário, incluindo nome, área e o período de férias.
- Clique em "Salvar" para registrar as informações na planilha.

### 2. Editar Funcionário

- Na tabela de funcionários, clique no botão "✏️" ao lado do funcionário que deseja editar.
- Altere as informações e clique em "Salvar" novamente.

### 3. Remover Funcionário

- Para remover um funcionário, clique no botão "❌" ao lado do nome do funcionário na tabela.

### 4. Visualizar o Calendário de Férias

- Abaixo da tabela de funcionários, você verá um calendário com os períodos de férias destacados. As cores são geradas automaticamente para cada funcionário.

## Observações

- **Armazenamento de dados**: Os dados são armazenados diretamente no Google Sheets, e todas as alterações feitas na aplicação são automaticamente refletidas na planilha.
- **Filtro de áreas**: Você pode filtrar os funcionários por área usando o seletor acima da tabela.
- **Personalização de cores**: As cores dos eventos no calendário são geradas automaticamente para cada funcionário e visam facilitar a visualização dos períodos de férias.
