# Arquivo: main.py
# Data: 06/02/2025
# IDE Cursor - claude 3.5 sonnet
# comando: streamlit run main.py

import streamlit as st
import sqlite3

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

    st.sidebar.title("Navegação")

    # Menu options - only showing active options
    page = st.sidebar.radio("Menu", [
        "Início", 
        "Tipo de Café",
        "Resultados",    # Nova opção adicionada
        # "Adm_User",        # Temporarily disabled
        # "Relatórios",      # Temporarily disabled
        # "Adm_Forms"        # Temporarily disabled
    ])

    if page == "Início":
        st.write("Selecione uma opção no menu à esquerda.")

    elif page == "Tipo de Café":
        if "user_id" not in st.session_state:
            st.error("Erro: ID do usuário não encontrado na sessão.")
            st.stop()
        from paginas import form_model
        form_model.process_forms_tab()

    elif page == "Resultados":    # Nova seção adicionada
        if "user_id" not in st.session_state:
            st.error("Erro: ID do usuário não encontrado na sessão.")
            st.stop()
        from paginas import resultados
        resultados.process_resultados_tab()

    # # Temporarily disabled - Adm_User section
    # elif page == "Adm_User":
    #     if user_profile == "Adm":
    #         from paginas import administracao
    #         administracao.app()
    #     else:
    #         st.error("Você não tem permissão para acessar esta página.")

    # # Temporarily disabled - Relatórios section
    # elif page == "Relatórios":
    #     if "user_id" not in st.session_state:
    #         st.error("Erro: ID do usuário não encontrado na sessão.")
    #         st.stop()
    #     from paginas import reports
    #     reports.app()
        
    # # Temporarily disabled - Adm_Forms section
    # elif page == "Adm_Forms":
    #     if user_profile == "Adm":
    #         if "user_id" not in st.session_state:
    #             st.error("Erro: ID do usuário não encontrado na sessão.")
    #             st.stop()
    #         from paginas import _crud_forms_tab
    #         _crud_forms_tab.app()
    #     else:
    #         st.error("Você não tem permissão para acessar esta página.")

if __name__ == "__main__":
    main()
