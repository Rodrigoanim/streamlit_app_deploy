# Arquivo: result_energetica.py
# Data: 12/08/2025 15:00
# Pagina de Análise Energética - Torrefação
# Adaptação para o uso de Discos SSD e a pasta Data para o banco de dados
# ajustes layout Anna e ABIC

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import DB_PATH  # Adicione esta importação
from paginas.form_model_recalc import verificar_dados_usuario, calculate_formula, atualizar_formulas
import io
import time
import traceback
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)

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
            color: #000000;
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
        
        # Botão Gerar PDF na coluna da direita
        col_esq, col_centro, col_dir = st.columns([3,2,3])
        with col_dir:
            gerar_pdf = st.button("Gerar PDF", type="primary", key="btn_gerar_pdf_energetica")
        with col_centro:
            msg_placeholder = st.empty()
        if gerar_pdf:
            try:
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
                buffer = generate_pdf_content_energetica(cursor, st.session_state.user_id)
                if buffer:
                    conn.close()
                    msg_placeholder.success("PDF gerado com sucesso!")
                    # Centralizar o botão de download
                    col_esq_dl, col_centro_dl, col_dir_dl = st.columns([3,2,3])
                    with col_centro_dl:
                        # Gera nome do arquivo baseado no subtítulo
                        titulo_arquivo = "Análise Energética - Torrefação"
                        # Remove caracteres especiais e substitui espaços por underscores
                        nome_arquivo = titulo_arquivo.replace(" ", "_").replace("-", "_").replace(":", "").lower()
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
            # Exibe a tabela apenas para o primeiro elemento do tipo 'tabela_ae' de cada linha
            tabela_exibida = False
            elementos_nao_tabela = []
            
            # Primeiro, processa a tabela se existir
            for element in row_elements[e_row]:
                if element[1] == 'tabela_ae' and not tabela_exibida:
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
                    tabela_ae(cursor, element)
                    tabela_exibida = True
                elif element[1] != 'tabela_ae':
                    elementos_nao_tabela.append(element)
            
            # Depois processa os outros elementos em duas colunas
            if elementos_nao_tabela:
                with st.container():
                    col1, col2 = st.columns(2)
                    for element in elementos_nao_tabela:
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
        
    except Exception as e:
        st.error(f"Erro ao carregar resultados: {str(e)}")

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

