import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import random
from supabase import create_client, Client
import os

# Configurações do Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
COLUNAS = ["id", "funcionario", "area", "inicio", "fim", "duracao"]

# Funções auxiliares
def load_data():
    return pd.DataFrame(supabase.table('planejamento_ferias').select('*').execute().data or [], columns=COLUNAS)

def save_data(data):
    try:
        return supabase.table('planejamento_ferias').insert(data.to_dict(orient='records')).execute().data
    except Exception as e:
        st.error(f"Erro ao inserir dados: {e}")

def delete_funcionario(funcionario_id):
    try:
        supabase.table('planejamento_ferias').delete().eq('id', funcionario_id).execute()
    except Exception as e:
        st.error(f"Erro ao deletar funcionário: {e}")

def gerar_cor_escura():
    return f"#{random.randint(0, 0x333333):06x}"

def exibir_tabela(funcionarios_data):
    st.write("### Funcionários e Período de Férias")
    selected_area = st.selectbox("Filtrar por Área", ["Todas"] + list(funcionarios_data['area'].unique()))
    data_filtrada = funcionarios_data[funcionarios_data['area'] == selected_area] if selected_area != "Todas" else funcionarios_data
    
    # Exibir tabela
    for col_name in ["ID", "Funcionário", "Início", "Fim", "Duração (dias)", "Editar", "Remover"]:
        st.write(col_name)

    cores = {nome: gerar_cor_escura() for nome in data_filtrada['funcionario'].unique()}
    
    for index, row in data_filtrada.iterrows():
        cols = st.columns([1, 3, 2, 2, 1, 1, 1])
        for col, value in zip(cols, [row["id"], row["funcionario"], pd.to_datetime(row["inicio"]).strftime('%d/%m/%Y'),
                                      pd.to_datetime(row["fim"]).strftime('%d/%m/%Y'), row["duracao"]]):
            if col == cols[1]:
                col.markdown(f'<div style="background-color:{cores[row["funcionario"]]}; color:#FFFFFF">{value}</div>', unsafe_allow_html=True)
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
            st.rerun()

def gerenciar_funcionarios():
    with st.form(key='form'):
        funcionario = st.text_input("Nome do Funcionário")
        area = st.text_input("Área")
        hoje = datetime.now().date()
        periodo = st.date_input("Selecione o período de férias", (hoje, hoje + timedelta(days=7)))

        duracao = (periodo[1] - periodo[0]).days
        if st.form_submit_button("Salvar"):
            novo_funcionario = pd.DataFrame({"funcionario": [funcionario], "area": [area],
                                              "inicio": [periodo[0]], "fim": [periodo[1]], "duracao": [duracao]})
            if st.session_state.edit_mode:
                funcionario_id = st.session_state.funcionarios_data.iloc[st.session_state.edit_index]["id"]
                delete_funcionario(funcionario_id)
            inserted_data = save_data(novo_funcionario)
            if inserted_data:
                novo_funcionario['id'] = [item['id'] for item in inserted_data]
                if st.session_state.edit_mode:
                    st.session_state.funcionarios_data.iloc[st.session_state.edit_index] = novo_funcionario.iloc[0]
                else:
                    st.session_state.funcionarios_data = pd.concat([st.session_state.funcionarios_data, novo_funcionario], ignore_index=True)
            reset_edit_mode()

def reset_edit_mode():
    st.session_state.edit_mode = False
    st.session_state.edit_index = None

def exibir_calendario(funcionarios_data):
    st.write("### Calendário de Férias")
    if not funcionarios_data.empty:
        primeira_data = pd.to_datetime(funcionarios_data['inicio'].min()).strftime('%Y-%m-%d')
    else:
        primeira_data = datetime(2025, 1, 1).strftime('%Y-%m-%d')

    eventos = [{
        "title": f"{row['funcionario']} (Férias)",
        "start": pd.to_datetime(row['inicio']).strftime('%Y-%m-%d'),
        "end": (pd.to_datetime(row['fim']) + timedelta(days=1)).strftime('%Y-%m-%d'),
        "backgroundColor": gerar_cor_escura(),
        "textColor": "#FFFFFF"
    } for _, row in funcionarios_data.iterrows()]

    calendar(events=eventos, options={
        "editable": True, "initialView": "dayGridMonth", "initialDate": primeira_data,
        "headerToolbar": {"left": "dayGridMonth,multiMonthYear", "center": "title", "right": "prev,next"},
        "eventMaxStack": 10, "eventDisplay": "block", "locale": "pt-BR"
    })

# Inicialização
st.title(":palm_tree: Planejamento de Férias")
st.session_state.funcionarios_data = load_data() if 'funcionarios_data' not in st.session_state else st.session_state.funcionarios_data
st.session_state.setdefault('edit_mode', False)
st.session_state.setdefault('show_form', False)

with st.expander("Adicionar Novo Funcionário", expanded=st.session_state.show_form):
    if st.button("Adicionar Novo Funcionário"):
        st.session_state.show_form = True
        reset_edit_mode()
    if st.session_state.show_form:
        gerenciar_funcionarios()

if not st.session_state.funcionarios_data.empty:
    exibir_tabela(st.session_state.funcionarios_data)
    exibir_calendario(st.session_state.funcionarios_data)
