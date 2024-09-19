import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# Configuração do Google Sheets
SHEET_NAME = 'planejamento_ferias'  # Substitua pelo nome da sua planilha
SHEET_ID = '1niEXvLi2C5qXOXy2bn5G1i-2L4UBPBiKlcGO_9LK5nw'  # ID da sua planilha

# Configurações de API do Google Sheets
def configurar_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Carrega as credenciais do segredo do GitHub Actions ou variável de ambiente
    credentials_info = os.getenv('GOOGLE_CREDENTIALS')  # Acessa o segredo no ambiente
    creds_dict = json.loads(credentials_info)  # Converte o JSON string para um dicionário

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    return client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Nome das colunas na planilha
COLUNAS = ["ID", "Funcionário", "Área", "Início", "Fim", "Duração (dias)"]

# Função para carregar dados do Google Sheets
def load_data():
    sheet = configurar_gspread()
    data = sheet.get_all_records()
    df = pd.DataFrame(data, columns=COLUNAS)
    if df.empty:
        df = pd.DataFrame(columns=COLUNAS)
    else:
        df['Duração (dias)'] = df['Duração (dias)'].astype(float).fillna(0).astype(int)
    return df

# Função para salvar dados no Google Sheets
def save_data(data):
    sheet = configurar_gspread()
    sheet.clear()  # Limpa todos os dados existentes
    sheet.append_row(COLUNAS)  # Adiciona o cabeçalho
    for index, row in data.iterrows():
        sheet.append_row(row.tolist())

# Função para adicionar ou editar funcionário
def gerenciar_funcionarios():
    with st.form(key='form'):
        funcionario = st.text_input("Nome do Funcionário", "")
        area = st.text_input("Área", "")
        
        today = datetime.now()
        next_year = today.year + 1
        jan_1 = datetime(next_year, 1, 1).date()
        dec_31 = datetime(next_year, 12, 31).date()

        inicio_fim = st.date_input(
            "Selecione o período de férias",
            format="DD/MM/YYYY",
            value=(jan_1, datetime(next_year, 1, 7).date()),  # Valor padrão
            min_value=jan_1,
            max_value=dec_31,
        )
        
        inicio, fim = inicio_fim
        
        duracao_dias = (fim - inicio).days

        if st.form_submit_button("Salvar"):
            novo_funcionario = pd.DataFrame({
                "ID": [len(st.session_state.funcionarios_data) + 1],
                "Funcionário": [funcionario],
                "Área": [area],
                "Início": [inicio.strftime('%d/%m/%Y')],
                "Fim": [fim.strftime('%d/%m/%Y')],
                "Duração (dias)": [duracao_dias]
            })

            if st.session_state.edit_mode:
                st.session_state.funcionarios_data.iloc[st.session_state.edit_index] = novo_funcionario.iloc[0]
            else:
                st.session_state.funcionarios_data = pd.concat([st.session_state.funcionarios_data, novo_funcionario], ignore_index=True)

            save_data(st.session_state.funcionarios_data)
            st.session_state.show_form = False
            st.rerun()  # Força a atualização da página

# Função para gerar uma cor escura
def gerar_cor_escura():
    return f"#{random.randint(0, 0x333333):06x}"

