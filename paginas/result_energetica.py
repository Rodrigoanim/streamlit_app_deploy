# Arquivo: result_energetica.py
# Data: 25/02/2025 20:00
# Pagina de Análise Energética - Torrefação
# Adaptação para o uso de Discos SSD e a pasta Data para o banco de dados
# ajustes layout Anna TWS

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
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
    Função principal para exibir a página de resultados com layout em duas colunas
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
                    break
            
            # Depois processa os elementos da linha normalmente
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
                            elif element[1] == 'tabela_ae':
                                tabela_ae(cursor, element)
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
                            elif element[1] == 'tabela_ae':
                                tabela_ae(cursor, element)
        
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
        user_id = element[10]    # user_id
        
        # Configurações do gráfico
        series = ['Simulação da Empresa', 'Menor valor setorial', 'Média setorial', 'Maior valor setorial']
        cores = ['#00008B', '#ADD8E6', '#3CB371', '#FFA500']  # Azul escuro, Azul claro, Verde, Laranja
        
        # Busca dados do banco
        dados = buscar_dados_grafico(cursor, select, user_id)
        
        # Prepara DataFrame para plotly
        df = preparar_dataframe_grafico(dados, series, rotulos.split('|'))
        
        # Cria e configura o gráfico
        fig = criar_grafico_barras(df, cores)
        
        # Exibe o gráfico
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico AE: {str(e)}")

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

def preparar_dataframe_grafico(dados, series, categorias):
    """Prepara DataFrame para o gráfico"""
    df_data = []
    for i, serie in enumerate(series):
        for j, categoria in enumerate(categorias):
            df_data.append({
                'Categoria': categoria,
                'Valor': dados[j][i],
                'Série': serie
            })
    return pd.DataFrame(df_data)

def criar_grafico_barras(df, cores):
    """Cria e configura o gráfico de barras"""
    fig = px.bar(
        df,
        x='Categoria',
        y='Valor',
        color='Série',
        barmode='group',
        color_discrete_sequence=cores
    )
    
    # Configurações do layout
    fig.update_layout(
        xaxis_title=None,
        # yaxis_title="MJ/1000kg de café",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(tickfont=dict(size=14)),
        yaxis=dict(
            tickfont=dict(size=14),
            tickformat=",.",
            separatethousands=True
        ),
        margin=dict(t=60, b=100)
    )
    
    return fig

def tabela_ae(cursor, element):
    """
    Cria uma tabela estilizada para análise energética.
    """
    try:
        # Extrai dados do elemento
        select = element[5]      # select_element
        str_value = element[6]   # str_element
        user_id = element[10]    # user_id
        
        # Configurações da tabela
        series = ['Simulação da Empresa', 'Menor valor setorial', 'Média setorial', 'Maior valor setorial']
        
        # Estrutura do container
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col2:
            # Busca e prepara dados
            dados = buscar_dados_tabela(cursor, select, user_id)
            df = criar_dataframe_tabela(dados, series, str_value.split('|'))
            
            # Aplica estilo e exibe
            styled_df = estilizar_tabela(df)
            st.table(styled_df)
            st.markdown("<br>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erro ao criar tabela AE: {str(e)}")

def buscar_dados_tabela(cursor, select, user_id):
    """Busca dados do banco para a tabela"""
    return buscar_dados_grafico(cursor, select, user_id)  # Mesma lógica do gráfico

def criar_dataframe_tabela(dados, series, categorias):
    """
    Cria DataFrame para a tabela sem a coluna de índice
    """
    df_dict = {'Indicadores': series}
    for i, categoria in enumerate(categorias):
        df_dict[categoria] = [format_br_number(dados[i][j]) for j in range(4)]
    
    # Cria o DataFrame e usa a primeira coluna como índice
    df = pd.DataFrame(df_dict)
    return df.set_index('Indicadores')

def estilizar_tabela(df):
    """
    Aplica estilos à tabela com colunas de largura igual
    """
    # Calcula a largura de cada coluna (100% dividido pelo número total de colunas)
    num_colunas = len(df.columns) + 1  # +1 para incluir a coluna de índice
    largura_coluna = f"{100/num_colunas}%"
    
    return df.style.set_properties(**{
        'background-color': 'white',
        'border': '1px solid #dee2e6',
        'text-align': 'right',
        'padding': '10px 12px',
        'font-size': '20px',
        'width': largura_coluna  # Define largura igual para todas as colunas
    }).set_table_styles([
        # Estilo geral da tabela
        {'selector': '',
         'props': [('border-collapse', 'collapse'),
                  ('margin', '50px auto 25px auto'),
                  ('width', '100%')]},  # Garante que a tabela ocupe toda a largura disponível
        # Estilo do cabeçalho
        {'selector': 'thead th',
         'props': [
             ('background-color', '#e8f5e9'),
             ('font-weight', 'bold'),
             ('border-bottom', '2px solid #dee2e6'),
             ('font-size', '20px'),
             ('width', largura_coluna)  # Largura igual para colunas do cabeçalho
         ]},
        # Estilo das linhas do corpo
        {'selector': 'tbody tr',
         'props': [('background-color', 'white')]},
        # Estilo das células e do índice
        {'selector': 'td, th',
         'props': [
             ('border-bottom', '1px solid #dee2e6'),
             ('text-align', 'left'),
             ('padding', '10px 12px'),
             ('width', largura_coluna)  # Largura igual para todas as células
         ]},
        # Estilo específico para células de dados
        {'selector': 'td',
         'props': [('text-align', 'right')]},
        # Estilo específico para o índice
        {'selector': 'th',
         'props': [
             ('text-align', 'left'),
             ('font-weight', 'normal'),
             ('width', largura_coluna)  # Largura igual para coluna de índice
         ]},
    ])

if __name__ == "__main__":
    show_results()

