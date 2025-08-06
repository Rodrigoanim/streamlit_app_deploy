# Data: 30/07/2025 - Hora: 18:00
# IDE Cursor - claude-4 sonnet
#  .\env\Scripts\Activate
# streamlit run main.py
# função para trocar de senha - OK
# ajustes Textos Anna - versão 

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
    page_title="Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído ",  # Título Aba Navegador
    page_icon="☕",
    layout="wide",
    menu_items={
        'About': """
        ### Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído 
        
        Versão: 3.3c - 05/08/2025
        
        Esta Ferramenta foi desenvolvida para cálcular os indicadores ambientais da Produção de Café Torrado e Moído.
        
        
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
logo_path = os.path.join(current_dir, "Logo_ABIC_8eb0ae.jpg")

# --- CSS Global ---
# Adiciona CSS para ocultar o botão de fullscreen das imagens globalmente
st.markdown("""
    <style>
        /* Oculta o botão baseado no aria-label identificado na inspeção */
        button[aria-label="Fullscreen"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)
# --- Fim CSS Global ---

# Adicionar o logotipo no sidebar usando st.sidebar.image
st.sidebar.markdown("""
    <style>
        /* Estilo geral do sidebar */
        [data-testid="stSidebar"] {
            padding-top: 0rem;
            background-color: #8eb0ae; # cor anterior #007a7d
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
            color: #53a7a9;
            text-decoration: none;
        }
        
        /* Estilo para botões no sidebar */
        [data-testid="stSidebar"] button {
            background-color: #53a7a9; # cor anterior #007a7d
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
        
        /* Remove o ícone de fullscreen usando o seletor aria-label (regra específica do sidebar mantida por segurança, embora a global deva cobrir) */
        [data-testid="stSidebar"] button[aria-label="Fullscreen"] {
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



def authenticate_user():
    """Autentica o usuário e verifica seu perfil no banco de dados."""
    # Adicionar CSS para a página de login
    if not st.session_state.get("logged_in", False):
        st.markdown("""
            <style>
                /* Estilo para a página de login */
                [data-testid="stAppViewContainer"] {
                    background-color: #007a7d;
                }
                
                /* Remove a faixa branca superior */
                [data-testid="stHeader"] {
                    background-color: #007a7d;
                }
                
                /* Ajuste da cor do texto para melhor contraste */
                [data-testid="stAppViewContainer"] p {
                    color: white;
                }
                
                /* Mantém o fundo do sidebar na cor original */
                [data-testid="stSidebar"] {
                    background-color: #8eb0ae !important;
                }
            </style>
        """, unsafe_allow_html=True)
    
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
            <p style='text-align: center; font-size: 35px;'></p> 
        """, unsafe_allow_html=True)
        
        # Login na sidebar - versão 3.3c
        st.sidebar.markdown("<h1 style='color: white; font-size: 24px;'>FCIAPC - ver. 3.3c</h1>", unsafe_allow_html=True)

        # Criar labels personalizados com cor branca
        st.sidebar.markdown("<p style='color: white; margin-bottom: 5px;'>E-mail</p>", unsafe_allow_html=True)
        email = st.sidebar.text_input("Email input", key="email", label_visibility="collapsed")

        st.sidebar.markdown("<p style='color: white; margin-bottom: 5px;'>Senha</p>", unsafe_allow_html=True)
        password = st.sidebar.text_input("Password input", type="password", key="password", 
                                        label_visibility="collapsed",
                                        on_change=lambda: st.session_state.update({"enter_pressed": True}) 
                                        if "password" in st.session_state else None)

        # Adiciona o checkbox de aceite dos termos
        st.sidebar.markdown("""
            <style>
                /* Estilo para o link dos termos */
                a {
                    color: white !important;
                    text-decoration: underline !important;
                }
                /* Estilo para o checkbox e seu texto */
                .stCheckbox {
                    color: white !important;
                }
                .stCheckbox label {
                    color: white !important;
                }
                .stCheckbox a {
                    color: white !important;
                    text-decoration: underline !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # link e path do arquivo termos_de_uso.pdf
        aceite_termos = st.sidebar.checkbox(
            'Declaro que li e aceito os termos de uso da [Ferramenta de Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído](https://ag93eventos.com.br/abic/termos_de_uso.pdf)',
            key='aceite_termos'
        )

        col1, col2 = st.sidebar.columns(2)
        with col1:
            login_button = st.button("Entrar", disabled=not aceite_termos)
        
        if login_button and aceite_termos:
            cursor.execute("""
                SELECT id, user_id, perfil, nome FROM usuarios WHERE LOWER(email) = LOWER(?) AND senha = ?
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
                
                st.sidebar.success(f"Login bem-sucedido. {user[3]}.")
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
    """Exibe a tela de boas-vindas"""
    
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
    col1, col2 = st.columns(2)
    
    # Coluna 1: Informações da Ferramenta
    with col1:
        st.markdown(f"""
            <div style="background-color: #007a7d; padding: 20px; border-radius: 8px;">
                <div style="color: #ffffff; font-size: 16px; line-height: 1.6;">
                    <p>Bem vindo(a) à ferramenta desenvolvida para os associados da ABIC para auxiliar ao usuário a prever os principais indicadores ambientais da produção de café torrado e moído.</p>
                    <p>Através desta ferramenta é possível prever como alterações na seleção de fornecedores de café e insumos na industrialização do mesmo afetam os indicadores relativos à Pegada de Carbono, às Demandas de Energia e Água e a Geração de Resíduos sólidos.</p>
                    <p>Os dados industriais refletem a média dos valores coletados durante a realização do projeto "Pegada de Carbono de Café Torrado e Moído no Brasil" no ano de 2023.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Coluna 2: Informações sobre Indicadores
    with col2:
        st.markdown(f"""
            <div style="background-color: #53a7a9; padding: 20px; border-radius: 8px;">
                <div style="color: #ffffff; font-size: 16px; line-height: 1.6;">
                    <p>Esta ferramenta foi criada para cálculo dos indicadores ambientais considerando as etapas agrícola, de transporte até a industrialização, de torrefação e/ou moagem e de acondicionamento em embalagem primária.</p>
                    <p>São calculados os indicadores ambientais de Pegada de Carbono, Demandas de Energia e Água e de Geração de Resíduos sólidos (*).</p>
                    <p>A unidade funcional do projeto são 1000kg de café torrado e moído acondicionados em embalagem primária.</p>
                    <p>(*) Resíduos com atual baixo potencial de aproveitamento dentro das fronteiras do estudo.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    


def zerar_value_element():
    """Função para zerar todos os value_element do usuário logado na tabela forms_tab onde type_element é input ou formula"""
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
                    AND type_element IN ('input', 'formula')
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

def trocar_senha():
    """Função para permitir que o usuário troque sua senha"""
    st.markdown("""
        <p style='text-align: center; font-size: 30px; font-weight: bold;'>
            Trocar Senha
        </p>
    """, unsafe_allow_html=True)
    
    # Criar formulário para troca de senha
    with st.form("form_trocar_senha"):
        st.markdown("**Digite sua senha atual:**")
        senha_atual = st.text_input("Senha atual", type="password", key="senha_atual")
        
        st.markdown("**Digite a nova senha:**")
        nova_senha = st.text_input("Nova senha", type="password", key="nova_senha")
        
        st.markdown("**Confirme a nova senha:**")
        confirmar_senha = st.text_input("Confirmar nova senha", type="password", key="confirmar_senha")
        
        submitted = st.form_submit_button("Trocar Senha")
        
        if submitted:
            # Validações
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("Todos os campos são obrigatórios!")
                return
            
            if nova_senha != confirmar_senha:
                st.error("As senhas não coincidem!")
                return
            
            if len(nova_senha) < 4:
                st.error("A nova senha deve ter pelo menos 4 caracteres!")
                return
            
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Verificar se a senha atual está correta
                cursor.execute("""
                    SELECT id, user_id, nome FROM usuarios 
                    WHERE user_id = ? AND senha = ?
                """, (st.session_state.get('user_id'), senha_atual))
                
                user = cursor.fetchone()
                
                if not user:
                    st.error("Senha atual incorreta!")
                    conn.close()
                    return
                
                # Atualizar a senha
                cursor.execute("""
                    UPDATE usuarios 
                    SET senha = ? 
                    WHERE user_id = ?
                """, (nova_senha, st.session_state.get('user_id')))
                
                conn.commit()
                conn.close()
                
                # Registrar a ação no monitor
                registrar_acesso(
                    user_id=st.session_state["user_id"],
                    programa="main.py",
                    acao="trocar_senha"
                )
                
                st.success("Senha alterada com sucesso!")
                
                # Limpar os campos (removido para evitar erro de Streamlit)
                # st.session_state.senha_atual = ""
                # st.session_state.nova_senha = ""
                # st.session_state.confirmar_senha = ""
                
            except Exception as e:
                st.error(f"Erro ao trocar senha: {str(e)}")
                if 'conn' in locals():
                    conn.close()

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
    
    # Titulo da página Principal
    st.markdown("""
        <p style='text-align: center; font-size: 32px; font-weight: bold;'>
            Ferramenta para Cálculo de Indicadores Ambientais <br> da Produção de Café Torrado e Moído
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
            "Empresa com Etapa Agrícola",
            "Empresa sem Etapa Agrícola",
            "Setorial com Etapa Agrícola",
            "Setorial sem Etapa Agrícola",
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
    # Adicionar Trocar Senha (disponível para todos os perfis)
    menu_groups["Administração"].append("Trocar Senha")
    # Adicionar Zerar Valores por último
    menu_groups["Administração"].append("Zerar Valores")
    
    # Se não houver opções de administração, remover o grupo
    if not menu_groups["Administração"]:
        menu_groups.pop("Administração")
    
    # Criar seletor de grupo
    selected_group = st.sidebar.selectbox(
        "Selecione o Módulo:",
        options=list(menu_groups.keys()),
        key="group_selection"
    )
    
    # Criar seletor de página dentro do grupo
    section = st.sidebar.radio(
        "Selecione a Página:",
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
        "Empresa com Etapa Agrícola",
        "Empresa sem Etapa Agrícola",
        "Setorial com Etapa Agrícola",
        "Setorial sem Etapa Agrícola"
    ]:
        # Importa configurações centralizadas de subtítulos
        from paginas.resultados import get_subtitle_configs
        configs = get_subtitle_configs()
        section_to_title = configs["section_to_title"]
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
    elif section == "Trocar Senha":
        trocar_senha()
    elif section == "Zerar Valores":
        zerar_value_element()

    # Após todo o código do menu, adicionar espaço e a imagem do rodapé
    st.sidebar.markdown("<br>" * 1, unsafe_allow_html=True)
    
    # Logo do rodapé
    footer_logo_path = os.path.join(current_dir, "Logo_Pegada_8eb0ae.jpg")
    if os.path.exists(footer_logo_path):
        col1, col2, col3 = st.sidebar.columns([1,2,1])
        with col2:
            st.image(
                footer_logo_path,
                width=100, 
                use_container_width=False  # Alterado para False para respeitar o width definido
            )

def show_page(selected_simulation=None):
    """
    Gerencia a exibição das páginas de simulação
    Args:
        selected_simulation: Título da simulação selecionada
    """
    # Importa configurações centralizadas de páginas
    from paginas.resultados import get_pages_config
    PAGES_CONFIG = get_pages_config()

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
