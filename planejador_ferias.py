import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import random
from supabase import create_client, Client
import os

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nome das colunas na tabela
COLUNAS = ["id", "funcionario", "area", "inicio", "fim", "duracao"]

# Função para carregar dados do Supabase
def load_data():
    response = supabase.table('planejamento_ferias').select('*').execute()
    data = response.data
    return pd.DataFrame(data) if data else pd.DataFrame(columns=COLUNAS)

# Função para salvar dados no Supabase
def save_data(funcionario_data):
    try:
        response = supabase.table('planejamento_ferias').insert(funcionario_data.to_dict(orient='records')).execute()
        return response.data  # Retorna a lista de registros inseridos com seus IDs
    except Exception as e:
        st.error(f"Erro ao inserir dados: {e}")
        return []

# Função para deletar um funcionário do Supabase
def delete_funcionario(funcionario_id):
    try:
        supabase.table('planejamento_ferias').delete().eq('id', funcionario_id).execute()
    except Exception as e:
        st.error(f"Erro ao deletar funcionário: {e}")

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
            value=(jan_1, datetime(next_year, 1, 7).date()),  # Valor padrão
            min_value=jan_1,
            max_value=dec_31,
        )

        inicio, fim = inicio_fim
        duracao_dias = (fim - inicio).days

        submit_button = st.form_submit_button("Salvar")

        if submit_button:
            novo_funcionario = pd.DataFrame({
                "funcionario": [funcionario],
                "area": [area],
                "inicio": [inicio.strftime('%Y-%m-%d')],
                "fim": [fim.strftime('%Y-%m-%d')],
                "duracao": [duracao_dias]
            })

            if st.session_state.edit_mode:
                # Atualiza o funcionário existente
                st.session_state.funcionarios_data.iloc[st.session_state.edit_index, 1:] = novo_funcionario.iloc[0, 1:]
                # Atualiza no banco de dados
                funcionario_id = st.session_state.funcionarios_data.iloc[st.session_state.edit_index]["id"]
                delete_funcionario(funcionario_id)  # Remove o funcionário antigo
                inserted_data = save_data(novo_funcionario)  # Insere o novo com as atualizações
                if inserted_data:
                    novo_funcionario['id'] = [item['id'] for item in inserted_data]  # Atualiza o ID
                    st.session_state.funcionarios_data.iloc[st.session_state.edit_index, 0] = novo_funcionario['id'][0]

            else:
                # Insere novo funcionário no banco de dados
                inserted_data = save_data(novo_funcionario)
                # Atualiza o DataFrame com os IDs inseridos
                if inserted_data:
                    novo_funcionario['id'] = [item['id'] for item in inserted_data]  # Adiciona os IDs ao DataFrame
                    st.session_state.funcionarios_data = pd.concat([st.session_state.funcionarios_data, novo_funcionario], ignore_index=True)

            st.session_state.show_form = False
            reset_edit_mode()

def reset_edit_mode():
    st.session_state.edit_mode = False
    st.session_state.edit_index = None

# Função para gerar uma cor escura
def gerar_cor_escura():
    return f"#{random.randint(0, 0x333333):06x}"

# Função para exibir tabela de funcionários
def exibir_tabela():
    st.write("### Funcionários e Período de Férias")

    areas = st.session_state.funcionarios_data['area'].unique()
    selected_area = st.selectbox("Filtrar por Área", ["Todas"] + list(areas))

    data_filtrada = (st.session_state.funcionarios_data[st.session_state.funcionarios_data['area'] == selected_area]
                     if selected_area != "Todas" else st.session_state.funcionarios_data)

    col_names = ["ID", "Funcionário", "Início", "Fim", "Duração (dias)", "Editar", "Remover"]

    cols = st.columns([1, 3, 2, 2, 1, 1, 1])
    for col, name in zip(cols, col_names):
        col.write(name)

    if 'cores' not in st.session_state or st.session_state.cores is None:
        funcionarios = data_filtrada['funcionario'].unique()
        st.session_state.cores = {nome: gerar_cor_escura() for nome in funcionarios}

    cores = st.session_state.cores

    for index, row in data_filtrada.iterrows():
        cols = st.columns([1, 3, 2, 2, 1, 1, 1])
        for col, value in zip(cols, [row["id"], row["funcionario"],
                                      pd.to_datetime(row["inicio"]).strftime('%d/%m/%Y'),
                                      pd.to_datetime(row["fim"]).strftime('%d/%m/%Y'),
                                      row["duracao"]]):
            if col == cols[1]:
                cor_fundo = cores.get(row["funcionario"], gerar_cor_escura())
                col.markdown(f'<div style="background-color:{cor_fundo}; color:#FFFFFF">{value}</div>', unsafe_allow_html=True)
            else:
                col.write(value)

        if cols[5].button("✏️", key=f"edit_{index}"):
            st.session_state.edit_index = index
            st.session_state.edit_mode = True
            st.session_state.show_form = True
        
        if cols[6].button("❌", key=f"remove_{index}"):
            delete_funcionario(row["id"])
            st.session_state.funcionarios_data.drop(index, inplace=True)
            st.session_state.funcionarios_data.reset_index(drop=True, inplace=True)
            st.session_state.cores = None  # Limpar as cores para recalcular
            st.experimental_rerun()  # Recarregar a página após a exclusão

# Função para exibir calendário de férias
def exibir_calendario():
    st.markdown("---")
    st.write("### Calendário de Férias")

    if not st.session_state.funcionarios_data.empty:
        primeira_data = pd.to_datetime(st.session_state.funcionarios_data['inicio'].min())
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
        "eventMaxStack": 10,
        "eventDisplay": "block",
        "locale": "pt-BR"
    }

    if 'cores' not in st.session_state:
        funcionarios = st.session_state.funcionarios_data['funcionario'].unique()
        st.session_state.cores = {nome: gerar_cor_escura() for nome in funcionarios}

    cores = st.session_state.cores if st.session_state.cores is not None else {}

    eventos = [
        {
            "title": f"{row['funcionario']} (Férias)",
            "start": pd.to_datetime(row['inicio']).strftime('%Y-%m-%d'),
            "end": (pd.to_datetime(row['fim']) + timedelta(days=1)).strftime('%Y-%m-%d'),
            "backgroundColor": cores.get(row['funcionario'], gerar_cor_escura()),
            "textColor": "#FFFFFF"
        }
        for _, row in st.session_state.funcionarios_data.iterrows()
    ]

    calendar(events=eventos, options=calendar_options)

# Inicialização
st.title(":palm_tree: Planejamento de Férias")

if 'funcionarios_data' not in st.session_state:
    st.session_state.funcionarios_data = load_data()

if st.session_state.funcionarios_data.empty:
    st.session_state.funcionarios_data = pd.DataFrame(columns=COLUNAS)

st.session_state.setdefault('edit_mode', False)
st.session_state.setdefault('edit_index', None)
st.session_state.setdefault('show_form', False)

with st.expander("Adicionar Novo Funcionário", expanded=st.session_state.show_form):
    if st.button("Adicionar Novo Funcionário"):
        st.session_state.show_form = True
        reset_edit_mode()

    if st.session_state.show_form:
        gerenciar_funcionarios()

if not st.session_state.funcionarios_data.empty:
    exibir_tabela()
    exibir_calendario()
