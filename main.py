# Arquivo: main.py
# Data: 17/02/2025 - Hora: 14h25
# IDE Cursor - claude 3.5 sonnet
# comando: streamlit run main.py

import streamlit as st
import sqlite3
from paginas.form_model import process_forms_tab
from datetime import datetime

# Configuração da página - deve ser a primeira chamada do Streamlit
st.set_page_config(
    page_title="Simulador da Pegada de Carbono do Café Torrado",
    layout="wide"
)

def authenticate_user():
    """Autentica o usuário e verifica seu perfil no banco de dados."""
    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = None

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    if not st.session_state["logged_in"]:
        st.sidebar.title("Login")
        email = st.sidebar.text_input("E-mail")
        password = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            conn = sqlite3.connect("calcpc.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, perfil, nome FROM usuarios WHERE email = ? AND senha = ?
            """, (email, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                st.session_state["logged_in"] = True
                st.session_state["user_profile"] = user[2]
                st.session_state["user_id"] = user[1]
                st.session_state["user_name"] = user[3]
                st.success(f"Login bem-sucedido! Bem-vindo, {user[3]}.")
            else:
                st.error("E-mail ou senha inválidos.")

    return st.session_state.get("logged_in", False), st.session_state.get("user_profile", None)

def show_welcome():
    """Exibe a tela de boas-vindas com informações do usuário"""
    st.title("Bem-vindo ao Sistema!")
    
    # Buscar dados do usuário e contagem de formulários
    conn = sqlite3.connect("calcpc.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, empresa 
        FROM usuarios 
        WHERE user_id = ?
    """, (st.session_state.get('user_id'),))
    user_info = cursor.fetchone()
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM forms_tab 
        WHERE user_id = ?
    """, (st.session_state.get('user_id'),))
    form_count = cursor.fetchone()[0]
    conn.close()
    
    empresa = user_info[1] if user_info[1] is not None else "Não informada"
    
    # Layout em colunas usando st.columns
    col1, col2, col3 = st.columns(3)
    
    # Coluna 1: Dados do Usuário
    with col1:
        st.markdown(f"""
            <div style="background-color: #e8f4f8; padding: 20px; border-radius: 8px;">
                <h3 style="color: #2c3e50; font-size: 20px;">Seus Dados</h3>
                <div style="color: #34495e; font-size: 16px;">
                    <p>ID: {st.session_state.get('user_id')}</p>
                    <p>Nome: {st.session_state.get('user_name')}</p>
                    <p>E-mail: {user_info[0]}</p>
                    <p>Empresa: {empresa}</p>
                    <p>Perfil: {st.session_state.get('user_profile')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 2: Atividades
    with col2:
        st.markdown(f"""
            <div style="background-color: #e8f8ef; padding: 20px; border-radius: 8px;">
                <h3 style="color: #2c3e50; font-size: 20px;">Suas Atividades</h3>
                <div style="color: #34495e; font-size: 16px;">
                    <p>Formulários Preenchidos: {form_count}</p>
                    <p>Data Atual: {datetime.now().strftime('%d/%m/%Y')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 3: Módulos
    with col3:
        modulos_html = """
            <div style="background-color: #fff8e8; padding: 20px; border-radius: 8px;">
                <h3 style="color: #2c3e50; font-size: 20px;">Módulos Disponíveis</h3>
                <div style="color: #34495e; font-size: 16px;">
                    <p>Formulário - Tipo do Café</p>
                    <p>Formulário - Moagem e Torrefação</p>
                    <p>Formulário - Embalagem</p>
                    <p>Resultados / Gráficos</p>
                    <p>Resultados SEA - Sem Etapa Agrícola</p>
                    <p>Comparação Setorial</p>
                    <p>Comparação Setorial SEA - Sem Etapa Agrícola</p>
                    <p>Análise Energética - Torrefação</p>
                </div>
            </div>
        """
        
        st.markdown(modulos_html, unsafe_allow_html=True)

def main():
    """Gerencia a navegação entre as páginas do sistema."""
    logged_in, user_profile = authenticate_user()

    if not logged_in:
        st.stop()
    
    # Titulo da página
    st.title("Simulador da Pegada de Carbono do Café Torrado")

    # Adicionar informação do usuário logado
    st.sidebar.markdown(f"""
        **Usuário:** {st.session_state.get('user_name')}  
        **ID:** {st.session_state.get('user_id')}  
        **Perfil:** {st.session_state.get('user_profile')}
    """)

    if st.sidebar.button("Logout"):
        for key in ['logged_in', 'user_profile', 'user_id', 'user_name']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.sidebar.title("Menu de Navegação")
    
    # Adicionando "Comparação Setorial" ao menu de opções
    menu_options = ["Bem-vindo", "Form - Tipo do Café", "Form - Moagem e Torrefação", 
                   "Form - Embalagem", "Resultados", "Resultados SEA", "Comparação Setorial",
                   "Comparação Setorial SEA", "Análise Energética - Torrefação"]
    
    if user_profile and user_profile.lower() == "adm":
        menu_options.append("Administração")
    
    section = st.sidebar.radio(
        "Selecione a página:",
        menu_options,
        key="menu_selection"
    )
    
    # Mapeamento das opções do menu para os valores da coluna section
    section_map = {
        "Form - Tipo do Café": "cafe",
        "Form - Moagem e Torrefação": "moagem",
        "Form - Embalagem": "embalagem",
        "Resultados": "resultados",
        "Administração": "crud"
    }
    
    # Processa a seção selecionada
    if section == "Bem-vindo":
        show_welcome()
    elif section in ["Form - Tipo do Café", "Form - Moagem e Torrefação", "Form - Embalagem"]:
        process_forms_tab(section_map[section])
    elif section == "Resultados":
        from paginas.resultados import show_results
        show_results()
    elif section == "Resultados SEA":
        from paginas.result_sea import show_results
        show_results()
    elif section == "Comparação Setorial":
        from paginas.result_setorial import show_results
        show_results()
    elif section == "Comparação Setorial SEA":
        from paginas.result_setorial_sea import show_results
        show_results()
    elif section == "Análise Energética - Torrefação":
        from paginas.result_energetica import show_results
        show_results()
    elif section == "Administração":
        from paginas.crude import show_crud
        show_crud()

if __name__ == "__main__":
    main()
