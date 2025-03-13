# Arquivo: result_energetica.py
# Data: 11/03/2025 16:00
# Pagina de Análise Energética - Torrefação
# Adaptação para o uso de Discos SSD e a pasta Data para o banco de dados
# ajustes layout Anna - versão 2

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import DB_PATH  # Adicione esta importação
from paginas.form_model_recalc import verificar_dados_usuario, calculate_formula, atualizar_formulas

def format_br_number(value):
    """
    Formata um número para o padrão brasileiro (vírgula como separador decimal)
    Retorna números inteiros, sem casas decimais
    """
    try:
        if value is None:
            return "0"
        
        float_value = float(value)
        # Arredonda para inteiro e formata com separador de milhar
        return f"{int(round(float_value)):,}".replace(',', '.')
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

def new_user(cursor, user_id):
    """
    Cria registros iniciais para um novo usuário na tabela forms_energetica,
    copiando os dados do template (user_id = 0)
    """
    try:
        # Verifica se já existem registros para o usuário
        cursor.execute("""
            SELECT COUNT(*) FROM forms_energetica 
            WHERE user_id = ?
        """, (user_id,))
        
        if cursor.fetchone()[0] == 0:
            # Copia dados do template (user_id = 0) para o novo usuário
            cursor.execute("""
                INSERT INTO forms_energetica (
                    user_id, name_element, type_element, math_element,
                    msg_element, value_element, select_element, str_element,
                    e_col, e_row, section
                )
                SELECT 
                    ?, name_element, type_element, math_element,
                    msg_element, value_element, select_element, str_element,
                    e_col, e_row, section
                FROM forms_energetica
                WHERE user_id = 0
            """, (user_id,))
            
            cursor.connection.commit()
            st.success("Dados iniciais criados com sucesso!")
            
    except Exception as e:
        st.error(f"Erro ao criar dados do usuário: {str(e)}")

