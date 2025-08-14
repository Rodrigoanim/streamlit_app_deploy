"""
Módulo de Centralização de Estilos e Tema da Aplicação Streamlit FPC.

Este módulo centraliza todas as configurações estéticas da aplicação, incluindo:
- Paleta de cores corporativa da ABIC
- Tamanhos de fonte padronizados
- Funções para injeção de CSS customizado
- Configurações específicas para diferentes componentes da interface

PRINCÍPIOS DE DESIGN:
- Consistência visual em toda a aplicação
- Acessibilidade (contraste adequado)
- Responsividade para diferentes tamanhos de tela
- Manutenibilidade através de centralização

ESTRUTURA:
- COLORS: Dicionário com todas as cores utilizadas
- FONTS: Dicionário com tamanhos de fonte padronizados
- Funções CSS: Cada função gera CSS específico para um componente

USO:
    from ui.theme import COLORS, FONTS, sidebar_css, login_css
    
    # Aplicar CSS do sidebar
    st.markdown(sidebar_css(), unsafe_allow_html=True)
    
    # Usar cores em componentes
    st.markdown(f'<p style="color: {COLORS["primary"]}">Texto</p>', 
                unsafe_allow_html=True)

AUTOR: Sistema FPC - ABIC
VERSÃO: 1.0
ÚLTIMA ATUALIZAÇÃO: Janeiro 2025
"""

from __future__ import annotations

# =============================================================================
# PALETA DE CORES CORPORATIVA ABIC
# =============================================================================
# Todas as cores utilizadas na aplicação estão centralizadas aqui.
# Para alterar a identidade visual, modifique apenas este dicionário.
# 
# CONVENÇÕES:
# - primary: Cor principal da marca (verde ABIC)
# - secondary: Cor secundária/complementar
# - sidebar_*: Cores específicas do painel lateral
# - text_*: Cores de texto (light para fundos escuros, dark para fundos claros)
# - grid/axis: Cores para elementos de gráficos
#
# VALORES HEXADECIMAIS:
# - #007a7d: Verde principal ABIC (RGB: 0, 122, 125)
# - #53a7a9: Verde secundário (RGB: 83, 167, 169)
# - #8eb0ae: Verde claro para sidebar (RGB: 142, 176, 174)
COLORS = {
    "primary": "#007a7d",      # Verde principal ABIC - usado em headers, botões principais
    "secondary": "#53a7a9",    # Verde secundário - usado em botões secundários, destaques
    "sidebar_bg": "#8eb0ae",   # Fundo do sidebar - verde claro para contraste
    "sidebar_link": "#53a7a9", # Links no sidebar - verde secundário
    "text_light": "#FFFFFF",   # Texto claro - usado em fundos escuros (sidebar, login)
    "grid": "#E0E0E0",         # Linhas de grade dos gráficos - cinza claro
    "axis_line": "#B0B0B0",    # Linhas dos eixos dos gráficos - cinza médio
}

# =============================================================================
# TAMANHOS DE FONTE PADRONIZADOS
# =============================================================================
# Centraliza todos os tamanhos de fonte utilizados na aplicação.
# Valores em pixels para facilitar manutenção e consistência visual.
#
# HIERARQUIA DE FONTES:
# - base: Tamanho padrão para texto normal (16px)
# - sidebar_title: Título do sidebar (24px)
# - title: Títulos principais das páginas (32px)
#
# OBSERVAÇÕES:
# - 16px é o tamanho padrão recomendado para acessibilidade web
# - Títulos seguem proporção áurea (1.5x) para hierarquia visual
FONTS = {
    "base": 16,           # Texto base da aplicação
    "sidebar_title": 24,  # Título do sidebar
    "title": 32,          # Títulos principais das páginas
}

# =============================================================================
# FUNÇÕES DE INJEÇÃO DE CSS
# =============================================================================

def global_css() -> str:
    """
    Gera CSS global aplicado a toda a aplicação.
    
    FUNCIONALIDADES:
    - Remove botão de fullscreen do Plotly e imagens
    - Aplicado automaticamente em todas as páginas
    
    RETORNO:
        str: CSS global em formato string
        
    USO:
        st.markdown(global_css(), unsafe_allow_html=True)
        
    OBSERVAÇÕES:
    - CSS específico para elementos do Plotly
    - Usa !important para garantir que a regra seja aplicada
    """
    return """
    <style>
        /* Remove botão de fullscreen do Plotly e imagens */
        button[aria-label="Fullscreen"] { 
            display: none !important; 
        }
    </style>
    """


