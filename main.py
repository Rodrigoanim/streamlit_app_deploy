# Arquivo: main.py
# Data: 12/02/2025 - 20:43
# IDE Cursor - claude 3.5 sonnet
# comando: streamlit run main.py

import streamlit as st
import sqlite3
from paginas.form_model import process_forms_tab

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
                SELECT ID_User, perfil, nome_usuario FROM Usuarios WHERE email = ? AND senha = ?
            """, (email, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                st.session_state["logged_in"] = True
                st.session_state["user_profile"] = user[1]
                st.session_state["user_id"] = user[0]
                st.session_state["user_name"] = user[2]
                st.success(f"Login bem-sucedido! Bem-vindo, {user[2]}.")
            else:
                st.error("E-mail ou senha inválidos.")

    return st.session_state.get("logged_in", False), st.session_state.get("user_profile", None)

def main():
    """Gerencia a navegação entre as páginas do sistema."""
    logged_in, user_profile = authenticate_user()

    if not logged_in:
        st.stop()

    st.title("Simulador da Pegada de Carbono do Café Torrado - 2025")

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
    
    menu_options = ["Tipo do Café", "Moagem e Torrefação", "Embalagem", "Resultados"]
    
    # Modificando a verificação para ser case-insensitive
    if user_profile and user_profile.lower() == "adm":
        menu_options.append("Administração")
    
    section = st.sidebar.radio(
        "Selecione o Formulário:",
        menu_options,
        key="menu_selection"
    )
    
    # Mapeamento das opções do menu para os valores da coluna section
    section_map = {
        "Tipo do Café": "cafe",
        "Moagem e Torrefação": "moagem",
        "Embalagem": "embalagem",
        "Resultados": "resultados",
        "Administração": "crud"
    }
    
    # Processa a seção selecionada
    if section in ["Tipo do Café", "Moagem e Torrefação", "Embalagem"]:
        process_forms_tab(section_map[section])
    elif section == "Resultados":
        from paginas.resultados import show_results
        show_results()
    elif section == "Administração":
        from paginas.crude import show_crud
        show_crud()

if __name__ == "__main__":
    main()