def call_dados(cursor, element):
    """
    Busca dados na tabela forms_tab e atualiza o value_element do registro atual.
    Mantém consistência usando o mesmo user_id.
    """
    try:
        name = element[0]        # name_element
        type_elem = element[1]   # type_element
        str_value = element[6]   # str_element
        user_id = element[10]    # user_id
        
        if type_elem == 'call_dados':
            cursor.execute("""
                SELECT value_element 
                FROM forms_tab 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (str_value, user_id))
            
            result = cursor.fetchone()
            
            if result:
                value = result[0]
                
                cursor.execute("""
                    UPDATE forms_energetica 
                    SET value_element = ? 
                    WHERE name_element = ? 
                    AND user_id = ?
                """, (value, name, user_id))
                
                cursor.connection.commit()
            else:
                st.warning(f"Valor não encontrado na tabela forms_tab para {str_value} (user_id: {user_id})")
                
    except Exception as e:
        st.error(f"Erro ao processar call_dados: {str(e)}")

def subtitulo():
    """
    Exibe um subtítulo centralizado com estilo personalizado
    """
    st.markdown("""
        <p style='
            text-align: Left;
            font-size: 36px;
            color: #4A4A4A;
            margin-top: 4px;
            margin-bottom: 25px;
            font-family: sans-serif;
            font-weight: 500;
        '>Análise Energética - Torrefação</p>
    """, unsafe_allow_html=True)

def show_results():
    """
    Função principal para exibir a página de resultados
    """
    try:
        if 'user_id' not in st.session_state:
            st.error("Usuário não está logado!")
            return
            
        user_id = st.session_state.user_id
        
        # Adiciona o subtítulo no início da página
        subtitulo()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Atualiza todas as fórmulas
        if not atualizar_formulas(cursor, user_id):
            st.error("Erro ao atualizar fórmulas!")
            return
        
        # Garante que existam dados para o usuário
        new_user(cursor, user_id)
        
        # Buscar todos os elementos
        cursor.execute("""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row,
                   section, user_id
            FROM forms_energetica
            WHERE (type_element = 'titulo' OR type_element = 'pula linha' 
                  OR type_element = 'call_dados' OR type_element = 'grafico_ae'
                  OR type_element = 'tabela_ae')
            AND user_id = ?
            ORDER BY e_row, e_col
        """, (user_id,))
        
        elements = cursor.fetchall()
        row_elements = {}
        
        # Agrupa elementos por e_row
        for element in elements:
            e_row = element[8]
            if e_row not in row_elements:
                row_elements[e_row] = []
            row_elements[e_row].append(element)
        
        # Processa linha por linha
        for e_row in sorted(row_elements.keys()):
            # Primeiro verifica se tem tabela_ae nesta linha para mostrar o título
            for element in row_elements[e_row]:
                if element[1] == 'tabela_ae':
                    # Título centralizado ANTES de processar os elementos da linha
                    st.markdown(f"""
                        <p style='
                            text-align: center;
                            margin-top: 5px;
                            margin-bottom: 20px;
                            font-size: 24px;
                            color: #4A4A4A;
                            font-family: sans-serif;
                        '>{element[3]}</p>
                    """, unsafe_allow_html=True)
                    
                    # Para tabelas, usar container único sem colunas
                    for elem in row_elements[e_row]:
                        if elem[1] == 'tabela_ae':
                            tabela_ae(cursor, elem)
                    break
            else:
                # Para outros elementos, manter as duas colunas
                with st.container():
                    col1, col2 = st.columns(2)
                    
                    for element in row_elements[e_row]:
                        e_col = element[7]
                        
                        if e_col <= 3:
                            with col1:
                                if element[1] == 'titulo':
                                    titulo(cursor, element)
                                elif element[1] == 'pula linha':
                                    pula_linha(cursor, element)
                                elif element[1] == 'call_dados':
                                    call_dados(cursor, element)
                                elif element[1] == 'grafico_ae':
                                    grafico_ae(cursor, element)
                        else:
                            with col2:
                                if element[1] == 'titulo':
                                    titulo(cursor, element)
                                elif element[1] == 'pula linha':
                                    pula_linha(cursor, element)
                                elif element[1] == 'call_dados':
                                    call_dados(cursor, element)
                                elif element[1] == 'grafico_ae':
                                    grafico_ae(cursor, element)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao carregar resultados: {str(e)}")

def grafico_ae(cursor, element):
    """
    Cria um gráfico de barras agrupadas para análise energética.
    """
    try:
        # Extrai dados do elemento
        select = element[5]      # select_element
        rotulos = element[6]     # str_element
        msg = element[3]         # msg_element
        user_id = element[10]    # user_id
        
        if not select or not rotulos:
            st.warning("Dados insuficientes para criar o gráfico.")
            return
            
        # Configurações do gráfico
        series = ['Simulação', 'Menor valor setorial', 'Média setorial', 'Maior valor setorial']
        cores = ['#00008B', '#ADD8E6', '#3CB371', '#FFA500']
        
        # Processa dados
        categorias = rotulos.split('|')
        dados = buscar_dados_grafico(cursor, select, user_id)
        
        if not dados:
            st.warning("Não foram encontrados dados para o gráfico.")
            return
            
        # Cria DataFrame para plotly
        df_plot = pd.DataFrame(dados, columns=series)
        df_plot.index = categorias
        
        # Cria gráfico
        fig = go.Figure()
        
        for i, serie in enumerate(series):
            fig.add_trace(go.Bar(
                name=serie,
                x=categorias,
                y=df_plot[serie],
                marker_color=cores[i]
            ))
            
        # Layout
        fig.update_layout(
            title=msg,
            barmode='group',
            # xaxis_title="Categorias", # retirada para o gráfico ficar mais limpo
            # yaxis_title="MJ/1000kg de café", # retirada para o gráfico ficar mais limpo
            showlegend=True,
            legend=dict(
                orientation="h",  # horizontal
                yanchor="bottom",
                y=-0.3,  # posição abaixo do gráfico
                xanchor="center",
                x=0.5,  # centralizado
                title=None  # remove o título "Valores"
            ),
            # Remove a barra de ferramentas
            modebar_remove=[
                'zoom', 'pan', 'select', 'zoomIn', 'zoomOut', 
                'autoScale', 'resetScale', 'lasso2d', 'toImage'
            ],
            height=400
        )
        
        # Exibe
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico AE: {str(e)}")
        print(f"Erro detalhado: {str(e)}")

def buscar_dados_grafico(cursor, select, user_id):
    """Busca dados do banco para o gráfico"""
    dados = []
    grupos_dados = [grupo.split(',') for grupo in select.split('|')]
    
    for grupo in grupos_dados:
        valores_grupo = []
        for type_name in grupo:
            cursor.execute("""
                SELECT value_element 
                FROM forms_energetica 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC
                LIMIT 1
            """, (type_name.strip(), user_id))
            
            result = cursor.fetchone()
            valor = result[0] if result and result[0] is not None else 0.0
            valores_grupo.append(valor)
        dados.append(valores_grupo)
    
    return dados

def tabela_ae(cursor, element):
    """
    Cria uma tabela estilizada para análise energética.
    """
    try:
        # Extrai dados do elemento
        select = element[5]      # select_element (H54,H35,H49,J54,I54)
        user_id = element[10]    # user_id do usuário logado
        
        # Busca dados
        valores_ref = select.split(',')
        if len(valores_ref) != 5:
            st.warning("Configuração incorreta dos dados da tabela.")
            return
        
        # Busca valores do banco usando o user_id correto
        dados = []
        for ref in valores_ref:
            ref = ref.strip()
            cursor.execute("""
                SELECT value_element 
                FROM forms_energetica 
                WHERE name_element = ? 
                AND user_id = ?
                ORDER BY ID_element DESC 
                LIMIT 1
            """, (ref, user_id))
            
            result = cursor.fetchone()
            if result and result[0] is not None:
                valor = round(float(result[0]))
                valor_formatado = f"{valor:,.0f}".replace(',', '.')
            else:
                valor_formatado = "0"
            dados.append(valor_formatado)
        
        # Cria DataFrame - removida a coluna de índice
        df = pd.DataFrame({
            'Demandas de energia (MJ/1000kg de café)': [
                'Total',
                'Elétrica',
                'Térmica',
                'Renovável',
                'Fóssil'
            ],
            'Simulação da Empresa': dados
        }).reset_index(drop=True)  # Remove explicitamente o índice
        
        # Aplica estilo
        styled_df = df.style.set_properties(**{
            'text-align': 'left',
            'padding': '10px',
            'width': '50%'  # Define largura igual para ambas as colunas
        }).set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#f0f0f0'),
                ('text-align', 'center'),
                ('padding', '10px'),
                ('font-weight', 'bold'),
                ('width', '50%')  # Define largura igual para cabeçalhos
            ]},
            {'selector': 'td', 'props': [
                ('text-align', 'left'),
                ('width', '50%')  # Define largura igual para células
            ]},
            {'selector': 'td:last-child', 'props': [
                ('text-align', 'center')
            ]},
            # Esconde o índice
            {'selector': '.index_name', 'props': [('display', 'none')]},
            {'selector': '.row_heading', 'props': [('display', 'none')]},
            {'selector': '.blank', 'props': [('display', 'none')]}
        ])
        
        # Centraliza a tabela usando apenas uma coluna central
        _, col, _ = st.columns([1,2,1])
        with col:
            st.table(styled_df)
        
    except Exception as e:
        st.error(f"Erro ao criar tabela AE: {str(e)}")
        print(f"Erro detalhado: {str(e)}")

def buscar_valor_referencia(cursor, referencia, user_id):
    """
    Busca o valor de uma referência específica no banco de dados.
    """
    try:
        cursor.execute("""
            SELECT value_element 
            FROM forms_energetica 
            WHERE name_element = ? AND user_id = ?
        """, (referencia, user_id))
        
        resultado = cursor.fetchone()
        if resultado:
            return f"{resultado[0]:,.0f}"
        return None
        
    except Exception as e:
        print(f"Erro ao buscar valor de referência: {str(e)}")
        return None

if __name__ == "__main__":
    show_results()