def sidebar_css(
    *,
    bg: str = COLORS["sidebar_bg"],
    link: str = COLORS["sidebar_link"],
    text: str = COLORS["text_light"],
    button_bg: str = COLORS["secondary"],
    title_size: int = FONTS["sidebar_title"],
) -> str:
    """
    Gera CSS customizado para o sidebar da aplicação.
    
    PARÂMETROS:
        bg (str): Cor de fundo do sidebar (padrão: verde claro ABIC)
        link (str): Cor dos links no sidebar (padrão: verde secundário)
        text (str): Cor do texto no sidebar (padrão: branco)
        button_bg (str): Cor de fundo dos botões (padrão: verde secundário)
        title_size (int): Tamanho do título em pixels (padrão: 24px)
    
    ELEMENTOS ESTILIZADOS:
    - Container principal do sidebar
    - Títulos (h1) com cor e tamanho customizados
    - Parágrafos (p) com padding e cor
    - Links (a) sem sublinhado
    - Botões com bordas arredondadas
    - Navegação centralizada
    
    RETORNO:
        str: CSS completo do sidebar
        
    USO:
        st.markdown(sidebar_css(), unsafe_allow_html=True)
        
    PERSONALIZAÇÃO:
        # Usar cores diferentes
        st.markdown(sidebar_css(bg="#custom_color"), unsafe_allow_html=True)
        
        # Usar tamanho de título diferente
        st.markdown(sidebar_css(title_size=28), unsafe_allow_html=True)
    """
    return f"""
    <style>
        /* Container principal do sidebar */
        [data-testid="stSidebar"] {{
            padding-top: 0rem;
            background-color: {bg};
        }}
        
        /* Título do sidebar */
        [data-testid="stSidebar"] h1 {{
            color: {text};
            font-size: {title_size}px;
            padding: 10px;
        }}
        
        /* Texto do sidebar */
        [data-testid="stSidebar"] p {{
            color: {text};
            font-size: 16px;
            padding: 5px;
        }}
        
        /* Links do sidebar */
        [data-testid="stSidebar"] a {{
            color: {link};
            text-decoration: none;
        }}
        
        /* Botões do sidebar */
        [data-testid="stSidebar"] button {{
            background-color: {button_bg};
            color: {text};
            border-radius: 5px;
            padding: 8px 15px;
        }}
        
        /* Navegação do sidebar - centralizada */
        [data-testid="stSidebarNav"] {{
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #ffffff;
            border-radius: 5px;
            padding: 10px;
            margin: 5px;
        }}
        
        /* Container de elementos do sidebar - centralizado */
        .css-1v0mbdj.e115fcil1 {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem;
        }}
        
        /* Remove botão fullscreen do sidebar */
        [data-testid="stSidebar"] button[aria-label="Fullscreen"] {{
            display: none !important;
        }}
    </style>
    """


def login_css(
    *,
    bg: str = COLORS["primary"],
    sidebar_bg: str = COLORS["sidebar_bg"],
    text: str = COLORS["text_light"],
) -> str:
    """
    Gera CSS específico para a tela de login.
    
    PARÂMETROS:
        bg (str): Cor de fundo da aplicação (padrão: verde principal ABIC)
        sidebar_bg (str): Cor de fundo do sidebar (padrão: verde claro)
        text (str): Cor do texto (padrão: branco)
    
    ELEMENTOS ESTILIZADOS:
    - Container principal da aplicação
    - Header da aplicação
    - Parágrafos no container principal
    - Sidebar (força cor com !important)
    
    RETORNO:
        str: CSS para tela de login
        
    USO:
        st.markdown(login_css(), unsafe_allow_html=True)
        
    OBSERVAÇÕES:
    - Usa !important para sidebar para garantir que a cor seja aplicada
    - Aplicado apenas na tela de login para criar ambiente visual diferenciado
    """
    return f"""
    <style>
        /* Container principal da aplicação */
        [data-testid="stAppViewContainer"] {{ 
            background-color: {bg}; 
        }}
        
        /* Header da aplicação */
        [data-testid="stHeader"] {{ 
            background-color: {bg}; 
        }}
        
        /* Texto no container principal */
        [data-testid="stAppViewContainer"] p {{ 
            color: {text}; 
        }}
        
        /* Sidebar - força cor com !important */
        [data-testid="stSidebar"] {{ 
            background-color: {sidebar_bg} !important; 
        }}
    </style>
    """


def terms_css(*, text: str = COLORS["text_light"]) -> str:
    """
    Gera CSS para links e checkbox dos termos de uso na sidebar.
    
    PARÂMETROS:
        text (str): Cor do texto (padrão: branco)
    
    ELEMENTOS ESTILIZADOS:
    - Links gerais (a)
    - Checkbox do Streamlit (.stCheckbox)
    - Labels dos checkboxes
    - Links dentro dos checkboxes
    
    RETORNO:
        str: CSS para elementos dos termos
        
    USO:
        st.markdown(terms_css(), unsafe_allow_html=True)
        
    OBSERVAÇÕES:
    - Usa !important para garantir que as cores sejam aplicadas
    - Específico para a seção de termos de uso no sidebar
    - Mantém sublinhado nos links para acessibilidade
    """
    return f"""
    <style>
        /* Links gerais */
        a {{ 
            color: {text} !important; 
            text-decoration: underline !important; 
        }}
        
        /* Checkbox do Streamlit */
        .stCheckbox {{ 
            color: {text} !important; 
        }}
        
        /* Labels dos checkboxes */
        .stCheckbox label {{ 
            color: {text} !important; 
        }}
        
        /* Links dentro dos checkboxes */
        .stCheckbox a {{ 
            color: {text} !important; 
            text-decoration: underline !important; 
        }}
    </style>
    """


# =============================================================================
# EXPORTAÇÃO PÚBLICA
# =============================================================================
# Define quais elementos são exportados quando o módulo é importado
# com "from ui.theme import *"
__all__ = [
    "COLORS",      # Dicionário de cores
    "FONTS",       # Dicionário de tamanhos de fonte
    "global_css",  # CSS global da aplicação
    "sidebar_css", # CSS do sidebar
    "login_css",   # CSS da tela de login
    "terms_css",   # CSS dos termos de uso
]