# Função para exibir tabela de funcionários
def exibir_tabela():
    st.write("### Funcionários e Período de Férias")
    
    areas = st.session_state.funcionarios_data['Área'].unique()
    selected_area = st.selectbox("Filtrar por Área", ["Todas"] + list(areas))
    
    if selected_area != "Todas":
        data_filtrada = st.session_state.funcionarios_data[st.session_state.funcionarios_data['Área'] == selected_area]
    else:
        data_filtrada = st.session_state.funcionarios_data
    
    col_names = ["ID", "Funcionário", "Início", "Fim", "Duração (dias)", "Editar", "Remover"]
    
    cols = st.columns([1, 3, 2, 2, 1, 1, 1])
    for col, name in zip(cols, col_names):
        col.write(name)

    # Certifique-se de que o dicionário de cores está inicializado corretamente
    if 'cores' not in st.session_state or st.session_state.cores is None:
        funcionarios = data_filtrada['Funcionário'].unique()
        st.session_state.cores = {nome: gerar_cor_escura() for nome in funcionarios}

    cores = st.session_state.cores

    for index, row in data_filtrada.iterrows():
        cols = st.columns([1, 3, 2, 2, 1, 1, 1])
        for col, value in zip(cols, [row["ID"], row["Funcionário"], 
                                    pd.to_datetime(row["Início"]).strftime('%d/%m/%Y'), 
                                    pd.to_datetime(row["Fim"]).strftime('%d/%m/%Y'), 
                                    row["Duração (dias)"]] ):
            if col == cols[1]:
                cor_fundo = cores.get(row["Funcionário"], gerar_cor_escura())  # Gera uma cor se não existir
                cor_texto = "#FFFFFF"  # Texto branco para fundo escuro
                col.markdown(f'<div style="background-color:{cor_fundo}; color:{cor_texto}">{value}</div>', unsafe_allow_html=True)
            else:
                col.write(value)

        if cols[5].button("✏️", key=f"edit_{index}"):
            st.session_state.edit_index = index
            st.session_state.edit_mode = True
            st.session_state.show_form = True
        if cols[6].button("❌", key=f"remove_{index}"):
            st.session_state.funcionarios_data.drop(index, inplace=True)
            st.session_state.funcionarios_data.reset_index(drop=True, inplace=True)
            save_data(st.session_state.funcionarios_data)
            st.session_state.cores = None  # Limpar as cores para garantir a recalculação
            st.rerun()  # Força a atualização da página


# Função para exibir calendário de férias
def exibir_calendario():
    st.markdown("---")
    st.write("### Calendário de Férias")

    if not st.session_state.funcionarios_data.empty:
        primeira_data = pd.to_datetime(st.session_state.funcionarios_data['Início'].min(), format='%d/%m/%Y')
    else:
        primeira_data = datetime(2025, 1, 1)
    
    calendar_options = {
        "editable": "true",
        "selectable": "true",
        "initialView": "dayGridMonth",
        "initialDate": primeira_data.strftime('%Y-%m-%d'),
        "headerToolbar": {
            "left": "dayGridMonth,multiMonthYear",
            "center": "title",
            "right": "prev,next",
        },
        "eventMaxStack": 10,  # Número máximo de eventos visíveis antes de agrupá-los
        "eventDisplay": "block",  # Garantir que eventos sejam exibidos como blocos
        "locale": "pt-BR"
    }
    
    if 'cores' not in st.session_state:
        funcionarios = st.session_state.funcionarios_data['Funcionário'].unique()
        st.session_state.cores = {nome: gerar_cor_escura() for nome in funcionarios}

    cores = st.session_state.cores
    
    eventos = [
        {
            "title": f"{row['Funcionário']} (Férias)",
            "start": pd.to_datetime(row['Início'], format='%d/%m/%Y').strftime('%Y-%m-%d'),
            "end": (pd.to_datetime(row['Fim'], format='%d/%m/%Y') + timedelta(days=1)).strftime('%Y-%m-%d'),
            "backgroundColor": cores[row['Funcionário']],
            "textColor": "#FFFFFF"  # Texto branco para fundo escuro
        } 
        for _, row in st.session_state.funcionarios_data.iterrows()
    ]
    
    calendar(events=eventos, options=calendar_options)

# Inicialização
st.title(":palm_tree: Planejamento de Férias")

if 'funcionarios_data' not in st.session_state:
    st.session_state.funcionarios_data = load_data()

st.session_state.setdefault('edit_mode', False)
st.session_state.setdefault('edit_index', None)
st.session_state.setdefault('show_form', False)

with st.expander("Adicionar Novo Funcionário", expanded=st.session_state.show_form):
    if st.button("Adicionar Novo Funcionário"):
        st.session_state.show_form = True
        st.session_state.edit_mode = False

    if st.session_state.show_form:
        gerenciar_funcionarios()

if not st.session_state.funcionarios_data.empty:
    exibir_tabela()
    exibir_calendario()