def grafico_ae(cursor, element):
    """
    Cria um gráfico de barras agrupadas para análise energética.
    """
    try:
        # Extrai dados do elemento
        select = element[5]      # select_element
        rotulos = element[6]     # str_element
        msg = element[3]         # msg_element (título do gráfico)
        user_id = element[10]    # user_id
        if not select or not rotulos:
            st.warning("Dados insuficientes para criar o gráfico.")
            return
        # Configurações do gráfico
        series = ['Simulação', 'Menor valor setorial', 'Média setorial', 'Maior valor setorial']
        cores = ['#00008B', '#8eb0ae', '#53a7a9', '#007a7d']
        # Processa dados
        categorias = rotulos.split('|')
        dados = buscar_dados_grafico(cursor, select, user_id)
        if not dados:
            st.warning("Não foram encontrados dados para o gráfico.")
            return
        # Cria DataFrame para plotly
        df_plot = pd.DataFrame(dados, columns=series)
        df_plot.index = categorias
        
        # Encontra o valor máximo para criar ticks brasileiros
        max_value = df_plot.values.max() if len(dados) > 0 else 0
        tick_vals, tick_texts = create_br_ticks(max_value)
        
        # Cria gráfico
        fig = go.Figure()
        for i, serie in enumerate(series):
            fig.add_trace(go.Bar(
                name=serie,
                x=categorias,
                y=df_plot[serie],
                marker_color=cores[i],
                hoverinfo='skip',
                hovertemplate=None
            ))
        # Layout
        fig.update_layout(
            title=dict(
                text=msg if msg and msg.lower() != 'undefined' else '',
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top',
                font=dict(size=18)
            ),
            barmode='group',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.4,
                xanchor="center",
                x=0.5,
                title=None
            ),
            margin=dict(b=100),
            modebar_remove=[
                'zoom', 'pan', 'select', 'zoomIn', 'zoomOut', 
                'autoScale', 'resetScale', 'lasso2d', 'toImage'
            ],
            height=400,
            xaxis=dict(
                tickangle=0,
                tickfont=dict(size=14),  # tamanho do fonte do eixo X
                showgrid=False,
                showline=True,
                linecolor='#B0B0B0',
                linewidth=1
            ),
            yaxis=dict(
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
            shapes=[
                dict(
                    type='line',
                    xref='paper', x0=0, x1=1,
                    yref='y', y0=(tick_vals[-1] if tick_vals else 0), y1=(tick_vals[-1] if tick_vals else 0),
                    line=dict(color='#E0E0E0', width=1)
                )
            ]
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
        
        # Cria DataFrame
        df = pd.DataFrame({
            'Demandas de energia (MJ/1000kg de café)': [
                'Total',
                'Elétrica',
                'Térmica',
                'Renovável',
                'Fóssil'
            ],
            'Simulação da Empresa': dados
        }, index=None)

        # Aplica estilos CSS
        styles = [
            {
                'selector': '',
                'props': [('border-collapse', 'collapse')]
            },
            {
                'selector': 'thead th',
                'props': [
                    ('background-color', '#e8f5e9'),
                    ('color', 'black'),
                    ('font-weight', 'bold'),
                    ('text-align', 'center'),
                    ('padding', '12px'),
                    ('border', '1px solid #ddd')
                ]
            },
            {
                'selector': 'td',
                'props': [
                    ('padding', '10px'),
                    ('border', '1px solid #ddd'),
                    ('text-align', 'left')
                ]
            }
        ]

        # Aplica estilos e configurações
        styled_df = df.style\
            .set_table_styles(styles)\
            .apply(lambda x: ['background-color: #f5f5f5' if i % 2 == 0 else 'background-color: white' for i in range(len(x))], axis=0)\
            .set_properties(**{'text-align': 'left'})\
            .set_properties(subset=['Simulação da Empresa'], **{'text-align': 'center'})

        # Centraliza a tabela usando colunas
        _, col, _ = st.columns([1,2,1])
        with col:
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
        
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

def generate_pdf_content_energetica(cursor, user_id: int):
    """
    Gera o PDF da Análise Energética para o usuário logado:
    Página 1: Tabela e gráfico Demandas Elétricas e Térmicas
    Página 2: gráfico Demandas Energias Fóssil e Renovável
    """
    try:
        # Configurações de layout
        base_width = 250
        base_height = 180
        graph_width = base_width * 2.2 * 0.8
        graph_height = 300

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

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
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=18,  # Mantido tamanho original
            alignment=1,
            textColor=colors.HexColor('#1E1E1E'),
            fontName='Helvetica',
            leading=22,  # Valor original
            spaceBefore=10,
            spaceAfter=15
        )
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

        elements = []
        # Título principal, título e subtítulo (espaçamentos reduzidos)
        elements.append(Paragraph("Ferramenta para Cálculo de Indicadores Ambientais da Produção de Café Torrado e Moído", title_style))
        elements.append(Spacer(1, 8))  # Reduzido de 15 para 8
        elements.append(Paragraph("Análise Energética - Torrefação", subtitle_style))
        elements.append(Spacer(1, 5))  # Reduzido de 10 para 5
        elements.append(Paragraph("Indicadores Energéticos da Etapa de Torrefação", subtitle_style))
        elements.append(Spacer(1, 12))  # Reduzido de 20 para 12

        # Buscar elementos da tabela e gráficos
        cursor.execute("""
            SELECT name_element, type_element, math_element, msg_element,
                   value_element, select_element, str_element, e_col, e_row,
                   section, user_id
            FROM forms_energetica
            WHERE (type_element = 'tabela_ae' OR type_element = 'grafico_ae')
            AND user_id = ?
            ORDER BY e_row, e_col
        """, (user_id,))
        elementos = cursor.fetchall()

        # Tabela (se houver)
        tabela = next((e for e in elementos if e[1] == 'tabela_ae'), None)
        # Gráfico 1: Demandas Elétricas e Térmicas
        graficos = [e for e in elementos if e[1] == 'grafico_ae']
        grafico1 = next((g for g in graficos if 'elétrica' in g[3].lower() or 'térmica' in g[3].lower()), None)
        # Gráfico 2: Demandas Energias Fóssil e Renovável
        grafico2 = next((g for g in graficos if 'fóssil' in g[3].lower() or 'renovável' in g[3].lower()), None)

        # Página 1: tabela e gráfico 1
        if tabela:
            select = tabela[5]
            user_id = tabela[10]
            valores_ref = select.split(',')
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
            df = pd.DataFrame({
                'Demandas de energia (MJ/1000kg de café)': [
                    'Total', 'Elétrica', 'Térmica', 'Renovável', 'Fóssil'
                ],
                'Simulação da Empresa': dados
            }, index=None)  # Removendo o índice na criação do DataFrame
            table_data = [list(df.columns)] + df.values.tolist()
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10.5),  # 25% menor que 14
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 16),
                ('TOPPADDING', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('ROUNDRECT', (0, 0), (-1, -1), 10, colors.black),  # Arredonda os cantos
            ])
            t = Table(table_data, colWidths=[graph_width * 0.6, graph_width * 0.4])
            t.setStyle(table_style)
            elements.append(Table([[t]], colWidths=[graph_width], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            elements.append(Spacer(1, 10))  # Reduzido de 20 para 10

        if grafico1:
            select = grafico1[5]
            rotulos = grafico1[6]
            msg = grafico1[3]
            user_id = grafico1[10]
            series = ['Simulação', 'Menor valor setorial', 'Média setorial', 'Maior valor setorial']
            cores = ['#00008B', '#8eb0ae', '#53a7a9', '#007a7d']
            categorias = rotulos.split('|')
            dados = buscar_dados_grafico(cursor, select, user_id)
            if dados:
                df_plot = pd.DataFrame(dados, columns=series)
                df_plot.index = categorias
                
                # Encontra o valor máximo para criar ticks brasileiros
                max_value = df_plot.values.max() if len(dados) > 0 else 0
                tick_vals, tick_texts = create_br_ticks(max_value)
                
                fig = go.Figure()
                for i, serie in enumerate(series):
                    fig.add_trace(go.Bar(
                        name=serie,
                        x=categorias,
                        y=df_plot[serie],
                        marker_color=cores[i],
                        hoverinfo='skip',
                        hovertemplate=None
                    ))
                fig.update_layout(
                    title=None,
                    barmode='group',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.4,
                        xanchor="center",
                        x=0.5,
                        title=None,
                        font=dict(size=10)
                    ),
                    margin=dict(b=120, l=50, r=50, t=20),
                    height=graph_height,
                    width=graph_width,
                    xaxis=dict(
                        tickangle=0,
                        tickfont=dict(size=8),
                        tickmode='array',
                        ticktext=categorias,
                        tickvals=categorias,
                        showgrid=False,
                        showline=True,
                        linecolor='#B0B0B0',
                        linewidth=1
                    ),
                    yaxis=dict(
                        title=None,
                        tickfont=dict(size=8),  # Reduzido 20% (10 → 8)
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
                # Limpar tags HTML do título para compatibilidade com ReportLab
                import re
                if msg:
                    msg_clean = re.sub(r'<br\s*/?>', ' ', msg, flags=re.IGNORECASE)
                    msg_clean = re.sub(r'<[^>]+>', '', msg_clean)
                    msg_clean = re.sub(r'\s+', ' ', msg_clean)
                    msg_clean = msg_clean.strip()
                else:
                    msg_clean = ""
                elements.append(Paragraph(msg_clean, graphic_title_style))
                elements.append(Image(io.BytesIO(img_bytes), width=graph_width, height=graph_height))
                elements.append(Spacer(1, 10))  # Reduzido de 20 para 10

        elements.append(PageBreak())

        # Página 2: gráfico 2
        if grafico2:
            select = grafico2[5]
            rotulos = grafico2[6]
            msg = grafico2[3]
            user_id = grafico2[10]
            series = ['Simulação', 'Menor valor setorial', 'Média setorial', 'Maior valor setorial']
            cores = ['#00008B', '#8eb0ae', '#53a7a9', '#007a7d']
            categorias = rotulos.split('|')
            dados = buscar_dados_grafico(cursor, select, user_id)
            if dados:
                df_plot = pd.DataFrame(dados, columns=series)
                df_plot.index = categorias
                
                # Encontra o valor máximo para criar ticks brasileiros
                max_value = df_plot.values.max() if len(dados) > 0 else 0
                tick_vals, tick_texts = create_br_ticks(max_value)
                
                fig = go.Figure()
                for i, serie in enumerate(series):
                    fig.add_trace(go.Bar(
                        name=serie,
                        x=categorias,
                        y=df_plot[serie],
                        marker_color=cores[i],
                        hoverinfo='skip',
                        hovertemplate=None
                    ))
                fig.update_layout(
                    title=None,
                    barmode='group',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.4,
                        xanchor="center",
                        x=0.5,
                        title=None,
                        font=dict(size=10)
                    ),
                    margin=dict(b=120, l=50, r=50, t=20),
                    height=graph_height,
                    width=graph_width,
                    xaxis=dict(
                        tickangle=0,
                        tickfont=dict(size=8),
                        tickmode='array',
                        ticktext=categorias,
                        tickvals=categorias
                    ),
                    yaxis=dict(
                        title=None,
                        tickfont=dict(size=8),  # Reduzido 20% (10 → 8)
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
                # Limpar tags HTML do título para compatibilidade com ReportLab
                import re
                if msg:
                    msg_clean = re.sub(r'<br\s*/?>', ' ', msg, flags=re.IGNORECASE)
                    msg_clean = re.sub(r'<[^>]+>', '', msg_clean)
                    msg_clean = re.sub(r'\s+', ' ', msg_clean)
                    msg_clean = msg_clean.strip()
                else:
                    msg_clean = ""
                elements.append(Paragraph(msg_clean, graphic_title_style))
                elements.append(Image(io.BytesIO(img_bytes), width=graph_width, height=graph_height))
                elements.append(Spacer(1, 20))

        doc.build(elements)
        return buffer
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None

if __name__ == "__main__":
    show_results()

