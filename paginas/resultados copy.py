# resultados.py
# Data: 12/08/2025 - 11h00
# Pagina de resultados - Dashboard
# rotina das Simulações, tabelas: forms_resultados, forms_result-sea, forms_setorial, forms_setorial_sea
# novo layout para as tabelas e Gráficos - redução de conteudo e ajustes de layout

# type: ignore
# pylance: disable=reportMissingModuleSource

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import time
import traceback
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import DB_PATH

# Configurações centralizadas para subtítulos
def get_subtitle_configs():
    """
    Retorna todas as configurações de subtítulos centralizadas
    """
    return {
        # Mapeamento de tabelas para subtítulos completos (usado no main.py)
        "table_to_full_subtitle": {
            "forms_resultados": "Simulações: Empresa com Etapa Agrícola <br>(Cradle to Gate)",
            "forms_result_sea": "Simulações: Empresa sem Etapa Agrícola <br>(Gate to Gate)",
            "forms_setorial": "Simulações: Setorial com Etapa Agrícola <br>(Cradle to Gate)",
            "forms_setorial_sea": "Simulações: Setorial sem Etapa Agrícola <br>(Gate to Gate)"
        },
        # Mapeamento de seções para títulos completos (usado no main.py)
        "section_to_title": {
            "Empresa com Etapa Agrícola": "Simulações: Empresa com Etapa Agrícola <br>(Cradle to Gate)",
            "Empresa sem Etapa Agrícola": "Simulações: Empresa sem Etapa Agrícola <br>(Gate to Gate)",
            "Setorial com Etapa Agrícola": "Simulações: Setorial com Etapa Agrícola <br>(Cradle to Gate)",
            "Setorial sem Etapa Agrícola": "Simulações: Setorial sem Etapa Agrícola <br>(Gate to Gate)"
        },
        # Mapeamento para nomes de arquivos PDF (usado em resultados.py)
        "table_to_pdf_filename": {
            "forms_resultados": "Simulações - Empresa com Etapa Agrícola",
            "forms_result_sea": "Simulações - Empresa sem Etapa Agrícola",
            "forms_setorial": "Simulações - Setorial com Etapa Agrícola",
            "forms_setorial_sea": "Simulações - Setorial sem Etapa Agrícola"
        }
    }

def get_pages_config():
    """
    Retorna a configuração de páginas para o main.py
    """
    configs = get_subtitle_configs()
    return {
        configs["table_to_full_subtitle"]["forms_resultados"]: {
            "tabela": "forms_resultados",
            "titulo": configs["table_to_full_subtitle"]["forms_resultados"]
        },
        configs["table_to_full_subtitle"]["forms_result_sea"]: {
            "tabela": "forms_result_sea",
            "titulo": configs["table_to_full_subtitle"]["forms_result_sea"]
        },
        configs["table_to_full_subtitle"]["forms_setorial"]: {
            "tabela": "forms_setorial",
            "titulo": configs["table_to_full_subtitle"]["forms_setorial"]
        },
        configs["table_to_full_subtitle"]["forms_setorial_sea"]: {
            "tabela": "forms_setorial_sea",
            "titulo": configs["table_to_full_subtitle"]["forms_setorial_sea"]
        }
    }

from datetime import date
from paginas.monitor import registrar_acesso
from paginas.form_model_recalc import verificar_dados_usuario, calculate_formula, atualizar_formulas


def format_br_number(value):
    """
    Formata um número para o padrão brasileiro
    
    Args:
        value: Número a ser formatado
        
    Returns:
        str: Número formatado como string
        
    Notas:
        - Valores >= 1: sem casas decimais
        - Valores < 1: 3 casas decimais
        - Usa vírgula como separador decimal
        - Usa ponto como separador de milhar
        - Retorna "0" para valores None ou inválidos
    """
    try:
        if value is None:
            return "0"
        
        float_value = float(value)
        if abs(float_value) >= 1:
            return f"{float_value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')  # Duas casas decimais com separador de milhar
        else:
            return f"{float_value:.3f}".replace('.', ',')  # 3 casas decimais
    except:
        return "0"

