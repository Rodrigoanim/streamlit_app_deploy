"""
Centralização de estilos e tema da aplicação Streamlit.

Fornece paleta de cores, tamanhos de fonte e funções utilitárias para
injetar CSS global, do sidebar, da tela de login e de elementos específicos.
"""

from __future__ import annotations

# Paleta de cores (padrão ABIC)
COLORS = {
    "primary": "#007a7d",
    "secondary": "#53a7a9",
    "sidebar_bg": "#8eb0ae",
    "sidebar_link": "#53a7a9",
    "text_light": "#FFFFFF",
    "grid": "#E0E0E0",
    "axis_line": "#B0B0B0",
}

# Tamanhos de fonte padrão
FONTS = {
    "base": 16,
    "sidebar_title": 24,
    "title": 32,
}


def global_css() -> str:
    """CSS global: remove botão de fullscreen do Plotly/imagens."""
    return """
    <style>
        button[aria-label="Fullscreen"] { display: none !important; }
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
    """CSS do sidebar com base na paleta e tamanhos fornecidos."""
    return f"""
    <style>
        [data-testid="stSidebar"] {{
            padding-top: 0rem;
            background-color: {bg};
        }}
        [data-testid="stSidebar"] h1 {{
            color: {text};
            font-size: {title_size}px;
            padding: 10px;
        }}
        [data-testid="stSidebar"] p {{
            color: {text};
            font-size: 16px;
            padding: 5px;
        }}
        [data-testid="stSidebar"] a {{
            color: {link};
            text-decoration: none;
        }}
        [data-testid="stSidebar"] button {{
            background-color: {button_bg};
            color: {text};
            border-radius: 5px;
            padding: 8px 15px;
        }}
        [data-testid="stSidebarNav"] {{
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #ffffff;
            border-radius: 5px;
            padding: 10px;
            margin: 5px;
        }}
        .css-1v0mbdj.e115fcil1 {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem;
        }}
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
    """CSS para tela de login (container e header)."""
    return f"""
    <style>
        [data-testid="stAppViewContainer"] {{ background-color: {bg}; }}
        [data-testid="stHeader"] {{ background-color: {bg}; }}
        [data-testid="stAppViewContainer"] p {{ color: {text}; }}
        [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; }}
    </style>
    """


def terms_css(*, text: str = COLORS["text_light"]) -> str:
    """CSS para links e checkbox dos termos na sidebar."""
    return f"""
    <style>
        a {{ color: {text} !important; text-decoration: underline !important; }}
        .stCheckbox {{ color: {text} !important; }}
        .stCheckbox label {{ color: {text} !important; }}
        .stCheckbox a {{ color: {text} !important; text-decoration: underline !important; }}
    </style>
    """


__all__ = [
    "COLORS",
    "FONTS",
    "global_css",
    "sidebar_css",
    "login_css",
    "terms_css",
]


