# main.py
# Data: 03/04/2025 - Hora: 08:00
# IDE Cursor - claude 3.5 sonnet
# comando: streamlit run main.py
# ajustes TSW / Anna - redução de conteudo e ajustes de layout
# logotipos no sidebar e rodapé

import streamlit as st
import sqlite3
from paginas.form_model import process_forms_tab
from datetime import datetime, timedelta
import time
import sys
from config import DB_PATH, DATA_DIR  # Atualize a importação
import os
from paginas.monitor import registrar_acesso  # Adicione esta importação no topo do arquivo
import streamlit.components.v1 as components

# Adicione esta linha logo no início do arquivo, após os imports
# os.environ['RENDER'] = 'true'

# Configuração da página - deve ser a primeira chamada do Streamlit
st.set_page_config(
    page_title="Simulador da Pegada de Carbono do Café",  # Título simplificado
    page_icon="☕",
    layout="wide",
    menu_items={
        'About': """
        ### Sobre o Sistema - Simulador da Pegada de Carbono do Café Torrado/Moído
        
        Versão: 1.1. Beta
        
        Este sistema foi desenvolvido para simular a pegada de carbono 
        do processo de produção do café torrado/moído.
        
        © 2025 Todos os direitos reservados. ABIC - Associação Brasileira de Indústrias de Café.
        """,
        'Get Help': None,
        'Report a bug': None
    },
    initial_sidebar_state="expanded"
)

# Adicionar verificação e carregamento do logo
import os

# Obtém o caminho absoluto do diretório atual
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "ABIC_007a7d.jpg")