def titulo(cursor, element):
    """
    Exibe títulos formatados na interface com base nos valores do banco de dados.
    """
    try:
        name = element[0]        # name_element
        type_elem = element[1]   # type_element
        msg = element[3]         # msg_element
        value = element[4]       # value_element (já é REAL do SQLite)
        str_value = element[6]   # str_element
        col = element[7]         # e_col
        row = element[8]         # e_row
        
        # Verifica se a coluna é válida
        if col > 6:
            st.error(f"Posição de coluna inválida para o título {name}: {col}. Deve ser entre 1 e 6.")
            return
        
        # Se for do tipo 'titulo', usa o str_element do próprio registro
        if type_elem == 'titulo':
            if str_value:
                # Se houver um valor numérico para exibir
                if value is not None:
                    # Formata o valor para o padrão brasileiro
                    value_br = format_br_number(value)
                    # Substitui {value} no str_value pelo valor formatado
                    str_value = str_value.replace('{value}', value_br)
                st.markdown(str_value, unsafe_allow_html=True)
            else:
                st.markdown(msg, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Erro ao processar título: {str(e)}")

def pula_linha(cursor, element):
    """
    Adiciona uma linha em branco na interface quando o type_element é 'pula linha'
    """
    try:
        type_elem = element[1]  # type_element
        
        if type_elem == 'pula linha':
            st.markdown("<br>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Erro ao processar pula linha: {str(e)}")

def new_user(cursor, user_id: int, tabela: str):
    """
    Cria registros iniciais para um novo usuário na tabela especificada,
    copiando os dados do template (user_id = 0)
    
    Args:
        cursor: Cursor do banco de dados
        user_id: ID do usuário
        tabela: Nome da tabela para criar os registros
    """
    try:
        # Verifica se já existem registros para o usuário
        cursor.execute(f"""
            SELECT COUNT(*) FROM {tabela} 
            WHERE user_id = ?
        """, (user_id,))
        
        if cursor.fetchone()[0] == 0:
            # Copia dados do template (user_id = 0) para o novo usuário
            cursor.execute(f"""
                INSERT INTO {tabela} (
                    user_id, name_element, type_element, math_element,
                    msg_element, value_element, select_element, str_element,
                    e_col, e_row, section
                )
                SELECT 
                    ?, name_element, type_element, math_element,
                    msg_element, value_element, select_element, str_element,
                    e_col, e_row, section
                FROM {tabela}
                WHERE user_id = 0
            """, (user_id,))
            
            cursor.connection.commit()
            st.success("Dados iniciais criados com sucesso!")
            
    except Exception as e:
        st.error(f"Erro ao criar dados do usuário: {str(e)}")

def call_dados(cursor, element, tabela_destino: str):
    """
    Busca dados na tabela forms_tab e atualiza o value_element do registro atual.
    
    Args:
        cursor: Cursor do banco de dados
        element: Tupla com dados do elemento
        tabela_destino: Nome da tabela onde o valor será atualizado
    """
    try:
        name = element[0]        # name_element
        type_elem = element[1]   # type_element
        str_value = element[6]   # str_element
        user_id = element[10]    # user_id
        
        if type_elem == 'call_dados':
            # Busca o valor com CAST para garantir precisão decimal
            cursor.execute("""
                SELECT CAST(value_element AS DECIMAL(20, 8))
                FROM forms_tab 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (str_value, user_id))
            
            result = cursor.fetchone()
            
            if result:
                value = float(result[0]) if result[0] is not None else 0.0
                
                # Atualiza usando a tabela passada como parâmetro
                cursor.execute(f"""
                    UPDATE {tabela_destino}
                    SET value_element = CAST(? AS DECIMAL(20, 8))
                    WHERE name_element = ? 
                    AND user_id = ?
                """, (value, name, user_id))
                
                cursor.connection.commit()
            else:
                st.warning(f"Valor não encontrado na tabela forms_tab para {str_value} (user_id: {user_id})")
                
    except Exception as e:
        st.error(f"Erro ao processar call_dados: {str(e)}")

def create_br_ticks(max_value, target_ticks: int = 6):
    """
    Gera ticks "bonitos" (nice numbers) e define o maior tick como o primeiro múltiplo
    do passo acima do valor máximo. Assim, o último grid sempre cobre o maior valor.
    Retorna (tick_vals, tick_texts).
    """
    import math
    try:
        if max_value is None or max_value <= 0:
            return [0], ["0"]

        def nice_number(delta: float, round_value: bool) -> float:
            exponent = math.floor(math.log10(delta)) if delta > 0 else 0
            frac = delta / (10 ** exponent) if delta > 0 else 1
            if round_value:
                if frac < 1.5:
                    nice_frac = 1
                elif frac < 3:
                    nice_frac = 2
                elif frac < 7:
                    nice_frac = 5
                else:
                    nice_frac = 10
            else:
                if frac <= 1:
                    nice_frac = 1
                elif frac <= 2:
                    nice_frac = 2
                elif frac <= 5:
                    nice_frac = 5
                else:
                    nice_frac = 10
            return nice_frac * (10 ** exponent)

        # Passo "bonito" com base no número-alvo de ticks
        step = nice_number(max_value / max(1, (target_ticks - 1)), round_value=True)
        # Máximo do eixo é o primeiro múltiplo do passo acima do máximo real
        axis_max = math.ceil(max_value / step) * step

        # Gera a lista de ticks de 0 até axis_max (inclusive)
        num_steps = int(round(axis_max / step))
        tick_vals = [i * step for i in range(0, num_steps + 1)]

        tick_texts = [format_br_number(v) for v in tick_vals]
        return tick_vals, tick_texts
    except Exception as e:
        print(f"Erro ao criar ticks: {e}")
        return [0], ["0"]

def grafico_barra(cursor, element):
    """
    Cria um gráfico de barras verticais com dados da tabela específica.
    
    Args:
        cursor: Cursor do banco de dados SQLite
        element: Tupla contendo os dados do elemento do tipo 'grafico'
            [0] name_element: Nome do elemento
            [1] type_element: Tipo do elemento (deve ser 'grafico')
            [3] msg_element: Título/mensagem do gráfico
            [5] select_element: Lista de type_names separados por '|'
            [6] str_element: Lista de rótulos separados por '|'
            [9] section: Cor do gráfico (formato hex)
            [10] user_id: ID do usuário
    
    Configurações do Gráfico:
        - Título do gráfico usando msg_element
        - Barras verticais sem hover (tooltip)
        - Altura fixa de 400px
        - Largura responsiva
        - Sem legenda e títulos dos eixos
        - Fonte tamanho 14px
        - Valores no eixo Y formatados com separador de milhar
        - Cor das barras definida pela coluna 'section'
        - Sem barra de ferramentas do Plotly
    """
    try:
        # Extrai informações do elemento
        type_elem = element[1]   # type_element
        msg = element[3]         # msg_element (título do gráfico)
        select = element[5]      # select_element
        rotulos = element[6]     # str_element
        section = element[9]     # section (cor do gráfico)
        user_id = element[10]    # user_id
        
        # Validação do tipo e dados necessários
        if type_elem != 'grafico':
            return
            
        if not select or not rotulos:
            st.error("Configuração incompleta do gráfico: select ou rótulos vazios")
            return
            
        # Processa as listas de type_names e rótulos
        type_names = select.split('|')
        labels = rotulos.split('|')
        
        # Lista para armazenar os valores
        valores = []
        
        # Busca os valores para cada type_name no banco
        for type_name in type_names:
            tabela = st.session_state.tabela_escolhida
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = result[0] if result and result[0] is not None else 0.0
            valores.append(valor)
        
        # Define a cor das barras
        cor = section if section else '#1f77b4'  # azul padrão se não houver cor definida
        cores = [cor] * len(valores)  # aplica a mesma cor para todas as barras
        
        # Adiciona o título antes do gráfico usando markdown
        if msg:
            st.markdown(f"""
                <p style='
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                    color: #1E1E1E;
                    margin: 15px 0;
                    padding: 10px;
                '>{msg}</p>
            """, unsafe_allow_html=True)
        
        # Encontra o valor máximo para criar ticks brasileiros
        max_value = max(valores) if valores else 0
        tick_vals, tick_texts = create_br_ticks(max_value)
        
        # Cria o gráfico usando plotly express
        fig = px.bar(
            x=labels,
            y=valores,
            title=None,  # Remove título do plotly pois já usamos markdown
            color_discrete_sequence=cores
        )
        # Desabilita tooltips/hover nos traços
        fig.update_traces(hoverinfo='skip', hovertemplate=None)
        
        # Configura o layout do gráfico
        fig.update_layout(
            # Remove títulos dos eixos
            xaxis_title=None,
            yaxis_title=None,
            # Remove legenda
            showlegend=False,
            # Define dimensões
            height=400,
            width=None,  # largura responsiva
            # Configuração do eixo X
            xaxis=dict(
                tickfont=dict(size=15),  # tamanho fonte eixo X
                showgrid=False,
                showline=True,
                linecolor='#B0B0B0',
                linewidth=1
            ),
            # Configuração do eixo Y
            yaxis=dict(
                tickfont=dict(size=14),  # tamanho da fonte
                tickvals=tick_vals,
                ticktext=tick_texts,
                range=[0, tick_vals[-1] if tick_vals else 0],
                showgrid=True,
                gridcolor='#E0E0E0',
                gridwidth=1,
                showline=True,
                linecolor='#B0B0B0',
                linewidth=1
            ),
            # Desativa o hover (tooltip ao passar o mouse)
            hovermode=False,
            # Garante a linha do último tick do eixo Y
            shapes=[
                dict(
                    type='line',
                    xref='paper', x0=0, x1=1,
                    yref='y', y0=(tick_vals[-1] if tick_vals else 0), y1=(tick_vals[-1] if tick_vals else 0),
                    line=dict(color='#E0E0E0', width=1)
                )
            ]
        )
        
        # Exibe o gráfico no Streamlit
        # config={'displayModeBar': False} remove a barra de ferramentas do Plotly
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")

def tabela_dados(cursor, element):
    """
    Cria uma tabela estilizada com dados da tabela forms_resultados.
    Tabela transposta (vertical) com valores em vez de nomes.
    
    Args:
        cursor: Conexão com o banco de dados
        element: Tupla com os dados do elemento tipo 'tabela'
        
    Configurações do elemento:
        type_element: 'tabela'
        msg_element: título da tabela
        math_element: número de colunas da tabela
        select_element: type_names separados por | (ex: 'N24|N25|N26')
        str_element: rótulos separados por | (ex: 'Energia|Água|GEE')
        
    Nota: 
        - Layout usando três colunas do Streamlit para centralização
        - Proporção de colunas: [1, 8, 1] (10% vazio, 80% tabela, 10% vazio)
        - Valores formatados no padrão brasileiro
        - Tabela transposta (vertical) para melhor leitura
        - Coluna 'Valor' com largura aumentada em 25%
    """
    try:
        # Extrai informações do elemento
        type_elem = element[1]   # type_element
        msg = element[3]         # msg_element (título da tabela)
        select = element[5]      # select_element (type_names separados por |)
        rotulos = element[6]     # str_element (rótulos separados por |)
        user_id = element[10]    # user_id
        
        if type_elem != 'tabela':
            return
            
        # Validações iniciais
        if not select or not rotulos:
            st.error("Configuração incompleta da tabela: select ou rótulos vazios")
            return
            
        # Separa os type_names e rótulos
        type_names = select.split('|')
        rotulos = rotulos.split('|')
        
        # Valida se quantidade de rótulos corresponde aos type_names
        if len(type_names) != len(rotulos):
            st.error("Número de rótulos diferente do número de valores")
            return
            
        # Lista para armazenar os valores
        valores = []
        
        # Busca os valores para cada type_name
        for type_name in type_names:
            cursor.execute("""
                SELECT value_element 
                FROM forms_resultados 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_number(result[0]) if result and result[0] is not None else '0,00'
            valores.append(valor)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame({
            'Indicador': rotulos,
            'Valor': valores
        })
        
        # Criar três colunas, usando a do meio para a tabela
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Espaçamento fixo definido no código
            spacing = 20  # valor em pixels ajustado conforme solicitado
            
            # Adiciona quebras de linha antes do título
            num_breaks = spacing // 20
            for _ in range(num_breaks):
                st.markdown("<br>", unsafe_allow_html=True)
            
            # Exibe o título da tabela a esquerda
            st.markdown(f"<h4 style='text-align: left;'>{msg}</h4>", unsafe_allow_html=True)
            
            # Criar HTML da tabela com estilos inline
            html_table = f"""
            <div style='font-size: 20px; width: 80%;'>
                <table style='width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 0 8px rgba(0,0,0,0.1);'>
                    <thead>
                        <tr>
                            <th style='text-align: left; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Indicador</th>
                            <th style='text-align: right; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td style='padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Indicador']}</td><td style='text-align: right; padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Valor']}</td></tr>" for _, row in df.iterrows())}
                    </tbody>
                </table>
            </div>
            """
            
            # Exibe a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela: {str(e)}")

def gerar_dados_tabela(cursor, elemento, height_pct=100, width_pct=100):
    """
    Função auxiliar para gerar dados da tabela para o PDF
    """
    try:
        msg = elemento[3]         # msg_element
        select = elemento[5]      # select_element
        rotulos = elemento[6]     # str_element
        user_id = elemento[10]    # user_id
        
        # Limpar tags HTML do título para compatibilidade com ReportLab
        if msg:
            import re
            # Remove tags HTML comuns, substituindo <br> por espaço
            msg_clean = re.sub(r'<br\s*/?>', ' ', msg, flags=re.IGNORECASE)
            # Remove outras tags HTML
            msg_clean = re.sub(r'<[^>]+>', '', msg_clean)
            # Normalizar espaços múltiplos para um único espaço
            msg_clean = re.sub(r'\s+', ' ', msg_clean)
            # Remove espaços extras
            msg_clean = msg_clean.strip()
        else:
            msg_clean = ""
        
        if not select or not rotulos:
            st.error("Configuração incompleta da tabela: select ou rótulos vazios")
            return None
            
        # Separa os type_names e rótulos
        type_names = str(select).split('|')
        labels = str(rotulos).split('|')
        valores = []
        
        # Busca os valores para cada type_name
        for type_name in type_names:
            cursor.execute(f"""
                SELECT name_element, value_element 
                FROM {st.session_state.tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_number(result[1]) if result and result[1] is not None else '0,00'
            valores.append(valor)
        
        # Retornar dados formatados para a tabela
        return {
            'title': msg_clean if msg_clean else "Tabela de Dados",
            'data': [['Indicador', 'Valor']] + list(zip(labels, valores)),
            'height_pct': height_pct,
            'width_pct': width_pct
        }
        
    except Exception as e:
        st.error(f"Erro ao gerar dados da tabela: {str(e)}")
        return None

def gerar_dados_grafico(cursor, elemento, tabela_escolhida: str, height_pct=100, width_pct=100):
    try:
        msg = elemento[3]         # msg_element
        select = elemento[5]      # select_element
        rotulos = elemento[6]     # str_element
        section = elemento[9]     # section (cor do gráfico)
        user_id = elemento[10]    # user_id
        
        # Limpar tags HTML do título para compatibilidade com ReportLab
        if msg:
            import re
            # Remove tags HTML comuns, substituindo <br> por espaço
            msg_clean = re.sub(r'<br\s*/?>', ' ', msg, flags=re.IGNORECASE)
            # Remove outras tags HTML
            msg_clean = re.sub(r'<[^>]+>', '', msg_clean)
            # Normalizar espaços múltiplos para um único espaço
            msg_clean = re.sub(r'\s+', ' ', msg_clean)
            # Remove espaços extras
            msg_clean = msg_clean.strip()
        else:
            msg_clean = ""
        if not select or not rotulos:
            return None
        type_names = str(select).split('|')
        labels = str(rotulos).split('|')
        valores = []
        # Busca os valores para cada type_name
        for type_name in type_names:
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela_escolhida}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            result = cursor.fetchone()
            valor = float(result[0]) if result and result[0] is not None else 0.0
            valores.append(valor)
        cor = section if section else '#1f77b4'
        cores = [cor] * len(valores)
        # Ajustar base_width para ocupar mais da largura da página A4
        base_width = 250
        base_height = 180
        # largura dos gráficos igual à tabela (usando width_pct)
        adj_width = int(base_width * 2.2 * 0.8 * (width_pct / 100)) + 20  # aumenta 20 na largura
        adj_height = int(base_height * (height_pct / 100)) - 25           # reduz 25 na altura
        # Encontra o valor máximo para criar ticks brasileiros
        max_value = max(valores) if valores else 0
        tick_vals, tick_texts = create_br_ticks(max_value)
        
        fig = px.bar(
            x=labels,
            y=valores,
            title=None,
            color_discrete_sequence=cores
        )
        fig.update_layout(
            showlegend=False,
            height=adj_height,
            width=adj_width,
            margin=dict(t=30, b=50),
            xaxis=dict(
                title=None,
                tickfont=dict(size=8)
            ),
            yaxis=dict(
                title=None,
                tickfont=dict(size=10), # reduzido em 30%
                tickvals=tick_vals,
                ticktext=tick_texts,
                range=[0, tick_vals[-1] if tick_vals else 0],
                showgrid=True,
                gridcolor='#E0E0E0',
                gridwidth=1
            ),
            shapes=[
                dict(
                    type='line',
                    xref='paper', x0=0, x1=1,
                    yref='y', y0=(tick_vals[-1] if tick_vals else 0), y1=(tick_vals[-1] if tick_vals else 0),
                    line=dict(color='#E0E0E0', width=1)
                )
            ]
        )
        img_bytes = fig.to_image(format="png", scale=3)
        return {
            'title': msg_clean,
            'image': Image(io.BytesIO(img_bytes), 
                         width=adj_width,
                         height=adj_height)
        }
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")
        return None

def subtitulo(titulo_pagina: str):
    """
    Exibe o subtítulo da página e o botão de gerar PDF (temporariamente desabilitado)
    """
    try:
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown(f"""
                <p style='
                    text-align: Left;
                    font-size: 33px;
                    color: #000000;
                    margin-top: 10px;
                    margin-bottom: 30px;
                    font-family: sans-serif;
                    font-weight: 500;
                '>{titulo_pagina}</p>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("Gerar PDF", type="primary", key="btn_gerar_pdf"):
                try:
                    msg_placeholder = st.empty()
                    msg_placeholder.info("Gerando PDF... Por favor, aguarde.")
                    
                    for _ in range(3):
                        try:
                            conn = sqlite3.connect(DB_PATH, timeout=20)
                            cursor = conn.cursor()
                            break
                        except sqlite3.OperationalError as e:
                            if "database is locked" in str(e):
                                time.sleep(1)
                                continue
                            raise e
                    else:
                        st.error("Não foi possível conectar ao banco de dados. Tente novamente.")
                        return
                    
                    buffer = generate_pdf_content(
                        cursor, 
                        st.session_state.user_id,
                        st.session_state.tabela_escolhida
                    )
                    
                    if buffer:
                        conn.close()
                        msg_placeholder.success("PDF gerado com sucesso!")
                        
                        # Gera nome do arquivo baseado no subtítulo
                        configs = get_subtitle_configs()
                        subtitulo = configs["table_to_pdf_filename"].get(st.session_state.tabela_escolhida, "Simulações")
                        # Remove caracteres especiais e substitui espaços por underscores
                        nome_arquivo = subtitulo.replace(" ", "_").replace("-", "").replace(":", "").lower()
                        nome_arquivo = f"{nome_arquivo}.pdf"
                        
                        st.download_button(
                            label="Baixar PDF",
                            data=buffer.getvalue(),
                            file_name=nome_arquivo,
                            mime="application/pdf",
                        )
                    
                except Exception as e:
                    msg_placeholder.error(f"Erro ao gerar PDF: {str(e)}")
                    st.write("Debug: Stack trace completo:", traceback.format_exc())
                finally:
                    if 'conn' in locals() and conn:
                        conn.close()
                    
    except Exception as e:
        st.error(f"Erro ao gerar interface: {str(e)}")

def generate_pdf_content(cursor, user_id: int, tabela_escolhida: str):
    """
    Função específica para gerar o conteúdo do PDF usando uma conexão dedicada
    Novo layout: título, subtítulo, tabela centralizada, 4 gráficos em 2 linhas (2x2)
    """
    
    def clean_title_for_pdf(msg):
        """Função auxiliar para limpar tags HTML do título"""
        if msg:
            import re
            msg_clean = re.sub(r'<br\s*/?>', ' ', msg, flags=re.IGNORECASE)
            msg_clean = re.sub(r'<[^>]+>', '', msg_clean)
            msg_clean = re.sub(r'\s+', ' ', msg_clean)
            msg_clean = msg_clean.strip()
            return msg_clean
        else:
            return ""
    
    try:
        # Configurações de dimensões (em percentual)
        TABLE_HEIGHT_PCT = 25
        TABLE_WIDTH_PCT = 60
        GRAPH_HEIGHT_PCT = 100
        GRAPH_WIDTH_PCT = 100
        base_width = 250  # largura individual de cada gráfico/tabela
        base_height = 180 # altura individual de cada gráfico
        table_width = base_width * 2.2 * 0.8  # reduz 20% da largura da tabela
        table_height = base_height * (TABLE_HEIGHT_PCT / 100)
        graph_width = table_width  # gráficos agora têm a mesma largura da tabela
        graph_height = base_height

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        with sqlite3.connect(DB_PATH, timeout=20) as pdf_conn:
            pdf_cursor = pdf_conn.cursor()
            elements = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=21,  # Reduzido 20% (26 → 21)
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=21,  # Ajustado proporcionalmente
                spaceBefore=15,
                spaceAfter=20,
                borderRadius=5,
                backColor=colors.white,
                borderPadding=10
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,  # Reduzido 25% (20 → 16)
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=17,  # Ajustado proporcionalmente
                spaceBefore=10,
                spaceAfter=15
            )
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 16),  # cabeçalho
                ('TOPPADDING', (0, 1), (-1, -1), 12),    # corpo
                ('BOTTOMPADDING', (0, 1), (-1, -1), 12), # corpo
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROUNDEDCORNERS', [3, 3, 3, 3]),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
            ])

            # Estilo para títulos dos gráficos (reduzido em 20%)
            graphic_title_style = ParagraphStyle(
                'GraphicTitle',
                parent=styles['Heading2'],
                fontSize=11,  # Reduzido 20% (14 → 11)
                alignment=1,
                textColor=colors.HexColor('#1E1E1E'),
                fontName='Helvetica',
                leading=13,  # Ajustado proporcionalmente
                spaceBefore=6,
                spaceAfter=8
            )

            titulo_map = {
                "forms_resultados": "Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído",
                "forms_result_sea": "Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído",
                "forms_setorial": "Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído",
                "forms_setorial_sea": "Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído"
            }
            configs = get_subtitle_configs()
            subtitulo_map = configs["table_to_full_subtitle"]
            titulo_principal = titulo_map.get(tabela_escolhida, "Simulador")
            subtitulo_principal = subtitulo_map.get(tabela_escolhida, "Simulações")
            
            # Limpar tags HTML dos títulos para compatibilidade com ReportLab
            import re
            if titulo_principal:
                titulo_principal_clean = re.sub(r'<br\s*/?>', ' ', titulo_principal, flags=re.IGNORECASE)
                titulo_principal_clean = re.sub(r'<[^>]+>', '', titulo_principal_clean)
                titulo_principal_clean = re.sub(r'\s+', ' ', titulo_principal_clean)
                titulo_principal_clean = titulo_principal_clean.strip()
            else:
                titulo_principal_clean = "Simulador"
                
            if subtitulo_principal:
                subtitulo_principal_clean = re.sub(r'<br\s*/?>', ' ', subtitulo_principal, flags=re.IGNORECASE)
                subtitulo_principal_clean = re.sub(r'<[^>]+>', '', subtitulo_principal_clean)
                subtitulo_principal_clean = re.sub(r'\s+', ' ', subtitulo_principal_clean)
                subtitulo_principal_clean = subtitulo_principal_clean.strip()
            else:
                subtitulo_principal_clean = "Simulações"
            
            elements.append(Paragraph(titulo_principal_clean, title_style))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(subtitulo_principal_clean, subtitle_style))
            elements.append(Spacer(1, 20))

            # Buscar elementos da tabela e gráficos
            pdf_cursor.execute(f"""
                SELECT name_element, type_element, math_element, msg_element,
                       value_element, select_element, str_element, e_col, e_row,
                       section, user_id
                FROM {tabela_escolhida}
                WHERE (type_element = 'tabela' OR type_element = 'grafico')
                AND user_id = ?
                ORDER BY e_row, e_col
            """, (user_id,))
            elementos = pdf_cursor.fetchall()

            # Pega a primeira tabela e até 4 gráficos
            tabela = next((e for e in elementos if e[1] == 'tabela'), None)
            graficos = [e for e in elementos if e[1] == 'grafico'][:4]

            # --- ORGANIZAÇÃO DAS PÁGINAS DO PDF ---
            # Identificar os gráficos pelos títulos
            graficos_dict = {}
            for grafico in graficos:
                # Por padrão, altura 160 (será ajustada por página)
                dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=160, width_pct=100)
                if dados_grafico:
                    graficos_dict[dados_grafico['title']] = Table(
                        [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                        colWidths=[graph_width],
                        style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                    )

            # --- DIFERENCIAÇÃO DE LAYOUT POR TABELA ---
            if tabela_escolhida in ["forms_resultados", "forms_result_sea"]:
                # Layout padrão: Tabela + gráficos
                if tabela:
                    dados_tabela = gerar_dados_tabela(pdf_cursor, tabela, height_pct=TABLE_HEIGHT_PCT, width_pct=TABLE_WIDTH_PCT)
                    if dados_tabela:
                        t = Table(dados_tabela['data'], colWidths=[table_width * 0.6, table_width * 0.4])
                        t.setStyle(table_style)
                        elements.append(Table([[t]], colWidths=[table_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                        for _ in range(5):
                            elements.append(Spacer(1, 12))
                # Gráfico Demanda de Energia com altura reduzida em 25%
                if 'Demanda de Energia (MJ/1000kg de café)' in graficos_dict:
                    grafico_energia = next((g for g in graficos if 'Demanda de Energia' in g[3]), None)
                    if grafico_energia:
                        dados_grafico_energia = gerar_dados_grafico(pdf_cursor, grafico_energia, tabela_escolhida, height_pct=120, width_pct=100)
                        elements.append(Table(
                            [[Paragraph(dados_grafico_energia['title'], graphic_title_style)], [dados_grafico_energia['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                elements.append(PageBreak())

                # Página 2: Demanda de Água, Pegada de Carbono e Resíduos Sólidos (todos juntos, altura reduzida)
                titulos_graficos_p2 = [
                    'Demanda de Água (litros / 1000kg de café)',
                    'Pegada de Carbono (kg CO2eq/1000 kg de café)'
                ]
                residuos_key = next((k for k in graficos_dict if 'resíduo' in k.lower()), None)
                if residuos_key:
                    titulos_graficos_p2.append(residuos_key)
                for titulo in titulos_graficos_p2:
                    # Buscar gráfico usando título limpo
                    grafico = next((g for g in graficos if titulo in clean_title_for_pdf(g[3])), None)
                    if grafico:
                        dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=120, width_pct=100)
                        elements.append(Table(
                            [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                        elements.append(Spacer(1, 10))
            else:
                # Layout setorial: só gráficos, 2 por página
                # Página 1: Demanda de Energia e Demanda de Água
                palavras_chave_p1 = ["energia", "água"]
                graficos_p1 = []
                for palavra in palavras_chave_p1:
                    grafico = next((g for g in graficos if palavra in g[3].lower()), None)
                    if grafico:
                        dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=120, width_pct=100)
                        graficos_p1.append(Table(
                            [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                        graficos_p1.append(Spacer(1, 10))
                for g in graficos_p1:
                    elements.append(g)
                elements.append(PageBreak())
                # Página 2: Pegada de Carbono e Resíduos Sólidos
                palavras_chave_p2 = ["carbono", "resíduo"]
                graficos_p2 = []
                for palavra in palavras_chave_p2:
                    grafico = next((g for g in graficos if palavra in g[3].lower()), None)
                    if grafico:
                        dados_grafico = gerar_dados_grafico(pdf_cursor, grafico, tabela_escolhida, height_pct=120, width_pct=100)
                        graficos_p2.append(Table(
                            [[Paragraph(dados_grafico['title'], graphic_title_style)], [dados_grafico['image']]],
                            colWidths=[graph_width],
                            style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]
                        ))
                        graficos_p2.append(Spacer(1, 10))
                for g in graficos_p2:
                    elements.append(g)

            doc.build(elements)
            return buffer
    except Exception as e:
        st.error(f"Erro ao gerar conteúdo do PDF: {str(e)}")
        return None

def show_results(tabela_escolhida: str, titulo_pagina: str, user_id: int):
    """
    Função principal para exibir a interface web
    """
    try:
        if not user_id:
            st.error("Usuário não está logado!")
            return
            
        # Armazena a tabela na sessão para uso em outras funções
        st.session_state.tabela_escolhida = tabela_escolhida
        
        # Adiciona o subtítulo antes do conteúdo principal
        subtitulo(titulo_pagina)
        
        # Estabelece conexão com retry
        for _ in range(3):
            try:
                conn = sqlite3.connect(DB_PATH, timeout=20)
                cursor = conn.cursor()
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    time.sleep(1)
                    continue
                raise e
        else:
            st.error("Não foi possível conectar ao banco de dados. Tente novamente.")
            return
            
        # 1. Verifica se usuário tem dados em forms_tab
        verificar_dados_usuario(cursor, user_id)
        
        # 2. Atualiza todas as fórmulas e verifica o resultado
        if not atualizar_formulas(cursor, user_id):
            st.error("Erro ao atualizar fórmulas!")
            return

        # 3. Verifica/inicializa dados na tabela escolhida
        new_user(cursor, user_id, tabela_escolhida)
        conn.commit()
        
        # 4. Registra acesso à página
        registrar_acesso(
            user_id,
            "resultados",
            f"Acesso na simulação {titulo_pagina}"
        )

        # Configuração para esconder elementos durante a impressão e controlar quebra de página
        hide_streamlit_style = """
            <style>
                @media print {
                    [data-testid="stSidebar"] {
                        display: none !important;
                    }
                    .stApp {
                        margin: 0;
                        padding: 0;
                    }
                    #MainMenu {
                        display: none !important;
                    }
                    .page-break {
                        page-break-before: always !important;
                    }
                }
            </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
        
        # Buscar todos os elementos ordenados por row e col
        cursor.execute(f"""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row,
                   section, user_id
            FROM {tabela_escolhida}
            WHERE (type_element = 'titulo' OR type_element = 'pula linha' 
                  OR type_element = 'call_dados' OR type_element = 'grafico'
                  OR type_element = 'tabela')
            AND user_id = ?
            ORDER BY e_row, e_col
        """, (user_id,))
        
        elements = cursor.fetchall()
        
        # Contador para gráficos
        grafico_count = 0
        
        # Agrupar elementos por e_row
        row_elements = {}
        for element in elements:
            e_row = element[8]  # e_row do elemento
            if e_row not in row_elements:
                row_elements[e_row] = []
            row_elements[e_row].append(element)
        
        # Processar elementos por linha
        for e_row in sorted(row_elements.keys()):
            row_data = row_elements[e_row]
            
            # Primeiro processar tabelas em container separado
            tabelas = [elem for elem in row_data if elem[1] == 'tabela']
            for tabela in tabelas:
                with st.container():
                    # Centralizar a tabela usando colunas
                    col1, col2, col3 = st.columns([1, 8, 1])
                    with col2:
                        tabela_dados_sem_titulo(cursor, tabela)
            
            # Depois processar outros elementos em duas colunas
            outros_elementos = [elem for elem in row_data if elem[1] != 'tabela']
            if outros_elementos:
                with st.container():
                    col1, col2 = st.columns(2)
                    
                    # Processar elementos não-tabela
                    for element in outros_elementos:
                        e_col = element[7]  # e_col do elemento
                        
                        if e_col <= 3:
                            with col1:
                                if element[1] == 'grafico':
                                    grafico_count += 1
                                    grafico_barra(cursor, element)
                                    if grafico_count == 2:
                                        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
                                elif element[1] == 'titulo':
                                    titulo(cursor, element)
                                elif element[1] == 'pula linha':
                                    pula_linha(cursor, element)
                                elif element[1] == 'call_dados':
                                    call_dados(cursor, element, tabela_escolhida)
                        else:
                            with col2:
                                if element[1] == 'grafico':
                                    grafico_count += 1
                                    grafico_barra(cursor, element)
                                    if grafico_count == 2:
                                        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
                                elif element[1] == 'titulo':
                                    titulo(cursor, element)
                                elif element[1] == 'pula linha':
                                    pula_linha(cursor, element)
                                elif element[1] == 'call_dados':
                                    call_dados(cursor, element, tabela_escolhida)
        
    except Exception as e:
        st.error(f"Erro ao carregar resultados: {str(e)}")
    finally:
        if conn:
            conn.close()

def tabela_dados_sem_titulo(cursor, element):
    """Versão da função tabela_dados sem o título"""
    try:
        type_elem = element[1]   # type_element
        select = element[5]      # select_element
        rotulos = element[6]     # str_element
        user_id = element[10]    # user_id
        
        if type_elem != 'tabela':
            return
            
        # Validações iniciais
        if not select or not rotulos:
            st.error("Configuração incompleta da tabela: select ou rótulos vazios")
            return
            
        # Separa os type_names e rótulos
        type_names = select.split('|')
        rotulos = rotulos.split('|')
        
        # Valida se quantidade de rótulos corresponde aos type_names
        if len(type_names) != len(rotulos):
            st.error("Número de rótulos diferente do número de valores")
            return
            
        # Lista para armazenar os valores
        valores = []
        
        # Busca os valores para cada type_name
        for type_name in type_names:
            tabela = st.session_state.tabela_escolhida  # Pega a tabela da sessão
            cursor.execute(f"""
                SELECT value_element 
                FROM {tabela}
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = format_br_number(result[0]) if result and result[0] is not None else '0,00'
            valores.append(valor)
        
        # Criar DataFrame com os dados
        df = pd.DataFrame({
            'Indicador': rotulos,
            'Valor': valores
        })
        
        # Criar três colunas, usando a do meio para a tabela
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Criar HTML da tabela com estilos inline (sem o título)
            html_table = f"""
            <div style='font-size: 20px; width: 80%;'>
                <table style='width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 0 8px rgba(0,0,0,0.1);'>
                    <thead>
                        <tr>
                            <th style='text-align: left; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Indicador</th>
                            <th style='text-align: right; padding: 10px; background-color: #e8f5e9; border-bottom: 2px solid #dee2e6;'>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td style='padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Indicador']}</td><td style='text-align: right; padding: 8px 10px; border-bottom: 1px solid #dee2e6;'>{row['Valor']}</td></tr>" for _, row in df.iterrows())}
                    </tbody>
                </table>
            </div>
            """
            
            # Exibe a tabela HTML
            st.markdown(html_table, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela: {str(e)}")

if __name__ == "__main__":
    show_results()