# Adicionar o logotipo no sidebar usando st.sidebar.image
st.sidebar.markdown("""
    <style>
        /* Estilo geral do sidebar */
        [data-testid="stSidebar"] {
            padding-top: 0rem;
            background-color: #007a7d; # cor original #f0f0f0
        }
        
        /* Estilo para títulos no sidebar */
        [data-testid="stSidebar"] h1 {
            color: #FFFFFF; # cor da fonte branca
            font-size: 24px;
            # font-weight: bold;
            padding: 10px;
        }
        
        /* Estilo para texto normal no sidebar */
        [data-testid="stSidebar"] p {
            color: #FFFFFF; 
            font-size: 16px;
            padding: 5px;
        }
        
        /* Estilo para links no sidebar */
        [data-testid="stSidebar"] a {
            color: #007a7d;
            text-decoration: none;
        }
        
        /* Estilo para botões no sidebar */
        [data-testid="stSidebar"] button {
            background-color: #007a7d;
            color: white;
            border-radius: 5px;
            padding: 8px 15px;
        }
        
        /* Estilo para o menu de navegação */
        [data-testid="stSidebarNav"] {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #ffffff;
            border-radius: 5px;
            padding: 10px;
            margin: 5px;
        }
        
        /* Estilo para o container da imagem */
        .css-1v0mbdj.e115fcil1 {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem;
        }
        
        /* Remove o ícone de fullscreen */
        button[title="View fullscreen"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Verifica se o arquivo existe antes de tentar carregá-lo
if os.path.exists(logo_path):
    col1, col2, col3 = st.sidebar.columns([1,2,1])
    with col2:
        st.image(
            logo_path,
            width=150,  # ajuste este valor conforme necessário
            use_container_width=True
        )
else:
    st.sidebar.warning(f"Logo não encontrado em: {logo_path}")

# Atualizar metadados Open Graph com informações mais específicas
components.html(
    """
    <head>
        <title>Simulador da Pegada de Carbono do Café Torrado/Moído</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description" content="Simulador da ABIC para cálculo da pegada de carbono do café torrado/moído">
        
        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://apc.ag93app.com.br/?v=1.0">
        <meta property="og:title" content="Simulador da Pegada de Carbono do Café Torrado/Moído">
        <meta property="og:description" content="Ferramenta da ABIC para simulação da pegada de carbono do café torrado/moído">
        <meta property="og:image" content="https://ag93eventos.com.br/anim/pegada2.jpg?v=1.0">
        <meta property="og:site_name" content="Simulador Pegada de Carbono">    
           
        <!-- Adicional SEO -->
        <meta name="author" content="ABIC">
        <meta name="keywords" content="café, pegada de carbono, sustentabilidade, ABIC, café torrado, café moído">
        <link rel="canonical" href="https://apc.ag93app.com.br/">
    </head>
    """,
    height=0,
    width=0
)

def authenticate_user():
    """Autentica o usuário e verifica seu perfil no banco de dados."""
    # Verifica se o banco existe
    if not DB_PATH.exists():
        st.error(f"Banco de dados não encontrado em {DB_PATH}")
        return False, None
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if "user_profile" not in st.session_state:
        st.session_state["user_profile"] = None

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    if not st.session_state["logged_in"]:
        # Criar uma coluna centralizada
        col1, col2, col3 = st.columns([1, 20, 1])
        
        with col2:
            # Imagem de capa usando SPCC.jpg da raiz
            st.image("SPCC.jpg", use_container_width=True)
            
        st.markdown("""
            <p style='text-align: center; font-size: 35px;'>Faça login para acessar o sistema</p>
        """, unsafe_allow_html=True)
        
        # Login na sidebar
        st.sidebar.markdown("<h1 style='color: white; font-size: 24px;'>SPCC - versão 2.2</h1>", unsafe_allow_html=True)

        # Criar labels personalizados com cor branca
        st.sidebar.markdown("<p style='color: white; margin-bottom: 5px;'>E-mail</p>", unsafe_allow_html=True)
        email = st.sidebar.text_input("Email input", key="email", label_visibility="collapsed")

        st.sidebar.markdown("<p style='color: white; margin-bottom: 5px;'>Senha</p>", unsafe_allow_html=True)
        password = st.sidebar.text_input("Password input", type="password", key="password", 
                                        label_visibility="collapsed",
                                        on_change=lambda: st.session_state.update({"enter_pressed": True}) 
                                        if "password" in st.session_state else None)

        col1, col2 = st.sidebar.columns(2)
        with col1:
            login_button = st.button("Entrar")
        
        if login_button:
            cursor.execute("""
                SELECT id, user_id, perfil, nome FROM usuarios WHERE email = ? AND senha = ?
            """, (email, password))
            user = cursor.fetchone()

            if user:
                st.session_state["logged_in"] = True
                st.session_state["user_profile"] = user[2]
                st.session_state["user_id"] = user[1]
                st.session_state["user_name"] = user[3]
                
                # Registrar o acesso bem-sucedido
                registrar_acesso(
                    user_id=user[1],
                    programa="main.py",
                    acao="login"
                )
                
                st.sidebar.success(f"Login bem-sucedido! Bem-vindo, {user[3]}.")
                st.rerun()
            else:
                st.sidebar.error("E-mail ou senha inválidos.")

    return st.session_state.get("logged_in", False), st.session_state.get("user_profile", None)

def get_timezone_offset():
    """
    Determina se é necessário aplicar offset de timezone baseado no ambiente
    """
    is_production = os.getenv('RENDER') is not None
    
    if is_production:
        # Se estiver no Render, ajusta 3 horas para trás
        return datetime.now() - timedelta(hours=3)
    return datetime.now()  # Se local, usa hora atual

def show_welcome():
    """Exibe a tela de boas-vindas com informações do usuário"""
    st.markdown("""
        <p style='text-align: left; font-size: 40px; font-weight: bold;'>Bem-vindo ao sistema!</p>
    """, unsafe_allow_html=True)
    
    # Buscar dados do usuário
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, empresa 
        FROM usuarios 
        WHERE user_id = ?
    """, (st.session_state.get('user_id'),))
    user_info = cursor.fetchone()
    
    # Removemos a consulta de contagem de formulários
    conn.close()
    
    empresa = user_info[1] if user_info[1] is not None else "Não informada"
    
    # Layout em colunas usando st.columns
    col1, col2, col3 = st.columns(3)
    
    # Coluna 1: Dados do Usuário
    with col1:
        st.markdown(f"""
            <div style="background-color: #e8f4f8; padding: 20px; border-radius: 8px;">
                <p style="color: #2c3e50; font-size: 24px;">Seus Dados</p>
                <div style="color: #34495e; font-size: 16px;">
                    <p>ID: {st.session_state.get('user_id')}</p>
                    <p>Nome: {st.session_state.get('user_name')}</p>
                    <p>E-mail: {user_info[0]}</p>
                    <p>Empresa: {empresa}</p>
                    <p>Perfil: {st.session_state.get('user_profile')}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 2: Atividades (atualizada com hora)
    with col2:
        current_time = get_timezone_offset()
        ambiente = "Produção" if os.getenv('RENDER') else "Local"
        
        st.markdown(f"""
            <div style="background-color: #e8f8ef; padding: 20px; border-radius: 8px;">
                <p style="color: #2c3e50; font-size: 24px;">Suas Atividades</p>
                <div style="color: #34495e; font-size: 16px;">
                    <p>Data Atual: {current_time.strftime('%d/%m/%Y')}</p>
                    <p>Hora Atual: {current_time.strftime('%H:%M:%S')}</p>
                    <p>Ambiente: {ambiente}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 3: Módulos
    with col3:
        modulos_html = """
            <div style="background-color: #fff8e8; padding: 20px; border-radius: 8px;">
                <p style="color: #2c3e50; font-size: 24px;">Módulos Disponíveis</p>
                <div style="color: #34495e; font-size: 16px;">
                    <p>Entrada de Dados - Tipo do Café</p>
                    <p>Entrada de Dados - Torrefação e Moagem</p>
                    <p>Entrada de Dados - Embalagem</p>
                    <p>Simulações da Empresa</p>
                    <p>Simulações da Empresa Sem Etapa Agrícola</p>
                    <p>Simulações - Comparação Setorial</p>
                    <p>Simulações - Comparação Setorial Sem Etapa Agrícola</p>
                    <p>Simulações - Análise Energética - Torrefação</p>
                </div>
            </div>
        """
        
        st.markdown(modulos_html, unsafe_allow_html=True)

def zerar_value_element():
    """Função para zerar todos os value_element do usuário logado na tabela forms_tab onde type_element é input, formula ou formulaH"""
    # Inicializa o estado do checkbox se não existir
    if 'confirma_zeragem' not in st.session_state:
        st.session_state.confirma_zeragem = False
    
    # Checkbox para confirmação
    confirma = st.sidebar.checkbox("Confirmar zeragem dos valores?", 
                                 value=st.session_state.confirma_zeragem,
                                 key='confirma_zeragem')
    
    if st.sidebar.button("Zerar Valores"):
        if confirma:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Atualiza value_element para 0.0 para os tipos especificados
                cursor.execute("""
                    UPDATE forms_tab 
                    SET value_element = 0.0 
                    WHERE user_id = ? 
                    AND value_element IS NOT NULL
                    AND type_element IN ('input', 'formula', 'formulaH')
                """, (st.session_state["user_id"],))
                
                registros_afetados = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                # Registra a ação no monitor
                registrar_acesso(
                    user_id=st.session_state["user_id"],
                    programa="main.py",
                    acao="zerar_valores"
                )
                
                st.sidebar.success(f"Valores zerados com sucesso! ({registros_afetados} registros atualizados)")
                
                # Força a atualização da página após 1 segundo
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.sidebar.error(f"Erro ao zerar valores: {str(e)}")
                if 'conn' in locals():
                    conn.close()
        else:
            st.sidebar.warning("Confirme a operação para prosseguir")

def main():
    """Gerencia a navegação entre as páginas do sistema."""
    # Verifica se o diretório data existe
    if not DATA_DIR.exists():
        st.error(f"Pasta '{DATA_DIR}' não encontrada. O programa não pode continuar.")
        st.stop()
        
    # Verifica se o banco existe
    if not DB_PATH.exists():
        st.error(f"Banco de dados '{DB_PATH}' não encontrado. O programa não pode continuar.")
        st.stop()
        
    logged_in, user_profile = authenticate_user()
    
    if not logged_in:
        st.stop()
    
    # Armazenar página anterior para comparação
    if "previous_page" not in st.session_state:
        st.session_state["previous_page"] = None
    
    # Titulo da página
    st.markdown("""
        <p style='text-align: left; font-size: 44px; font-weight: bold;'>
            Simulador da Pegada de Carbono do Café Torrado/Moído
        </p>
    """, unsafe_allow_html=True)

    # Adicionar informação do usuário logado
    st.sidebar.markdown(f"""
        **Usuário:** {st.session_state.get('user_name')}  
        **ID:** {st.session_state.get('user_id')}  
        **Perfil:** {st.session_state.get('user_profile')}
    """)

    if st.sidebar.button("Logout"):
        # Registrar o logout antes de limpar a sessão
        if "user_id" in st.session_state:
            registrar_acesso(
                user_id=st.session_state["user_id"],
                programa="main.py",
                acao="logout"
            )
        
        for key in ['logged_in', 'user_profile', 'user_id', 'user_name']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.sidebar.title("Menu de Navegação")
    
    # Atualizar o mapeamento para incluir o novo nome do CRUD
    section_map = {
        "Tipo do Café": "cafe",
        "Torrefação e Moagem": "moagem",
        "Embalagem": "embalagem",
        "da Empresa": "Resultados",
        "Info Tabelas (CRUD)": "crud"
    }
    
    # Criando grupos de menu
    menu_groups = {
        "Principal": ["Bem-vindo"],
        "Entrada de Dados": [
            "Tipo do Café",
            "Torrefação e Moagem",
            "Embalagem"
        ],
        "Simulações": [
            "da Empresa",
            "da Empresa sem Etapa Agrícola",
            "Comparação Setorial",
            "Comparação Setorial SEA",
            "Análise Energética - Torrefação"
        ],
        "Administração": []  # Iniciando vazio para adicionar itens na ordem correta
    }
    
    # Adicionar opções administrativas na ordem desejada
    if user_profile and user_profile.lower() == "master":
        menu_groups["Administração"].append("Info Tabelas (CRUD)")
    if user_profile and user_profile.lower() == "master":
        menu_groups["Administração"].append("Diagnóstico")
    if user_profile and user_profile.lower() in ["adm", "master"]:
        menu_groups["Administração"].append("Monitor de Uso")
    # Adicionar Zerar Valores por último
    menu_groups["Administração"].append("Zerar Valores")
    
    # Se não houver opções de administração, remover o grupo
    if not menu_groups["Administração"]:
        menu_groups.pop("Administração")
    
    # Criar seletor de grupo
    selected_group = st.sidebar.selectbox(
        "Selecione o módulo:",
        options=list(menu_groups.keys()),
        key="group_selection"
    )
    
    # Criar seletor de página dentro do grupo
    section = st.sidebar.radio(
        "Selecione a página:",
        menu_groups[selected_group],
        key="menu_selection"
    )

    # Verificar se houve mudança de página
    if st.session_state.get("previous_page") != section:
        save_current_form_data()
        st.session_state["previous_page"] = section

    # Processa a seção selecionada
    if section == "Bem-vindo":
        show_welcome()
    elif section in ["Tipo do Café", "Torrefação e Moagem", "Embalagem"]:
        process_forms_tab(section_map[section])
    elif section in [
        "da Empresa",
        "da Empresa sem Etapa Agrícola",
        "Comparação Setorial",
        "Comparação Setorial SEA"
    ]:
        # Mapeamento de seções para títulos completos
        section_to_title = {
            "da Empresa": "Simulações da Empresa",
            "da Empresa sem Etapa Agrícola": "Simulações da Empresa Sem Etapa Agrícola",
            "Comparação Setorial": "Simulações - Comparação Setorial",
            "Comparação Setorial SEA": "Simulações - Comparação Setorial Sem Etapa Agrícola"
        }
        # Passa o título completo para show_page
        show_page(selected_simulation=section_to_title[section])
    elif section == "Análise Energética - Torrefação":
        from paginas.result_energetica import show_results as show_energetica
        show_energetica()
    elif section == "Info Tabelas (CRUD)":
        from paginas.crude import show_crud
        show_crud()
    elif section == "Monitor de Uso":
        from paginas.monitor import main as show_monitor
        show_monitor()
    elif section == "Diagnóstico":
        from paginas.diagnostico import show_diagnostics
        show_diagnostics()
    elif section == "Zerar Valores":
        zerar_value_element()

    # Após todo o código do menu, adicionar espaço e a imagem do rodapé
    st.sidebar.markdown("<br>" * 2, unsafe_allow_html=True)
    
    # Logo do rodapé
    footer_logo_path = os.path.join(current_dir, "pegada_cafe.jpg")
    if os.path.exists(footer_logo_path):
        col1, col2, col3 = st.sidebar.columns([1,2,1])
        with col2:
            st.image(
                footer_logo_path,
                width=150,
                use_container_width=True
            )

def show_page(selected_simulation=None):
    """
    Gerencia a exibição das páginas de simulação
    Args:
        selected_simulation: Título da simulação selecionada
    """
    # Mapeamento de páginas para tabelas e títulos
    PAGES_CONFIG = {
        "Simulações da Empresa": {
            "tabela": "forms_resultados",
            "titulo": "Simulações da Empresa"
        },
        "Simulações da Empresa Sem Etapa Agrícola": {
            "tabela": "forms_result_sea",
            "titulo": "Simulações da Empresa Sem Etapa Agrícola"
        },
        "Simulações - Comparação Setorial": {
            "tabela": "forms_setorial",
            "titulo": "Simulações - Comparação Setorial"
        },
        "Simulações - Comparação Setorial Sem Etapa Agrícola": {
            "tabela": "forms_setorial_sea",
            "titulo": "Simulações - Comparação Setorial Sem Etapa Agrícola"
        }
    }

    # Verifica se usuário está logado
    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login para continuar.")
        return

    # Usa a simulação passada ou permite seleção via selectbox
    if selected_simulation and selected_simulation in PAGES_CONFIG:
        page_config = PAGES_CONFIG[selected_simulation]
    else:
        st.error("Simulação não encontrada")
        return
    
    # Chama a função show_results com os parâmetros apropriados
    from paginas.resultados import show_results
    show_results(
        tabela_escolhida=page_config["tabela"],
        titulo_pagina=page_config["titulo"],
        user_id=st.session_state.user_id
    )

def save_current_form_data():
    """Salva os dados do formulário atual quando houver mudança de página"""
    if "form_data" in st.session_state:
        with st.spinner('Salvando dados...'):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Queries SQL sem comentários para evitar erros de parsing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_cafe (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    data_input TIMESTAMP,
                    tipo_cafe TEXT,
                    quantidade FLOAT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_moagem (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    data_input TIMESTAMP,
                    tipo_moagem TEXT,
                    temperatura FLOAT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS form_embalagem (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    data_input TIMESTAMP,
                    tipo_embalagem TEXT,
                    peso FLOAT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
                )
            """)
            
            previous_page = st.session_state.get("previous_page", "")
            
            if "Tipo do Café" in previous_page:
                tipo_cafe = st.session_state.get("form_data", {}).get("tipo_cafe")
                quantidade = st.session_state.get("form_data", {}).get("quantidade")
                
                if tipo_cafe and quantidade is not None:  # Verifica se os dados existem
                    cursor.execute("""
                        INSERT OR REPLACE INTO form_cafe 
                        (user_id, data_input, tipo_cafe, quantidade)
                        VALUES (?, datetime('now'), ?, ?)
                    """, (
                        st.session_state["user_id"],
                        tipo_cafe,
                        quantidade
                    ))
            
            elif "Torrefação e Moagem" in previous_page:
                cursor.execute("""
                    INSERT OR REPLACE INTO form_moagem 
                    (user_id, data_input, tipo_moagem, temperatura)
                    VALUES (?, datetime('now'), ?, ?)
                """, (
                    st.session_state["user_id"],
                    st.session_state.get("form_data", {}).get("tipo_moagem"),
                    st.session_state.get("form_data", {}).get("temperatura")
                ))
            
            elif "Embalagem" in previous_page:
                cursor.execute("""
                    INSERT OR REPLACE INTO form_embalagem 
                    (user_id, data_input, tipo_embalagem, peso)
                    VALUES (?, datetime('now'), ?, ?)
                """, (
                    st.session_state["user_id"],
                    st.session_state.get("form_data", {}).get("tipo_embalagem"),
                    st.session_state.get("form_data", {}).get("peso")
                ))
            
            conn.commit()
            conn.close()
            # Limpar os dados do formulário após salvar
            st.session_state["form_data"] = {}
            time.sleep(0.5)  # Pequeno delay para feedback visual
        st.success('Dados salvos com sucesso!')

def login():
    """Função de login do usuário"""
    # Mova estas variáveis para dentro da função
    email = st.text_input("E-mail", key="email")
    senha = st.text_input("Senha", type="password", key="password")
    
    if st.form_submit_button("Login"):
        try:
            # Use a conexão do DB_PATH em vez de criar_conexao
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
            usuario = cursor.fetchone()
            
            if usuario:
                st.session_state.autenticado = True
                st.session_state.user_id = usuario[0]
                st.session_state.nome = usuario[1]
                st.session_state.email = usuario[2]
                st.session_state.admin = usuario[4]
                
                # Registra o acesso bem-sucedido
                registrar_acesso(
                    user_id=usuario[0],
                    programa="main.py",
                    acao="login"
                )
                
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Email ou senha incorretos")
                
            conn.close()
            
        except Exception as e:
            st.error(f"Erro ao realizar login: {str(e)}")
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    main()
